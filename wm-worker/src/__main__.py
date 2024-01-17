import argparse
import asyncio
import json
import logging.config
import os

import aiocron
import discord as dpy
from meilisearch import Client
from quart import Quart

from services.donations import Donations
from services.foundry import Foundry
from services.kanka import Kanka
from services.questions import Questions
from westmarches_utils.api import WestMarchesApiConfig, WestMarchesApi
from westmarches_utils.api.auth import APIKey, Basic, Bearer
from westmarches_utils.api.kanka import KankaApiConfig
from westmarches_utils.config import Config
from westmarches_utils.queue import Queue, JobDefinition


async def main():
    config = Config.load(os.environ.get('CONFIG_PATH', '/etc/wm-worker/config.json'))
    config.set('meilisearch.endpoint', os.environ.get('MEILI_ENDPOINT', config.get('meilisearch.endpoint', 'http://meilisearch:7700')))
    config.set('api.endpoint', os.environ.get('API_ENDPOINT', config.get('api.endpoint', 'http://api:3000')))
    config.set('kanka.api_root', os.environ.get('KANKA_API_ROOT', config.get('kanka.api_root', 'https://api.kanka.io/1.0')))
    config.set('redis.endpoint', os.environ.get('REDIS_ENDPOINT', config.get('redis.endpoint', 'redis://redis')))
    config.meilisearch.key = os.environ.get('MEILI_KEY', config.get('meilisearch.key'))
    config.kanka.token = os.environ.get('KANKA_TOKEN', config.get('kanka.token'))
    config.api.token = os.environ.get('API_TOKEN', config.get('api.token'))
    config.discord.token = os.environ.get('DISCORD_BOT_SECRET', config.get('discord.token'))

    # Ugly SN to dict converted
    logging.config.dictConfig(json.loads(json.dumps(config.log, default=lambda x: vars(x))))

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    app = Quart(__name__)
    queue = Queue(config)

    intents = dpy.Intents.none()
    intents.guilds = True

    api_config = WestMarchesApiConfig(
        api_auth=APIKey(config.api.token),
        management_api_auth=Basic('foundry_manager', os.environ['MGMNT_API_SECRET']),
        kanka=KankaApiConfig(config.kanka.campaign, Bearer(config.kanka.token))
    )

    api = WestMarchesApi(api_config)

    discord = dpy.Client(intents=intents)
    ms = Client(config.meilisearch.endpoint, config.meilisearch.key)
    foundry = Foundry(ms, discord, api)
    kanka = Kanka(config, discord, queue, ms, foundry, api)
    questions = Questions(config, discord)
    donations = Donations(config)

    await foundry.initialize()
    await kanka.initialize()

    @aiocron.crontab(config.cron.foundry.update, loop=asyncio.get_event_loop())
    async def foundry_update():
        logging.getLogger('cron.foundry.update').debug('Queued')
        await queue.put(JobDefinition('foundry.cron'))

    @aiocron.crontab(config.cron.kanka.live, loop=asyncio.get_event_loop())
    async def kanka_live():
        logging.getLogger('cron.kanka.live').debug('Queued')
        await queue.put(JobDefinition('kanka.sync'))

    @aiocron.crontab(config.cron.questions.review, loop=asyncio.get_event_loop())
    async def questions_review():
        logging.getLogger('cron.questions.review').debug('Queued')
        await queue.put(JobDefinition('questions.cron'))

    @aiocron.crontab(config.cron.donations.reset, loop=asyncio.get_event_loop())
    async def donations_reset():
        logging.getLogger('cron.donations.reset').debug('Queued')
        await queue.put(JobDefinition('donations.reset'))

    async def worker():
        logger = logging.getLogger('worker')

        while True:
            logger.debug('Waiting item')
            job = await queue.get()
            logger.debug('Processing item')
            try:
                await job.run()
            except Exception as e:
                logger.warning(str(e), exc_info=True)

    @app.route('/health')
    async def health():
        return 'hello'

    queue.register('foundry.cron', foundry.cron)
    queue.register('foundry.backup', foundry.backup)
    queue.register('kanka.sync', kanka.sync)
    queue.register('kanka.notify', kanka.notify)
    queue.register('questions.cron', questions.cron)
    queue.register('donations.reset', donations.reset)

    subparsers.add_parser('kanka.live').set_defaults(func=kanka.sync)
    subparsers.add_parser('kanka.sync_tags').set_defaults(func=kanka.sync_tag_characters)
    subparsers.add_parser('foundry.update').set_defaults(func=foundry.cron)
    subparsers.add_parser('foundry.backup').set_defaults(func=foundry.backup)
    subparsers.add_parser('foundry.upgrade_audit').set_defaults(func=foundry.upgrade_audit)
    subparsers.add_parser('kanka.sync').set_defaults(func=kanka.sync)
    subparsers.add_parser('donations.reset').set_defaults(func=donations.reset)
    subparsers.add_parser('foundry.reindex_actors').set_defaults(func=foundry.reindex_actors)
    subparsers.add_parser('queue.process').set_defaults(func=worker)
    args = parser.parse_args()

    if "func" in args:
        await discord.login(config.discord.token)
        await args.func()
    else:
        await asyncio.gather(
            discord.start(config.discord.token),
            app.run_task('0.0.0.0'),
            worker())


if __name__ == "__main__":
    asyncio.run(main())
