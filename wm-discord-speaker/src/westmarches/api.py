import logging
from abc import ABC, abstractmethod

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

    def backup(self):
        self._client.post('/backup/perform')

    def restart(self):
        self._client.post('/container/restart/foundry')


class WestMarchesApiClient:

    def __init__(self, auth: AbstractAuth, endpoint="manager_api") -> None:
        self._auth = auth
        self._endpoint = endpoint

        self._foundry = FoundryApi(self)

    def post(self, path: str):
        ex = None  # type: HTTPException
        resp = requests.post(self._endpoint + path, auth=self._auth())

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
