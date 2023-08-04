import logging

from types import SimpleNamespace

import asyncio
import arrow
import pytest
from elasticsearch import AsyncElasticsearch as Elasticsearch
from unittest.mock import Mock, patch, AsyncMock, ANY

from services.api import ApiClient
from services.foundry import Foundry
from services.kanka import Kanka
from services.utils import Config


pytest_plugins = ('pytest_asyncio',)

@pytest.fixture()
def es() -> Elasticsearch:
    return AsyncMock(Elasticsearch)

@pytest.fixture()
def config() -> Config:
    return Config(
        cache=Config(base_path='/dev/null'),
        kanka=Config(api_endpoint='http://devnull.lan'),
    )

@pytest.fixture()
def api(config) -> ApiClient:
    return AsyncMock(ApiClient)

@pytest.fixture()
def foundry(es) -> Foundry:
    return AsyncMock(Foundry)

@pytest.fixture()
def kanka(foundry, es, config, api) -> Kanka:
    return Kanka(config,
                 Mock(),
                 Mock(),
                 es,
                 foundry,
                 api)


@pytest.mark.asyncio
async def test_ownership(foundry: Foundry, es: Elasticsearch, kanka: Kanka, api: ApiClient, caplog):
    some_date = arrow.utcnow().shift(months=-3)
    actor_id = 12345
    actor_name = 'pytest_Actor'

    user1 = SimpleNamespace(foundry='azer123', kanka=SimpleNamespace(id='8764539'))
    user2 = SimpleNamespace(foundry='lsnx820', kanka=SimpleNamespace(id='0428366', name='Randall'))
    user3 = SimpleNamespace(foundry='83xks74', kanka=SimpleNamespace(id='7294953'))
    foundry_owner = 'azer123'
    kanka_owner = '8764539'

    # def es_search(index: str, **kwargs):
    #     if index.startswith('foundry_audit'):
    #         return {
    #             'hits': {
    #                 'total': {'value': 0},
    #                 'hits': []
    #             }
    #         }
    #
    #     if index == 'kanka_character':
    #         return {
    #             'hits': {
    #                 'total': {'value': 0},
    #                 'hits': []
    #             }
    #         }
    #
    #     raise RuntimeError()
    #
    # es.search = AsyncMock(side_effect=es_search)


    foundry.list_modified_characters.return_value = [actor_id]
    foundry.fetch_pcs.return_value = [{
        'name': actor_name,
        'permission': {
            user1.foundry: 3,
            user2.foundry: 3
        }
    }]

    with patch.object(kanka, 'search_indexed_character_from_name', new_callable=AsyncMock) as search_indexed_character_from_name, \
        patch.object(kanka, 'add_user_entity_permission', new_callable=AsyncMock) as add_user_entity_permission, \
        caplog.at_level(logging.DEBUG):

        search_indexed_character_from_name.return_value = {
            'id': actor_id,
            'name': 'kanka_actor',
            'acls': {
                'users': [user1.kanka.id]
            }
        }

        api.search_users_from_kanka_ids.return_value = [{
            'foundry': {
                '_id': user1.foundry
            }
        }]

        api.search_users_from_foundry_ids.return_value = [{
            'kanka': {
                'id': user2.kanka.id,
                'name': user2.kanka.name
            }
        }]

        await kanka.ownership(some_date.isoformat())

        foundry.list_modified_characters.assert_called_with(some_date.isoformat())
        foundry.fetch_pcs.assert_called_with(ids=[actor_id])
        search_indexed_character_from_name.assert_called_with(actor_name)
        add_user_entity_permission.assert_called()


    # es.search.assert_any_call(index=f'foundry_audit-{some_date.strftime("%Y.%m")}', query={
    #     'range': {
    #         '@timestamp': {
    #             'gt': some_date.isoformat()
    #         }
    #     }
    # }, size=ANY, from_=ANY)
