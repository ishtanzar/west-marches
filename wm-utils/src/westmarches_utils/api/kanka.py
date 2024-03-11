import asyncio
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

import requests
from typing import Optional

from westmarches_utils.api.abstract import AbstractApi
from westmarches_utils.api.auth import AbstractClientAuth
from westmarches_utils.api.exception import ClientException


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

    async def _request(self, method, url='', **kwargs) -> KankaApiResponse:
        try:
            return KankaApiResponse(await super()._request(method, url, **kwargs))
        except ClientException as e:
            if e.response.status_code == 429:
                await asyncio.sleep(61)

                return await AbstractKankaApi._request(self, method, url, **kwargs)
            else:
                raise e

    async def list_since(self,  page=1, related=False, last_sync=None, **kwargs) -> (list, str):
        params = {"page": page}

        if related:
            params["related"] = int(related)

        if last_sync:
            params["lastSync"] = last_sync

        data = (response := await AbstractKankaApi.get(self, params=params, **kwargs)).data
        response_json = response.json

        if next_url := response_json.get('links', {}).get('next'):
            if next_query := urlparse(next_url).query:
                if (next_page := int(parse_qs(next_query).get('page', [None])[0])) > page:
                    data += (await AbstractKankaApi.list_since(self, next_page, related, last_sync, **kwargs))[0]

        return data, response_json.get('sync')

    async def list(self,  page=1, related=False, **kwargs) -> (list, str):
        data, _ = await AbstractKankaApi.list_since(self, page, related, **kwargs)

        return data


class AbstractEntityApi(AbstractKankaApi):

    async def get(self, **kwargs) -> dict:
        [object_] = await super().list()
        return object_


class EntityApi(AbstractEntityApi):

    @property
    def permissions(self):
        return AbstractKankaApi(self._endpoint + '/entity_permissions', self._auth)

    @property
    def attributes(self):
        return AbstractKankaApi(self._endpoint + '/attributes', self._auth)


class KankaApi(AbstractApi):

    _entities_endpoint = '/entities'
    _users_endpoint = '/users'

    def __init__(self, config: "KankaApiConfig") -> None:
        super().__init__(config.endpoint, config.auth)

        self.__config = config
        self._campaign_endpoint = config.endpoint + '/campaigns/' + str(config.campaign)
        self._journals_endpoint = self._campaign_endpoint + '/journals'

        self._entity_types = AbstractKankaApi(config.endpoint + '/entity-types', self._auth)

        self._journals = AbstractKankaApi(self._journals_endpoint, self._auth)
        self._calendars = AbstractKankaApi(self._campaign_endpoint + '/calendars', self._auth)
        self._characters = AbstractKankaApi(self._campaign_endpoint + '/characters', self._auth)
        self._users = AbstractKankaApi(self._campaign_endpoint + self._users_endpoint, self._auth)
        self._entities = AbstractKankaApi(self._campaign_endpoint + self._entities_endpoint, self._auth)

    @property
    def users(self):
        return self._users

    @property
    def entities(self):
        return self._entities

    @property
    def journals(self):
        return self._journals

    @property
    def characters(self):
        return self._characters

    @property
    def entity_types(self):
        return self._entity_types

    @property
    def calendars(self):
        return self._calendars

    def user(self, entity_id: str) -> AbstractEntityApi:
        return AbstractEntityApi(
            self._campaign_endpoint + self._users_endpoint + '/' + str(entity_id),
            self.__config.auth
        )

    def journal(self, journal_id: str) -> AbstractKankaApi:
        return AbstractKankaApi(self._journals_endpoint + '/' + str(journal_id), self.__config.auth)

    def entity(self, entity_id: str) -> EntityApi:
        return EntityApi(self._campaign_endpoint + self._entities_endpoint + '/' + str(entity_id), self.__config.auth)
