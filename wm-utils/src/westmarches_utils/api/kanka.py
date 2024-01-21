import asyncio
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

import requests
from typing import Optional

from westmarches_utils.api import AbstractApi, AbstractClientAuth


@dataclass
class KankaApiConfig:
    campaign: int
    auth: Optional[AbstractClientAuth] = None
    endpoint: str = 'https://api.kanka.io/1.0'


class KankaApiResponse:

    def __init__(self, response: requests.Response):
        self._response = response

    @property
    def get(self) -> requests.Response:
        return self._response

    @property
    def json(self):
        return self.get.json()

    @property
    def status_code(self):
        return self.get.status_code

    @property
    def data(self) -> list:
        return _data if isinstance(_data := self.json.get('data', []), list) else [_data]


class AbstractKankaApi(AbstractApi):

    async def get(self, **kwargs) -> KankaApiResponse:
        response = KankaApiResponse(await self._request('get', **kwargs))

        if response.status_code == 429:
            await asyncio.sleep(61)

            return await self.get(**kwargs)

        return response

    async def list_since(self,  page=1, related=False, last_sync=None, **kwargs) -> (list, str):
        params = {"page": page}

        if related:
            params["related"] = int(related)

        if last_sync:
            params["lastSync"] = last_sync

        data = (response := await self.get(params=params, **kwargs)).data
        response_json = response.json

        if next_url := response_json.get('links', {}).get('next'):
            if next_query := urlparse(next_url).query:
                if (next_page := int(parse_qs(next_query).get('page', [None])[0])) > page:
                    data += (await self.list_since(page=next_page, **kwargs))[0]

        return data, response_json.get('sync')

    async def list(self,  page=1, related=False, **kwargs) -> (list, str):
        data, _ = await self.list_since(page, related, **kwargs)

        return data


class AbstractEntityApi(AbstractKankaApi):

    async def get(self, *args, **kwargs) -> dict:
        [object_], sync = await AbstractKankaApi.list(self)
        return object_


class EntityApi(AbstractEntityApi):

    @property
    def permissions(self):
        return AbstractApi(self._endpoint + '/entity_permissions')


class KankaApi(AbstractApi):

    _entities_endpoint = '/entities'
    _users_endpoint = '/users'

    def __init__(self, config: "KankaApiConfig") -> None:
        super().__init__(config.endpoint, config.auth)

        self._campaign_endpoint = config.endpoint + '/campaigns/' + str(config.campaign)
        self._journals = AbstractKankaApi(self._campaign_endpoint + '/journals', self._auth)
        self._calendars = AbstractKankaApi(self._campaign_endpoint + '/calendars', self._auth)
        self._users = AbstractKankaApi(self._campaign_endpoint + self._users_endpoint, self._auth)
        self._entity_types = AbstractKankaApi(config.endpoint + '/entity-types', self._auth)
        self._entities = AbstractKankaApi(self._campaign_endpoint + self._entities_endpoint, self._auth)

    @property
    def users(self):
        return self._users

    @property
    def entities(self):
        return self._entities

    @property
    def entity_types(self):
        return self._entity_types

    @property
    def calendars(self):
        return self._calendars

    def user(self, entity_id: str) -> AbstractEntityApi:
        return AbstractEntityApi(self._entities_endpoint + self._users_endpoint + '/' + entity_id)

    def entity(self, entity_id: str) -> EntityApi:
        return EntityApi(self._campaign_endpoint + self._entities_endpoint + '/' + entity_id)
