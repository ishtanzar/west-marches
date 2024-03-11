import requests
from typing import Optional, List

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

    async def find(self, query: Optional[object] = None) -> List[dict]:
        resp = await self.search(json=query)
        return resp.json()

    async def find_one(self, query: Optional[object] = None, default=None) -> dict:
        items = await self.find(query)
        return (items or (default,))[0]

    async def update(self, item_id, update):
        return (await self.patch(item_id, json=update)).json()

    async def update_full(self, item_id, update):
        return (await self.put(item_id, json=update)).json()

    async def create(self, create):
        return (await self.post(json=create)).json()

    def on_response(self, response: requests.Response) -> requests.Response:
        ex: Optional[HTTPException] = None

        if 400 <= (response_code := response.status_code) < 500:
            ex = ClientException(response)
        elif 500 <= response_code:
            ex = ServerException(response)

        if ex:
            self._logger.warning(f'{response.request.method} {response.request.url} - {response_code} - {response.text}',
                                 extra={'exception': ex.asdict()})
            raise ex
        else:
            self._logger.debug(f'{response.request.method} {response.request.url} - {response_code}')

        return response
