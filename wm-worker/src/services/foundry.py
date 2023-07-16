import os.path
from pathlib import Path

import arrow
import json
import logging
import requests
from elasticsearch import ApiError,AsyncElasticsearch as Elasticsearch


class Foundry:

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es
        self.logger = logging.getLogger('foundry')

    async def initialize(self):
        index_name = 'foundry_actor'
        index_config_file = Path(__file__) / '../../resources/kanka_actor.index.json'

        opts = json.load(index_config_file.resolve().open())

        if await self.es.indices.exists(index=index_name):
            await self.es.indices.put_settings(index=index_name, settings=opts['settings'])
            await self.es.indices.put_mapping(index=index_name, **opts['mappings'])
        else:
            await self.es.indices.create(index=index_name, **opts)

        for index in await self.es.indices.get(index='*'):
            await self.es.indices.put_settings(index=index, settings={'index': {'number_of_replicas': 0}})

    async def fetch_pcs(self, ids=[]):
        query = {
            'type': 'character'
        }

        if len(ids) > 0:
            query['_id'] = {'$in': ids}

        resp = requests.request('search', 'http://foundry:30000/api/actors', json=query)

        if resp.status_code == 200:
            self.logger.debug(f'GET {resp.url} - {resp.status_code}')
            return resp.json()['actors']

    async def list_modified_characters(self, last_sync: str = None) -> list:
        modified = set()
        query_from = 0
        query_size = 1000
        last_sync_obj = arrow.get(last_sync) if last_sync else arrow.utcnow().shift(hours=-1)

        while True:
            resp = await self.es.search(index=f'foundry_audit-{last_sync_obj.strftime("%Y.%m")}', query={
                'range': {
                    '@timestamp': {
                        'gt': last_sync_obj.isoformat()
                    }
                }
            }, size=query_size, from_=query_from)

            for h in resp['hits']['hits']:
                modified.add(h['_source']['fields']['actor'])

            if resp['hits']['total']['value'] < (query_from + query_size):
                break

            query_from = query_from + query_size

        return list(modified)

    async def cron(self):
        char_ids = await self.list_modified_characters()
        characters = await self.fetch_pcs(ids=char_ids)

        for actor in characters:
            await self.index_actor(actor)

    async def reindex(self):
        for actor in await self.fetch_pcs():
            try:
                await self.index_actor(actor)
            except ApiError as e:
                self.logger.warning(e.info['error']['reason'])

    async def index_actor(self, actor):
        actor['id'] = actor['_id']
        del actor['_id']

        self.logger.debug(f'Indexing actor/{actor["name"]}')
        await self.es.index(index='foundry_actor', id=actor['id'], document=actor)
