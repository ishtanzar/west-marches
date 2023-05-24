import asyncio
import json
import logging
import random
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import discord
import elasticsearch.helpers
import requests
from elasticsearch import AsyncElasticsearch as Elasticsearch

from services.utils import Cache


class Kanka:
    _doc_types = {}
    _users = {}
    _roles = {
        195421: 'Public'  # todo: find API endpoint for campaign roles
    }

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

    async def initialize(self):
        await self.refresh_users()
        self._doc_types = await self.fetch_entity_types()

    async def fetch(self, endpoint, last_sync=None, page=1, related=False):
        data = []
        params = {"page": page}

        if related:
            params["related"] = 1

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
                    next_data, _ = await self.fetch(endpoint, last_sync, parse_qs(query)['page'])
                    data += next_data
            last_sync = resp_json['sync'] if 'sync' in resp_json else None
        elif resp.status_code == 429:
            self.logger.info(f'GET {resp.url} - {resp.status_code} - {resp.text}')
            await asyncio.sleep(61)

            return await self.fetch(endpoint, last_sync, page)
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
        if not self._users:
            await self.refresh_users()

        return self._users

    def get_date_announce(self, day, month, year):
        return random.choice(self.config.discord.random.date_announce) % {'day': day, 'month': month, 'year': year}

    async def fetch_entity(self, _id: int):
        [entity], __ = await self.fetch(self.config.kanka.api_endpoint + f'/entities/{_id}', related=True)
        return entity

    async def fetch_permissions(self, _id: int):
        permissions, __ = await self.fetch(self.config.kanka.api_endpoint + f'/entities/{_id}/entity_permissions')
        return permissions

    async def fetch_entities(self):
        return await self.fetch(self.config.kanka.api_endpoint + '/entities', self.entities_cache["last_sync"])

    async def fetch_users(self):
        users, __ = await self.fetch(self.config.kanka.api_endpoint + '/users')
        return users

    async def fetch_entity_types(self):
        resp, __ = await self.fetch('https://kanka.io/api/1.0' + '/entity-types')
        return {item['id']: item['code'] for item in resp}

    async def refresh_users(self):
        self.logger.info('[Kanka] refreshing users & groups')

        for user in await self.fetch_users():
            self._users[user['id']] = user['name']

            if roles := user.get('role'):
                self._roles.update({role['id']: role['name'] for role in roles})

    async def cron(self):
        self.logger.info('[Kanka] syncing')
        entities, last_sync = await self.fetch_entities()

        # await self.notify(entities=entities)
        await self.index(entities=entities)

        self.entities_cache["last_sync"] = last_sync
        self.logger.info(f'[Kanka] sync ok, entities={len(entities)}, lastSync={self.entities_cache["last_sync"]}')

    def get_entity_url(self, entity):
        entity_map = {
            'family': 'families',
            'ability': 'abilities',
        }
        return f'{self.config.kanka.endpoint}' \
               f'/{entity_map[entity["type"]] if entity["type"] in entity_map else entity["type"] + "s"}' \
               f'/{entity["child_id"]}'

    async def notify(self, entities: list = None, entity: dict = None):
        channel = await self.get_notification_channel()
        calendar_id, calendar_channels = await self.get_calendar_notification_config()

        if entities:
            count = len(entities)
            if count > 50:
                self.logger.warning(f'{count} entities modified, no notifications')
            else:
                for entity in entities:
                    await self.queue.put((self.notify, [], {entity: entity}))
        elif entity:
            author = await self.get_user(entity["updated_by"])
            await channel.send(f'{author or "Inconnu"} a modifié "{entity["name"]}"\n'
                               f'{self.get_entity_url(entity)}')

            if entity['id'] == calendar_id:
                try:
                    entity = await self.fetch_entity(entity['id'])
                    months = entity['child']['months']
                    [cal_year, cal_month, cal_day] = entity['child']['date'].split('-')

                    for calendar_chanel in calendar_channels:
                        await calendar_chanel.send(
                            self.get_date_announce(cal_day, months[int(cal_month) - 1]["name"], cal_year)
                        )
                except Exception as e:
                    self.logger.exception(f'[Kanka] failed to send date notification: {e.__class__.__name__} {e}',
                                          exc_info=False)

    async def flatten(self, entity):
        entity_ids = []
        misc_ids = []
        fields = ['location_id', 'race_id']
        mentions = []

        if child := entity.get('child'):
            await self.flatten(child)

        if entry := entity.get('entry'):
            entity_ids = re.findall(r'\[(\w+):(\d+)]', entry)

        if tags := entity.get('tags'):
            for tag in tags:
                misc_ids.append(('tag', tag))

        if (created_by := entity.get('created_by')) and (create_user := self._users.get(created_by)):
            entity['created_by_name'] = create_user

        if (updated_by := entity.get('updated_by')) and (update_user := self._users.get(updated_by)):
            entity['updated_by_name'] = update_user

        for field in fields:
            if value := entity.get(field):
                misc_ids.append((field.split('_')[0], value))

        resp = await self.es.search(index='kanka_*', query={
            'bool': {
                'should': [
                    {'terms': {'child_id': [ent_id for ent_type, ent_id in misc_ids]}},
                    {'ids': {'values': [ent_id for ent_type, ent_id in entity_ids]}}
                ]
            }
        })

        for hit in resp['hits']['hits']:
            type_ = self._doc_types[hit['_source']['type_id']]

            if (type_, hit['_id']) in entity_ids or (type_, hit['_source']['child']['id']) in misc_ids:
                mentions.append({
                    'id': hit['_id'],
                    'type': self._doc_types[hit['_source']['type_id']],
                    'type_id': hit['_source']['type_id'],
                    'name': hit['_source']['name']
                })

            for field in fields:
                if type_ == field.split('_')[0] and hit['_source']['child']['id'] == entity[field]:
                    entity[field.split('_')[0]] = {
                        'id': hit['_id'],
                        'type': self._doc_types[hit['_source']['type_id']],
                        'type_id': hit['_source']['type_id'],
                        'name': hit['_source']['name']
                    }

        if mentions:
            entity['mentions'] = mentions

        return entity

    async def index(self, entity=None, entities=None):
        if entities:
            return [await self.index(entity=entity) for entity in entities]

        if entity:
            entity_id = entity['id']
            entity_type = entity['type']
            entity_name = entity['name']
            entity_acls = {}

            try:

                if 'child' not in entity or 'id' not in entity['child']:
                    entity = await self.fetch_entity(entity_id)

                self.logger.debug(f'Flattening {entity_type}/{entity_name}')
                await self.flatten(entity)

                if acls := await self.fetch_permissions(entity_id):
                    acl_users = []
                    acl_roles = []

                    for acl in acls:
                        if (role_id := acl['campaign_role_id']) and role_id not in acl_roles and acl['action'] >= 1:
                            acl_roles.append(role_id)
                        if (user_id := acl['user_id']) and user_id not in acl_users and acl['action'] >= 1:
                            acl_users.append(user_id)

                    if acl_users:
                        entity_acls['users'] = acl_users
                    if acl_roles:
                        entity_acls['roles'] = acl_roles
                else:
                    entity_acls['roles'] = [self.config.kanka.gm_role_id]

                entity['acls'] = entity_acls

                self.logger.debug(f'Indexing {entity_type}/{entity_name}')
                await self.es.index(index='kanka_' + entity_type, id=entity_id, document=entity)

                return entity_id
            except Exception as e:
                self.logger.error(f'Failed to index {entity_type}/{entity_name}: {e}')

    async def recompute(self):
        docs = elasticsearch.helpers.async_scan(client=self.es, index='kanka_*', query={
            'query': {
                'query_string': {
                    'query': "_id:2259866"
                }
            }
        })

        async for doc in docs:
            await self.index(doc['_source'])

    def init_cache(self):
        users_cache_file = Path(self.config.cache.base_path) / 'users.cache.json'
        if users_cache_file.exists():
            with open(users_cache_file) as fp:
                self._users = json.load(fp)

        self.entities_cache = Cache(Path(self.config.cache.base_path) / 'entities.cache.json')

