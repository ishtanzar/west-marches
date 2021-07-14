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
        await self._client.post('/container/restart/foundry')

    async def roster(self) -> dict:
        resp = await self._client.get('/roster')
        return resp.json()


class SessionApi(AbstractApi):

    async def schedule(self, date: str, message: dict) -> dict:
        resp = await self._client.post('/session', json={
            'date': date,
            'message': message,
        })
        return resp.json()


class WestMarchesApiClient:

    def __init__(self, auth: AbstractAuth, endpoint="manager_api") -> None:
        self._auth = auth
        self._endpoint = endpoint

        self._sessions = SessionApi(self)
        self._foundry = FoundryApi(self)

    async def get(self, path: str):
        resp = requests.get(self._endpoint + path, auth=self._auth())

        return self.on_response(resp)

    async def post(self, path: str, *args, **kwargs):
        resp = requests.post(self._endpoint + path, auth=self._auth(), *args, **kwargs)

        return self.on_response(resp)

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
