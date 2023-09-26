from enum import Enum

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
from westmarches_utils.api import WestMarchesApi
from westmarches_utils.cache import Cache
from westmarches_utils.queue import Queue, JobDefinition

from services.foundry import Foundry


class Permission(Enum):
    READ = 1
    EDIT = 2
    ADD = 3
    DELETE = 4
    POSTS = 5
    PERMISSIONS = 6


class Kanka:
    _doc_types = {}
    _users = {}
    _roles = {
        195421: 'Public'  # todo: https://trello.com/c/3zrtWskR/1007-api-roles
    }

    entities_cache = {}

    def __init__(self,
                 config,
                 discord: discord.Client,
                 queue: Queue,
                 es: Elasticsearch,
                 foundry: Foundry,
                 api: WestMarchesApi) -> None:
        super().__init__()

        self.config = config
        self.queue = queue
        self.discord = discord
        self.es = es
        self.api = api
        self.foundry = foundry
        self.discord_notification_channel = None
        self.discord_calendar_notification_channels = None
        self.logger = logging.getLogger('[KANKA]')

        self.init_cache()

    async def initialize(self):
        await self.refresh_users()
        self._doc_types = await self.fetch_entity_types()

        await self.es.indices.put_index_template(name='kanka_indices', template={
            'settings': {
                'analysis': {
                    'analyzer': {
                        'default': {
                            'type': 'french'
                        }
                    }
                },
                'index': {
                    'number_of_shards': 1,
                    'number_of_replicas': 0
                }
            }
        }, index_patterns=['kanka_*'])

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

    async def add_user_entity_permission(self, _id: int, user: int, action:int = 1):
        resp = requests.post(self.config.kanka.api_endpoint + f'/entities/{_id}/entity_permissions', json={
            'user_id': user,
            'action': action,
            'access': True
        })

        if resp.status_code == 200:
            self.logger.debug(f'GET {resp.url} - {resp.status_code}')
            return resp.json()['data']
        else:
            self.logger.warning(f'GET {resp.url} - {resp.status_code} - {resp.text}')
            raise Exception('Unable to create permission')

    async def fetch_entities(self, last_sync=None):
        return await self.fetch(self.config.kanka.api_endpoint + '/entities', last_sync)

    async def fetch_users(self):
        users, __ = await self.fetch(self.config.kanka.api_endpoint + '/users')
        return users

    async def fetch_entity_types(self):
        resp, __ = await self.fetch('https://kanka.io/api/1.0' + '/entity-types')
        return {item['id']: item['code'] for item in resp}

    async def refresh_users(self):
        self.logger.info('Refreshing users & groups')

        for user in await self.fetch_users():
            self._users[user['id']] = user['name']

            if roles := user.get('role'):
                self._roles.update({role['id']: role['name'] for role in roles})

    async def search_indexed_character_from_name(self, name):
        resp = await self.es.search(index='kanka_character', query={
            'query_string': {
                'query': f'name:"{name}"'
            }
        })

        if resp['hits']['total']['value'] == 1:
            return resp['hits']['hits'][0]['_source']
        else:
            # todo: WARN
            return None

    async def sync(self):
        self.logger.info('Syncing')
        last_sync = self.entities_cache["last_sync"]
        entities, new_sync = await self.fetch_entities(last_sync)

        try:
            await self.notify(entities=entities)
        except Exception as e:
            self.logger.exception(f'[Kanka] failed to notify: {e.__class__.__name__} {e}', exc_info=False)

        try:
            await self.index(entities=entities)
        except Exception as e:
            self.logger.exception(f'[Kanka] failed to index: {e.__class__.__name__} {e}', exc_info=False)

        try:
            await self.ownership(last_sync)
        except Exception as e:
            self.logger.exception(f'[Kanka] failed to modify permissions: {e.__class__.__name__} {e}', exc_info=False)

        self.entities_cache["last_sync"] = new_sync
        self.logger.info(f'Sync ok, entities={len(entities)}, lastSync={self.entities_cache["last_sync"]}')

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
                    logging.getLogger('kanka.notify').debug('Queued')
                    await self.queue.put(JobDefinition('kanka.notify', entity=entity))
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

    async def ownership(self, last_sync):
        actors = []

        self.logger.debug(f'Checking for modified characters since {last_sync}')
        modified_ids = await self.foundry.list_modified_characters(last_sync)

        if modified_ids:
            self.logger.debug(f'Fetching foundry actors {modified_ids}')
            actors = await self.foundry.fetch_pcs(ids=modified_ids)

        for foundry_actor in actors:
            self.logger.debug(f'Searching for kanka character named {foundry_actor["name"]}')
            kanka_character = await self.search_indexed_character_from_name(foundry_actor["name"])

            if kanka_character:
                kanka_acls = kanka_character['acls']

                foundry_owners = [u for u in foundry_actor['permission'] if u != 'default' and foundry_actor['permission'][u] == 3]
                kanka_owners_ids = kanka_acls['users'] if 'users' in kanka_acls else []
                self.logger.debug(f'Searching for kanka users {kanka_owners_ids}')
                users_from_kanka_owners = await self.api.users.search({"kanka.id": { "$in": kanka_owners_ids }})

                for owner in foundry_owners:
                    found = False

                    for user in users_from_kanka_owners:
                        if user['foundry']['_id'] == owner:
                            found = True
                            break

                    if not found:
                        self.logger.debug(f'Searching for kanka user {owner}')
                        [new_user] = await self.api.users.search({"foundry._id": owner})
                        for action in [Permission.READ, Permission.EDIT, Permission.DELETE, Permission.PERMISSIONS]:
                            self.logger.info(f'Granting {action} for {kanka_character["name"]}[{kanka_character["id"]}] to {new_user["kanka"]["name"]}[{new_user["kanka"]["id"]}]')
                            await self.add_user_entity_permission(kanka_character['id'], new_user['kanka']['id'], action.value)

    async def recompute(self):
        docs = elasticsearch.helpers.async_scan(client=self.es, index='kanka_*', query={
            'query': {
                'query_string': {
                    'query': "*"
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

