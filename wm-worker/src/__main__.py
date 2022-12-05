import logging.config

from types import SimpleNamespace

import json

from pathlib import Path

from dataclasses import dataclass

import argparse

import aiocron
import discord
from urllib.parse import urlparse, parse_qs

import asyncio
import os
import requests

from quart import Quart


class Config:
    __data__ = object()

    @staticmethod
    def get():
        return Config.__data__

    @staticmethod
    def load(path):
        with Path(path).open() as fp:
            Config.__data__ = json.load(fp, object_hook=lambda x: SimpleNamespace(**x))
        return Config.__data__


class Cache:

    _data = {}
    _path = None

    def __init__(self, file: Path):
        self._path = file
        if file.exists():
            with open(file) as fp:
                self._data = json.load(fp)

    def __setitem__(self, key, value):
        self._data[key] = value

        with self._path.open('w') as fp:
            json.dump(self._data, fp)

    def __getitem__(self, item):
        if item in self._data:
            return self._data[item]
        else:
            return None


class Kanka:
    user_cache = {}
    entities_cache = {}

    def __init__(self,
                 config,
                 discord: discord.Client,
                 queue: asyncio.Queue) -> None:
        super().__init__()

        self.config = config
        self.queue = queue
        self.discord = discord
        self.discord_notification_channel = None
        self.logger = logging.getLogger('kanka')

        self.init_cache()

    def fetch(self, page=1):
        data = []

        resp = requests.get(self.config.kanka.api_endpoint + '/entities',
                            params={"page": page, "lastSync": self.entities_cache["last_sync"]},
                            headers={
                                'Authorization': 'Bearer ' + self.config.kanka.token,
                                'User-Agent': 'kanka-sync/0.0.1'
                            })

        if resp.status_code == 200:
            self.logger.debug(f'GET {resp.url} - {resp.status_code}')
            resp_json = resp.json()
            data += resp_json['data']
            if resp_json['links']['next']:
                query = urlparse(resp_json['links']['next']).query
                if query:
                    data += self.fetch(parse_qs(query)['page'])
            self.entities_cache["last_sync"] = resp_json['sync']
        else:
            self.logger.warning(f'GET {resp.url} - {resp.status_code} - {resp.text}')
            raise Exception('Unable to fetch entities')

        return data

    async def get_user(self, user_id):
        users = await self.get_users()
        return users[user_id] if user_id in users else None

    async def get_notification_channel(self):
        if not self.discord_notification_channel:
            self.discord_notification_channel = await self.discord.fetch_channel(self.config.discord.kanka_notify_channel)
        return self.discord_notification_channel

    async def get_users(self):
        if not self.user_cache:
            cache = {}

            for user in await self.fetch_users():
                cache[user['id']] = user['name']

            self.user_cache = cache
        return self.user_cache

    async def fetch_users(self):
        resp = requests.get(self.config.kanka.api_endpoint + '/users',
                            headers={
                                'Authorization': 'Bearer ' + self.config.kanka.token,
                                'User-Agent': 'kanka-sync/0.0.1'
                            })

        if resp.status_code == 200:
            self.logger.debug(f'GET {resp.url} - {resp.status_code}')
            return resp.json()['data']

        self.logger.warning(f'GET {resp.url} - {resp.status_code} - {resp.text}')
        raise Exception('Unable to fetch users')

    async def cron(self):
        print('[Kanka] syncing')
        entities = self.fetch()
        print(f'[Kanka] sync ok, entities={len(entities)}, lastSync={self.entities_cache["last_sync"]}')

        await self.notify(entities)

    def get_entity_url(self, entity):
        entity_map = {
            'family': 'families',
            'ability': 'abilities',
        }
        return f'{self.config.kanka.endpoint}' \
               f'/{entity_map[entity["type"]] if entity["type"] in entity_map else entity["type"] + "s"}' \
               f'/{entity["child_id"]}'

    async def notify(self, entities):
        channel = await self.get_notification_channel()
        count = len(entities)
        if count > 100:
            self.logger.warning(f'{count} entities modified, no notifications')
        else:
            for entity in entities:
                author = await self.get_user(entity["updated_by"])
                await channel.send(f'{author or "Inconnu"} a modifié "{entity["name"]}"\n'
                                   f'{self.get_entity_url(entity)}')

    def init_cache(self):
        users_cache_file = Path(self.config.cache.base_path) / 'users.cache.json'
        if users_cache_file.exists():
            with open(users_cache_file) as fp:
                self.user_cache = json.load(fp)

        self.entities_cache = Cache(Path(self.config.cache.base_path) / 'entities.cache.json')


async def main():
    config = Config.load(os.environ.get('CONFIG_PATH', '/etc/wm-worker/config.json'))
    config.kanka.token = os.environ.get('KANKA_TOKEN', config.kanka.token)
    config.discord.token = os.environ.get('DISCORD_BOT_SECRET', config.discord.token)

    # Ugly SN to dict converted
    logging.config.dictConfig(json.loads(json.dumps(config.log, default=lambda x: vars(x))))

    app = Quart(__name__)
    queue = asyncio.Queue()
    client = discord.Client(intents=discord.Intents.none())

    kanka = Kanka(config, client, queue)

    @aiocron.crontab('* * * * *', loop=asyncio.get_event_loop())
    async def kanka_live():
        logger = logging.getLogger('cron.kanka.live')
        logger.debug('Adding task to the queue')
        await queue.put(kanka.cron)

    async def worker():
        logger = logging.getLogger('worker')

        while True:
            logger.debug('Waiting item')
            routine = await queue.get()
            logger.debug('Processing item')
            await routine()

    @app.route('/health')
    async def health():
        return 'hello'

    await asyncio.gather(
        client.start(config.discord.token),
        app.run_task(),
        worker())


if __name__ == "__main__":
    asyncio.run(main())
