import argparse
import asyncio
import json
import logging.config
import os

import aiocron
import discord
from elasticsearch import AsyncElasticsearch as Elasticsearch
from quart import Quart

from services.donations import Donations
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
    questions = Questions(config, client)
    donations = Donations(config)

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
            routine = await queue.get()
            logger.debug('Processing item')
            try:
                await routine()
            except Exception as e:
                logger.warning(str(e), exc_info=True)

    @app.route('/health')
    async def health():
        return 'hello'

    subparsers.add_parser('kanka.live').set_defaults(func=kanka.cron)
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
