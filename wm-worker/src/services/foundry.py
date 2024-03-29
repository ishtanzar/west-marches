import logging
from pathlib import Path

import arrow
import discord
from meilisearch import Client
from meilisearch.errors import MeilisearchApiError
from typing import Optional
from westmarches_utils.api.exception import HTTPException

from westmarches_utils.api import WestMarchesApi
from westmarches_utils.cache import Cache


class Foundry:

    def __init__(
            self,
            config,
            ms: Client,
            dpy: discord.Client,
            api: WestMarchesApi) -> None:

        self._config = config
        self._ms = ms
        self._discord = dpy
        self._api = api
        self.audit_indexes = []
        self._logger = logging.getLogger('foundry')
        self._cache = Cache(Path(config.cache.base_path) / 'foundry.cache.json')

    async def initialize(self):
        self.audit_indexes = [idx for idx in self._ms.get_indexes()['results'] if idx.uid.startswith('foundry_audit-')]
        for index in self.audit_indexes:
            index.update_filterable_attributes(['@timestamp','timestamp','message', 'fields.user.name', 'fields.actor'])

    async def fetch_pcs(self, ids: list = None) -> list:
        if ids is None:
            ids = []

        query = {
            'type': 'character'
        }

        if len(ids) > 0:
            query['_id'] = {'$in': ids}

        try:
            return await self._api.foundry.actors.search(query)
        except HTTPException:
            return []

    async def list_modified_characters(self, last_sync: str | int = None) -> list:
        modified = set()
        query_from = 0
        query_size = 1000
        last_sync_obj = arrow.get(last_sync) if last_sync else arrow.utcnow().shift(hours=-1)
        index = self._ms.index('foundry_audit-' + last_sync_obj.strftime("%Y_%m"))

        while True:
            try:
                hits_count = 0
                ts = str(int(last_sync_obj.float_timestamp * 1000))

                self._logger.debug(f'ms.search {index.uid} - offset={query_from} limit={query_size} ts>{ts}')

                resp = index.search('', {
                    'offset': query_from,
                    'limit': query_size,
                    'filter': "message = 'Actor modified' AND timestamp > " + ts
                })

                for h in resp['hits']:
                    hits_count += 1
                    modified.add(h['fields']['actor'])

                if hits_count < query_size:
                    break

                query_from = query_from + query_size
            except MeilisearchApiError as e:
                self._logger.exception(f'Failed to query index: ' + e.message)
                return []

        self._logger.debug(f'Found {len(modified)} characters modified')
        return list(modified)

    async def cron(self):
        self._logger.debug('Cron')
        last_sync = self._cache["last_modified_characters_sync"]
        new_sync = arrow.utcnow()

        char_ids = await self.list_modified_characters(last_sync)

        if char_ids:
            characters = await self.fetch_pcs(char_ids)

            for actor in characters:
                await self.index_actor(actor)

        self._cache["last_modified_characters_sync"] = new_sync.int_timestamp

    async def reindex_actors(self):
        for actor in await self.fetch_pcs():
            try:
                await self.index_actor(actor)
            except MeilisearchApiError as e:
                self._logger.warning(str(e))

    async def index_actor(self, actor):
        actor['id'] = actor['_id']
        del actor['_id']

        self._logger.debug(f'Indexing actor/{actor["name"]}')
        self._ms.index('foundry_actor').add_documents([actor])

    async def backup(self, schemas: Optional[list] = None, reaction_msg: Optional[dict] = None):
        clean_schemas = 'all'
        channel = message = None

        if schemas:
            clean_schemas = ','.join(schemas)

        if reaction_msg and 'channel_id' in reaction_msg and 'message_id' in reaction_msg:
            channel = await self._discord.fetch_channel(reaction_msg['channel_id'])
            message = await channel.fetch_message(reaction_msg['message_id'])
            await message.add_reaction('\U000025B6')

        await self._api.management.foundry.backup(clean_schemas)

        if channel and message:
            await message.add_reaction('\U00002705')

    async def upgrade_audit(self):
        indexes = {}

        resp = self._ms.multi_search([{
            "indexUid": idx.uid,
            "filter": "'@timestamp' EXISTS",
            "limit": 5000
        } for idx in self.audit_indexes])

        for results in resp['results']:
            hit_count = 0

            if (uid := results['indexUid']) not in indexes:
                self._logger.debug(f'Adding {uid} to index cache')
                indexes[uid] = self._ms.index(uid)

            index = indexes[uid]

            self._logger.debug(f'Upgrading {results["estimatedTotalHits"]} entries from {uid}')
            for hit in results['hits']:
                iso_in = hit.pop('@timestamp')
                arrow_obj = arrow.get(iso_in)
                hit['timestamp'] = arrow_obj.int_timestamp
                index.add_documents([hit])
                hit_count += 1
                self._logger.debug(f'Upgraded {hit_count}/{results["estimatedTotalHits"]}')
