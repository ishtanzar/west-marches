import asyncio
import json
import logging
import random
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import discord
import requests
from elasticsearch import AsyncElasticsearch as Elasticsearch

from services.utils import Cache


class Kanka:
    user_cache = {}
    entities_cache = {}

    def __init__(self,
                 config,
                 discord: discord.Client,
                 queue: asyncio.Queue,
                 es: Elasticsearch) -> None:
        super().__init__()

        self.config = config
        self.queue = queue
        self.discord = discord
        self.es = es
        self.discord_notification_channel = None
        self.discord_calendar_notification_channels = None
        self.logger = logging.getLogger('kanka')

        self.init_cache()

    def fetch(self, endpoint, last_sync=None, page=1):
        data = []
        params = {"page": page, "related": 1}

        if last_sync:
            params["lastSync"] = last_sync

        resp = requests.get(endpoint,
                            params=params,
                            headers={
                                'Authorization': 'Bearer ' + self.config.kanka.token,
                                'User-Agent': 'kanka-sync/0.0.1'
                            })

        if resp.status_code == 200:
            self.logger.debug(f'GET {resp.url} - {resp.status_code}')
            resp_json = resp.json()
            data += resp_json['data'] if isinstance(resp_json['data'], list) else [resp_json['data']]
            if 'links' in resp_json and 'next' in resp_json['links']:
                query = urlparse(resp_json['links']['next']).query
                if query:
                    next_data, _ = self.fetch(endpoint, last_sync, parse_qs(query)['page'])
                    data += next_data
            last_sync = resp_json['sync'] if 'sync' in resp_json else None
        else:
            self.logger.warning(f'GET {resp.url} - {resp.status_code} - {resp.text}')
            raise Exception('Unable to fetch from API')

        return data, last_sync

    async def get_user(self, user_id):
        users = await self.get_users()
        return users[user_id] if user_id in users else None

    async def get_notification_channel(self):
        if not self.discord_notification_channel:
            self.discord_notification_channel = await self.discord.fetch_channel(self.config.discord.kanka_notify_channel)
        return self.discord_notification_channel

    async def get_calendar_notification_config(self):
        channels = []

        if not self.discord_calendar_notification_channels:
            for _id in self.config.discord.kanka_calendar_notification_channels:
                channels.append(await self.discord.fetch_channel(_id))
            self.discord_calendar_notification_channels = channels

        return self.config.kanka.calendar_entity_id, self.discord_calendar_notification_channels

    async def get_users(self):
        if not self.user_cache:
            cache = {}

            users, _ = self.fetch_users()
            for user in users:
                cache[user['id']] = user['name']

            self.user_cache = cache
        return self.user_cache

    def get_date_announce(self, day, month, year):
        return random.choice(self.config.discord.random.date_announce) % {'day': day, 'month': month, 'year': year}

    def fetch_entity(self, id:int):
        [entity], __ = self.fetch(self.config.kanka.api_endpoint + f'/entities/{id}')
        return entity

    def fetch_entities(self):
        return self.fetch(self.config.kanka.api_endpoint + '/entities', self.entities_cache["last_sync"])

    def fetch_users(self):
        return self.fetch(self.config.kanka.api_endpoint + '/users')

    async def cron(self):
        print('[Kanka] syncing')
        entities, last_sync = self.fetch_entities()
        self.entities_cache["last_sync"] = last_sync
        self.logger.info(f'[Kanka] sync ok, entities={len(entities)}, lastSync={self.entities_cache["last_sync"]}')

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
        calendar_id, calendar_channels = await self.get_calendar_notification_config()

        count = len(entities)
        if count > 50:
            self.logger.warning(f'{count} entities modified, no notifications')
        else:
            for entity in entities:
                author = await self.get_user(entity["updated_by"])
                await channel.send(f'{author or "Inconnu"} a modifié "{entity["name"]}"\n'
                                   f'{self.get_entity_url(entity)}')

                if entity['id'] == calendar_id:
                    try:
                        entity = self.fetch_entity(entity['id'])
                        months = entity['child']['months']
                        [cal_year, cal_month, cal_day] = entity['child']['date'].split('-')

                        for calendar_chanel in calendar_channels:
                            await calendar_chanel.send(
                                self.get_date_announce(cal_day, months[int(cal_month) - 1]["name"], cal_year)
                            )
                    except Exception as e:
                        self.logger.exception(f'[Kanka] failed to send date notification: {e.__class__.__name__} {e}',
                                              exc_info=False)
                break

    def init_cache(self):
        users_cache_file = Path(self.config.cache.base_path) / 'users.cache.json'
        if users_cache_file.exists():
            with open(users_cache_file) as fp:
                self.user_cache = json.load(fp)

        self.entities_cache = Cache(Path(self.config.cache.base_path) / 'entities.cache.json')

