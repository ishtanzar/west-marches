import argparse
import asyncio
import json
import logging.config
import os
import re
from types import SimpleNamespace

import aiocron
import discord as dpy
from meilisearch import Client
from meilisearch.models.document import Document
from quart import Quart
from westmarches_utils.api.exception import ClientException

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
    foundry = Foundry(config, ms, discord, api)
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

    async def maintenance():
        logger = logging.getLogger('maintenance')
        # resp = ms.index('kanka_journal').search('', {
        #     "filter": "child.type = 'Rapport-MJ'",
        #     "limit": 2000
        # })

        # Full reindex an entity type
        # for entity in await api.kanka.entities.list(params={"types": "journal"}):
        #     await kanka.index(entity=entity)

        # # Compare tags vs characters
        # resp = ms.index('kanka_journal').get_documents({"limit": 5000})
        # tags = {}
        # characters = {}
        # for journal in resp.results:
        #     if journal.child['type'] == 'Rapport-MJ':
        #         for tag_id in journal.tags:
        #             if tag_id in tags:
        #                 tag = tags[tag_id]
        #             elif tag := (ms.index('kanka_tag').search('', {"filter": f"child_id = {tag_id}"})['hits'][0:] + [None])[0]:
        #                 tags[tag_id] = tag
        #             else:
        #                 logger.warning(f'No such tag {tag_id}')
        #                 continue
        #
        #             tag_name = tag['name']
        #             ms_name = tag_name.replace("'", r"\'")
        #
        #             if tag_name in characters:
        #                 continue
        #             elif pc := (ms.index('kanka_character').search('', {"filter": f"name = '{ms_name}'"})['hits'][0:] + [None])[0]:
        #                 characters[tag_name] = pc
        #             else:
        #                 logger.info(f'No such character {tag_name} (id: {tag_id}), creating')
        #                 resp = await api.kanka.characters.post(json={"name": tag_name})
        #                 await kanka.index(entity=(pc:={
        #                     "child": (new_char := resp.json['data']),
        #                     "name": new_char["name"],
        #                     "id": new_char["entity_id"],
        #                     "child_id": new_char["id"],
        #                     "type": "character"
        #                 }))
        #                 characters[tag_name] = pc

        # Migrate tag => character
        resp = ms.index('kanka_journal').get_documents({"limit": 5000})

        # resp = SimpleNamespace()
        # resp.results = [
        #     ms.index('kanka_journal').get_document("5909972")
        # ]
        #
        logger.info('Hits: ' + str(len(resp.results)))

        journal: Document
        for journal in resp.results:
            if journal.child['type'] == 'Rapport-MJ':
                logger.info(f'{journal.name}: {journal.tags}')
                remaining_tags = []
                new_pcs = []
                for tag_id in journal.tags:
                    if tag := (ms.index('kanka_tag').search('', {"filter": f"child_id = {tag_id}"})['hits'][0:] + [None])[0]:
                        # tag_name = tag['name'].replace("'", r"\'")
                        # logger.debug(f'Tag {tag_id}: {tag_name}')
                        # if not (pc := (ms.index('kanka_character').search('', {"filter": f"name = '{tag_name}'"})['hits'][0:] + [None])[0]):
                        #     logger.info(f'No such character {tag_name}, creating')
                        #     resp = await api.kanka.characters.post(json={"name": tag_name, "is_dead": True})
                        #     await kanka.index(entity={
                        #         "child": (pc := resp.json['data']),
                        #         "name": pc["name"],
                        #         "id": pc["entity_id"],
                        #         "child_id": pc["id"],
                        #         "type": "character"
                        #     })

                        try:
                            if tag['type'] != 'PJ':
                                await api.kanka.tag(tag_id).put(json={
                                    'type': 'PJ'
                                })
                                tag['type'] = 'PJ'
                        except ClientException as e:
                            logger.warning(e.response.text)

                        new_pcs.append(f'<a href="#" class="mention" data-name="{tag["name"]}" data-mention="[tag:{tag["id"]}]">{tag["name"]}</a>')
                    else:
                        logger.warning('Tag not found')
                        remaining_tags.append(tag_id)

                if new_pcs:
                    entry, count = re.subn(
                        r'(<h4>.*?Personnages.*?</h4>.*?(?:<a[^>]*data-mention="\[tag:[0-9]*]"[^>]*>[^<]*</a>[, ]*)*)(.*?<hr>)',
                        rf'\1{", ".join(new_pcs)}\2',
                        journal.child['entry'] or ''
                    )
                    if not count:
                        entry = f'''<h4><font color="#424242">Personnages</font></h4>
                        <p>{", ".join(new_pcs)}</p>
                        <hr>''' + (journal.child['entry'] or '')

                    journal.child.update(updated_journal:={
                        "entry": entry,
                        "tags": remaining_tags
                    })
                    await api.kanka.journal(journal.child_id).put(json=updated_journal)
                    await kanka.index(entity=journal.__dict__)

        logger.info('Done')

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
    subparsers.add_parser('maintenance').set_defaults(func=maintenance)
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
