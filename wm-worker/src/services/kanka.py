import json
import logging
import random
import re
from enum import Enum
from io import StringIO
from pathlib import Path
from typing import Optional

import discord
from meilisearch import Client
from meilisearch.errors import MeilisearchError
from westmarches_utils.api.exception import ClientException

from services.foundry import Foundry
from westmarches_utils.api import WestMarchesApi
from westmarches_utils.cache import Cache
from westmarches_utils.queue import Queue, JobDefinition


class Permission(Enum):
    READ = 1
    EDIT = 2
    ADD = 3
    DELETE = 4
    POSTS = 5
    PERMISSIONS = 6


def task_wrapper(args):
    pass


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
                 ms: Client,
                 foundry: Foundry,
                 api: WestMarchesApi) -> None:
        super().__init__()

        self.config = config
        self.queue = queue
        self.discord = discord
        self.ms = ms
        self.api = api
        self.foundry = foundry
        self.discord_notification_channel = None
        self.discord_calendar_notification_channels = None
        self.logger = logging.getLogger('[KANKA]')

        self.init_cache()

    async def initialize(self):
        await self.refresh_users()
        self._doc_types = {item['id']: item['code'] for item in await self.api.kanka.entity_types.list()}

        for type_id in self._doc_types:
            self.ms.index('kanka_' + self._doc_types[type_id]).update_filterable_attributes(
                self.config.meilisearch.indexes.kanka.filterable_attributes)

    async def get_user(self, user_id):
        users = await self.get_users()
        return users[user_id] if user_id in users else None

    async def get_notification_channel(self):
        if not self.discord_notification_channel:
            self.discord_notification_channel = await self.discord.fetch_channel(
                self.config.discord.kanka_notify_channel)
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

    async def refresh_users(self):
        self.logger.info('Refreshing users & groups')

        for user in await self.api.kanka.users.list():
            self._users[user['id']] = user['name']

            if roles := user.get('role'):
                self._roles.update({role['id']: role['name'] for role in roles})

    async def search_indexed_character_from_name(self, name) -> Optional[dict]:
        resp = self.ms.index('kanka_character').search('', { 'filter': f'name = "{name}"' })
        hits = len(resp['hits'])

        if hits > 1:
            self.logger.warning(f'[Kanka] Multiple hits for Character named {name}')

        if hits >= 1:
            self.logger.debug(f'[Kanka] Found {hits} Characters named {name}')
            return resp['hits'][0]
        else:
            self.logger.warning(f'[Kanka] No hits for Character named {name}')
            return None

    async def sync(self):
        self.logger.info('Syncing')
        last_sync = self.entities_cache["last_sync"]
        entities, new_sync = await self.api.kanka.entities.list_since(last_sync=last_sync)

        calendars, _ = await self.api.kanka.calendars.list_since(last_sync=last_sync)
        entities.extend([await self.api.kanka.entity(entity['entity_id']).get() for entity in calendars])

        try:
            await self.notify(entities=entities)
        except Exception as e:
            self.logger.exception(f'[Kanka] failed to notify: {e.__class__.__name__} {e}', exc_info=False)

        try:
            await self.index(entities=entities)
        except Exception as e:
            self.logger.exception(f'[Kanka] failed to index: {e.__class__.__name__} {e}', exc_info=False)

        try:
            await self.foundry_sync(last_sync)
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
            author = await self.api.kanka.user(entity["updated_by"]).get()

            if api_user := (await self.api.users.find_one({'kanka.id': entity["updated_by"]}, {'value': None}))['value']:
                if discord_username := api_user.get("discord", {}).get("username"):
                    author = f'{discord_username} (kanka : {author["name"]})'

            await channel.send(f'{author or "Inconnu"} a modifié "{entity["name"]}"\n'
                               f'{self.get_entity_url(entity)}')

            if entity['id'] == calendar_id:
                try:
                    entity = await self.api.kanka.entity(entity['id']).get()
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

        kanka_indices = [result.uid for result in self.ms.get_indexes()['results'] if result.uid.startswith('kanka_')]
        resp = self.ms.multi_search([{
            "indexUid": idx,
            "filter": f'(id IN [{", ".join([str(ent_id) for ent_type, ent_id in entity_ids])}]) OR '
                      f'(child_id IN [{", ".join([str(ent_id) for ent_type, ent_id in misc_ids])}])'
        } for idx in kanka_indices])

        for index in resp['results']:
            for hit in index['hits']:
                type_ = self._doc_types[hit['type_id']]

                if (type_, hit['id']) in entity_ids or (type_, hit['child']['id']) in misc_ids:
                    mentions.append({
                        'id': hit['id'],
                        'type': self._doc_types[hit['type_id']],
                        'type_id': hit['type_id'],
                        'name': hit['name']
                    })

                for field in fields:
                    if type_ == field.split('_')[0] and hit['child']['id'] == entity[field]:
                        entity[field.split('_')[0]] = {
                            'id': hit['id'],
                            'type': self._doc_types[hit['type_id']],
                            'type_id': hit['type_id'],
                            'name': hit['name']
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
                    entity = await self.api.kanka.entity(entity_id).get()

                self.logger.debug(f'Flattening {entity_type}/{entity_name}')
                await self.flatten(entity)

                if acls := await self.api.kanka.entity(entity_id).permissions.list():
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
                self.ms.index('kanka_' + entity_type).add_documents([entity])

                return entity_id
            except Exception as e:
                self.logger.error(f'Failed to index {entity_type}/{entity_name}', exc_info=e)

    async def foundry_sync(self, last_sync):
        self.logger.info(f'Checking for modified characters since {last_sync}')
        modified_ids = await self.foundry.list_modified_characters(last_sync)
        foundry_attribute = '_foundry.id'
        ignore_sync_attribute = '_kanka_sync.ignore'
        actors = []

        if modified_ids:
            self.logger.debug(f'Fetching foundry actors {modified_ids}')
            actors = await self.foundry.fetch_pcs(modified_ids)

        for foundry_actor in actors:
            self.logger.debug(f'Searching for kanka character named {foundry_actor["name"]}')
            kanka_character = await self.search_indexed_character_from_name(foundry_actor["name"])

            if not kanka_character:
                try:
                    self.logger.info(f'Creating kanka character named {foundry_actor["name"]}')
                    resp = await self.api.kanka.characters.post(json={
                        'name': foundry_actor["name"]
                    })

                    child = resp.json['data']
                    kanka_character = {
                        'attributes': [],
                        'child': child,
                        'id': child['entity_id'],
                        'name': foundry_actor["name"],
                    }
                except ClientException:
                    self.logger.warning(f'Failed to create kanka character name {foundry_actor["name"]}')
                    continue

            attributes_map = {a['name']: a for a in kanka_character.get('attributes', [])}

            if attributes_map.get(ignore_sync_attribute, False):
                self.logger.debug(f'Kanka sync ignore flag is set, ignoring actor')
                continue

            if not foundry_attribute in attributes_map:
                try:
                    self.logger.info(f'Linking kanka character {kanka_character["child"]["id"]} and foundry actor {foundry_actor["_id"]}/')
                    await self.api.kanka.entity(kanka_character['id']).attributes.post(json={
                        'name': foundry_attribute,
                        'value': foundry_actor["_id"],
                        'entity_id': kanka_character['id']
                    })
                except ClientException:
                    self.logger.warning(f'Failed to create link between kanka character and foundry actor')

            kanka_acls = kanka_character.get('acls', {})

            foundry_owners = [u for u in foundry_actor['permission'] if u != 'default' and foundry_actor['permission'][u] == 3]
            kanka_owners_ids = kanka_acls.get('users', [])
            self.logger.debug(f'Searching for kanka users {kanka_owners_ids}')
            users_from_kanka_owners = await self.api.users.find({"kanka.id": { "$in": kanka_owners_ids }})

            for owner in foundry_owners:
                found = False

                for user in users_from_kanka_owners:
                    if user['foundry']['_id'] == owner:
                        found = True
                        break

                if not found:
                    self.logger.debug(f'Searching for user with foundry._id={owner}')
                    if api_user := (await self.api.users.find_one({"foundry._id": owner}, {})).get('value'):
                        if "kanka" in api_user:
                            self.logger.debug(f'Found user "{api_user["foundry"]["name"]}" with kanka name "{api_user["kanka"]["name"]}"')
                            for action in [Permission.READ, Permission.EDIT, Permission.DELETE, Permission.PERMISSIONS]:
                                self.logger.info(f'Granting {action} for {kanka_character["name"]}[{kanka_character["id"]}] to {api_user["kanka"]["name"]}[{api_user["kanka"]["id"]}]')
                                await self.api.kanka.entity(kanka_character['id']).permissions.post(json=[{
                                    'user_id': api_user['kanka']['id'],
                                    'action': action.value,
                                    'access': True
                                }])

    async def sync_tag_characters(self):
        self.logger.debug('Fetching characters from foundry')

        if actors := await self.foundry.fetch_pcs():
            missing_pcs = []
            malformed_journals = []
            warns = []

            for foundry_pc in actors:
                pc_name = foundry_pc.get('name')
                tags = []
                characters = []

                self.logger.debug(f'Searching for a tag named "{pc_name}" in ES')
                try:
                    quoted_name = pc_name.replace('"','\\"')
                    resp = self.ms.multi_search([{
                        "indexUid": uid,
                        "filter": f'name = "{quoted_name}"',
                    } for uid in ['kanka_tag', 'kanka_character']])

                    for result in resp['results']:
                        for hit in result['hits']:
                            if result['indexUid'] == 'kanka_tag':
                                tags.append(hit)
                            else:
                                characters.append(hit)

                    if (pc_hits := len(characters)) == 0:
                        self.logger.info(f'No Character matching Actor named "{pc_name}"')
                        missing_pcs.append(foundry_pc)
                    elif pc_hits > 1:
                        self.logger.warning(warn := f'{pc_hits} Characters matching Actor named "{pc_name}"')
                        warns.append(warn)
                    elif pc_hits == 1:
                        self.logger.debug(f'Found Character matching Actor named "{pc_name}", skipping')
                        if (tag_hits := len(tags)) == 0:
                            self.logger.info(f'No Tag matching Actor named "{pc_name}"')
                        elif tag_hits > 1:
                            self.logger.warning(warn := f'{tag_hits} Tags matching Actor named "{pc_name}"')
                            warns.append(warn)
                        elif tag_hits == 1:
                            journals_idx = self.ms.index('kanka_journal')
                            journals_tag = journals_idx.search('', {
                                'filter': f'child.tags IN [{tags[0].get("child_id")}]'
                            }).get('hits', {})

                            journals_ids_character = [journal.get('id') for journal in
                                                      journals_idx.search('', {
                                                          'filter': f'child.mentions.id IN [{characters[0].get("child_id")}]'
                                                      }).get('hits', {})]

                            for journal in journals_tag:
                                if journal.get('id') not in journals_ids_character:
                                    malformed_journals.append(journal)

                except MeilisearchError as e:
                    self.logger.error(f'Failed to search in ES: {e.message}')

            msg = StringIO(
                'Rapport de migration Tag => Character \n'
                '======== \n'
                'PJ n\'ayant pas de fiche Kanka du type Character : \n'
                + ('\n'.join(['- ' + pc.get('name') for pc in missing_pcs])) +
                '\n ======== \n'
                'Journals utilisant un Tag alors que le personnage existe comme Character :\n'
                + ('\n'.join(['- ' + journal_.get('name') for journal_ in malformed_journals])) +
                '\n ======== \n'
                'Warnings :\n'
                + ('\n'.join(warns))
            )

            # channel = await self.discord.fetch_channel(859352329294577684)  # PM
            channel = await self.discord.fetch_channel(859433172704690186)  # dvp-bot-test
            await channel.send(file=discord.File(msg, filename='report.txt'))
        else:
            self.logger.error('Failed to fetch Player Characters from Foundry')

    def init_cache(self):
        users_cache_file = Path(self.config.cache.base_path) / 'users.cache.json'
        if users_cache_file.exists():
            with open(users_cache_file) as fp:
                self._users = json.load(fp)

        self.entities_cache = Cache(Path(self.config.cache.base_path) / 'entities.cache.json')
