import requests
from typing import Optional

from abc import ABC

from westmarches_utils import get_logger
from westmarches_utils.api.auth import AbstractClientAuth
from westmarches_utils.api.exception import HTTPException, ClientException, ServerException


class AbstractApi(ABC):

    def __init__(self, endpoint: str, auth: Optional[AbstractClientAuth] = None) -> None:
        self._auth = auth
        self._endpoint = endpoint
        self._logger = get_logger(self)

    async def _request(self, method, url='', **kwargs) -> requests.Response:
        if self._auth:
            _, kwargs = self._auth.authenticate(**kwargs)

        if url and not url.startswith('/'):
            url = '/' + url

        resp = requests.request(method, self._endpoint + url, **kwargs)

        return self.on_response(resp)

    async def search(self, *args, **kwargs) -> requests.Response:
        return await self._request('search', *args, **kwargs)

    async def get(self, *args, **kwargs) -> requests.Response:
        return await self._request('get', *args, **kwargs)

    async def post(self, *args, **kwargs) -> requests.Response:
        return await self._request('post', *args, **kwargs)

    async def patch(self, *args, **kwargs) -> requests.Response:
        return await self._request('patch', *args, **kwargs)

    async def put(self, *args, **kwargs) -> requests.Response:
        return await self._request('put', *args, **kwargs)

    async def find(self, query: Optional[object] = None):
        resp = await self.search(json=query)
        return resp.json()

    async def find_one(self, query: Optional[object] = None, default=None):
        items = await self.find(query)
        return (items or (default,))[0]

    async def update(self, item_id, update):
        await self.patch(item_id, json=update)

    async def create(self, create):
        await self.patch(json=create)

    def on_response(self, resp: requests.Response) -> requests.Response:
        ex: Optional[HTTPException] = None

        if 400 <= resp.status_code < 500:
            ex = ClientException(resp)
        elif 500 <= resp.status_code:
            ex = ServerException(resp)

        if ex:
            self._logger.warning('Received %d when calling %s', resp.status_code, resp.request.url,
                        extra={'exception': ex.asdict()})
            raise ex

        return resp
