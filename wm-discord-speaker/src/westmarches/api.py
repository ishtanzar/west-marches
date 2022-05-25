import logging
from abc import ABC, abstractmethod
from typing import Optional

import requests

log = logging.getLogger("red.westmarches.api")


class AbstractAuth(ABC):

    @abstractmethod
    def __call__(self):
        pass


class BasicAuth(AbstractAuth):

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

    def __call__(self):
        return self._username, self._password


class HTTPException(IOError):
    def __init__(self, response: requests.Response) -> None:
        self._response = response

    @property
    def response(self) -> requests.Response:
        return self._response

    def asdict(self):
        return {
            '_class': type(self).__name__,
            'request': {
                'method': self._response.request.method,
                'url': self._response.request.url,
                'body': self._response.request.body,
                'headers': self._response.request.headers
            },
            'response': {
                'code': self._response.status_code,
                'headers': self._response.headers,
                'body': self._response.text
            }
        }


class ServerException(HTTPException):
    pass


class ClientException(HTTPException):
    pass


class AbstractApi(ABC):

    def __init__(self, client: "WestMarchesApiClient") -> None:
        self._client = client


class FoundryApi(AbstractApi):

    async def backup(self) -> None:
        await self._client.post('/backup/perform')

    async def list_backups(self) -> dict:
        resp = await self._client.get('/backup/list')
        return resp.json()

    async def restore(self, backup_id: str) -> None:
        await self._client.post('/backup/restore/%s' % backup_id)

    async def restart(self) -> None:
        await self._client.post('/foundry/restart')

    async def actors(self) -> dict:
        resp = await self._client.get('/foundry/actors')
        return resp.json()

    async def users(self, filter: Optional[object] = None):
        resp = await self._client.get('/foundry/users', params=filter)
        return resp.json()

    async def users_add(self, name, discord: Optional[object] = None) -> str:
        resp = await self._client.post('/foundry/users', json={
            'name': name,
            'discord': discord
        })
        return resp.json()

    async def users_update(self, user_id, name: Optional[str] = None, role: Optional[int] = None,
                           password: Optional[str] = None) -> str:
        body = {}
        if name:
            body['name'] = name
        if role:
            body['role'] = role
        if password:
            body['password'] = password

        resp = await self._client.put('/foundry/users/%s' % user_id, json=body)
        return resp.json()


class SessionApi(AbstractApi):

    async def schedule(self, date: str, message: dict) -> dict:
        resp = await self._client.post('/session', json={
            'date': date,
            'message': message,
        })
        return resp.json()


class IntentsApi(AbstractApi):

    async def add_pattern(self, intent, pattern) -> None:
        await self._client.post('/intent/%s/pattern' % intent, json={
            'pattern': pattern
        })

    async def train(self) -> None:
        await self._client.post('/intent/train')

    async def predict(self, message) -> dict:
        resp = await self._client.post('/intent/predict', json={
            'message': message
        })
        return resp.json()


class WestMarchesApiClient:

    def __init__(self, auth: AbstractAuth, endpoint="manager_api") -> None:
        self._auth = auth
        self._endpoint = endpoint

        self._sessions = SessionApi(self)
        self._foundry = FoundryApi(self)
        self._intents = IntentsApi(self)

    async def _request(self, method, *args, **kwargs):
        resp = requests.request(method, auth=self._auth(), *args, **kwargs)

        return self.on_response(resp)

    async def get(self, path: str, *args, **kwargs):
        return await self._request('get', self._endpoint + path, *args, **kwargs)

    async def post(self, path: str, *args, **kwargs):
        return await self._request('post', self._endpoint + path, *args, **kwargs)

    async def put(self, path: str, *args, **kwargs):
        return await self._request('put', self._endpoint + path, *args, **kwargs)

    @staticmethod
    def on_response(resp: requests.Response) -> requests.Response:
        ex: Optional[HTTPException] = None

        if 400 <= resp.status_code < 500:
            ex = ClientException(resp)
        elif 500 <= resp.status_code:
            ex = ServerException(resp)

        if ex:
            log.warning('Received %d when calling %s', resp.status_code, resp.request.url,
                        extra={'exception': ex.asdict()})
            raise ex

        return resp

    @property
    def foundry(self) -> FoundryApi:
        return self._foundry

    @property
    def sessions(self) -> SessionApi:
        return self._sessions

    @property
    def intents(self):
        return self._intents
