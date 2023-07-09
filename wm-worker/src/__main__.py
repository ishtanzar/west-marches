import argparse
import asyncio
import json
import logging.config
import os
import re
from zipfile import ZipFile, BadZipFile

import aiocron
import discord
import requests
from elasticsearch import AsyncElasticsearch as Elasticsearch
from quart import Quart

from services.donations import Donations
from services.foundry import Foundry
from services.kanka import Kanka
from services.questions import Questions
from services.utils import Config


async def main():
    config = Config.load(os.environ.get('CONFIG_PATH', '/etc/wm-worker/config.json'))
    config.kanka.token = os.environ.get('KANKA_TOKEN', config.kanka.token)
    config.discord.token = os.environ.get('DISCORD_BOT_SECRET', config.discord.token)
    es = Elasticsearch('http://elasticsearch:9200')

    # Ugly SN to dict converted
    logging.config.dictConfig(json.loads(json.dumps(config.log, default=lambda x: vars(x))))

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    app = Quart(__name__)
    queue = asyncio.Queue()

    intents = discord.Intents.none()
    intents.guilds = True

    client = discord.Client(intents=intents)

    kanka = Kanka(config, client, queue, es)
    foundry = Foundry(es)
    questions = Questions(config, client)
    donations = Donations(config)

    await foundry.initialize()
    await kanka.initialize()

    @aiocron.crontab(config.cron.foundry.update, loop=asyncio.get_event_loop())
    async def foundry_update():
        logging.getLogger('cron.foundry.update').debug('Queued')
        await queue.put(foundry.cron)

    @aiocron.crontab(config.cron.kanka.live, loop=asyncio.get_event_loop())
    async def kanka_live():
        logging.getLogger('cron.kanka.live').debug('Queued')
        await queue.put(kanka.cron)

    @aiocron.crontab(config.cron.questions.review, loop=asyncio.get_event_loop())
    async def questions_review():
        logging.getLogger('cron.questions.review').debug('Queued')
        await queue.put(questions.cron)

    @aiocron.crontab(config.cron.donations.reset, loop=asyncio.get_event_loop())
    async def donations_reset():
        logging.getLogger('cron.donations.reset').debug('Queued')
        await queue.put(donations.reset)

    async def worker():
        logger = logging.getLogger('worker')

        while True:
            logger.debug('Waiting item')
            job = await queue.get()
            logger.debug('Processing item')
            try:
                if isinstance(job, tuple):
                    routine, _args, _kwargs = job
                else:
                    routine = job
                    _args = []
                    _kwargs = {}

                await routine(*_args, **_kwargs)
            except Exception as e:
                logger.warning(str(e), exc_info=True)

    @app.route('/health')
    async def health():
        return 'hello'

    @app.route('/kanka/reindex')
    async def kanka_reindex():
        url = "https://kanka.io/api/1.0/campaigns/67312/entities?related=1"
        headers = {"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiNDcwMzQ3ZWFiNzdiMTZkOGMyNDE3MTczYTgyYTZhMGE2NGFmMDYyMDUwZTk1Y2YwNzFhOTVjOWFkNDJhMWQ5ZDEwMjM2YWJkZmZiYmNlYWIiLCJpYXQiOjE2NjcxNjA4OTguNDc5OTk3LCJuYmYiOjE2NjcxNjA4OTguNDgwMDAxLCJleHAiOjE2OTg2OTY4OTguNDcyNTIsInN1YiI6IjY5MTk2Iiwic2NvcGVzIjpbXX0.aXwbgS37aQIyvNkTOmd_CejE9peEsaxqolT1swqcoLsPJHmt2awnIa-5CdqefRzs0FqGHsklarQwiNypimhFDpFut0rKyx0EtjgZe69aq0ziBDyJYFQZv3haoWh6VJTHmrC186svnFIBVmJZIRFFfkkeEVOTK9J1VUwsg-Lrm9tcpgjvzhU_Oe5iIWM-tD3fjr7_LoRMht_oA2lVVf20k6Djr88l7V1ulvRhjon65vIyG3EyBZAl3-pa3UnRV8JfErSJVuv3_pWAZARCkGUpSlF_sMxzflSC54cPJd0B32edBmOEHoi9T9GQEOm9_y93vCVkD1r7CPspBER9Iap9ZCYS1DSM8mkBsKsO5SLO23JaOG24_Ra_bueKTS7MgzEGeAYw1T1JzEZx6u07MCPF7gDG2Rd82OZ2_o5u80ohfwNyNDNZOZBdjwxI1Bz2xYKlGTl6cf08x9M3dfXcctLkwbMxVXgTwHfgx2dtVG55RCzKJJoVPXDOrwmB3buAJFd7qflgZnpECgopuXWQ_vJ7GTTrtT5uMX8pmqRrTH3c5Y4xRZaFXJtLMSfXShZS8f_lwDHVICAfFSGy7orDOzZeVqTbMxRZ2bWyp4UEiSt-mWdJf0VWxNYUd40cCFB-8aD7Q_ZfdHeHWLmVvfBjUA2QCLIWKJfb5b4P64Zy3nF_98o"}

        response = requests.request("GET", url, data='', headers=headers)

        entity = response.json()['data']
        # es.index(index="kanka_entities", id=entity['entity_id'], document=entity)
        indexed_docs = 0

        # try:
        #     with ZipFile('/opt/project/campaign_67312_6445aeb3e8a74_20230423_221827.zip', mode='r') as archive:
        #         routines = []
        #         # for filename in archive.namelist():
        #         # for filename in ['journals/the-bad-batch-s01e04-ishtanzar.json']:
        #         for filename in ['characters/aldail.json']:
        #             match = re.search(r'(?P<type>\w+)s/(?P<name>.*).json', filename)
        #             if match:
        #                 doc = json.loads(archive.read(filename))
        #
        #                 # entity = doc.pop('entity')
        #                 # entity['child'] = doc
        #                 # entity['type'] = doc_types[entity['type_id']]
        #
        #                 routines.append(kanka.index(entity=entity))
        #         result = await asyncio.gather(*routines, return_exceptions=True)
        #         indexed_docs = len([r for r in result if r is not None and not isinstance(r, Exception)])
        # except BadZipFile:
        #     return 'KO'

        return f'Indexed {indexed_docs} documents'

    subparsers.add_parser('kanka.live').set_defaults(func=kanka.cron)
    subparsers.add_parser('foundry.update').set_defaults(func=foundry.cron)
    subparsers.add_parser('foundry.reindex').set_defaults(func=foundry.reindex)
    subparsers.add_parser('es.recompute').set_defaults(func=kanka.recompute)
    subparsers.add_parser('donations.reset').set_defaults(func=donations.reset)
    args = parser.parse_args()

    if "func" in args:
        await client.login(config.discord.token)
        await args.func()
    else:
        await asyncio.gather(
            client.start(config.discord.token),
            app.run_task('0.0.0.0'),
            worker())


if __name__ == "__main__":
    asyncio.run(main())
