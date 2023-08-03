import logging

import requests


class ApiClient:

    def __init__(self, config) -> None:
        self._config = config
        self.logger = logging.getLogger('api')

    async def search_users_from_kanka_ids(self, kanka_ids):
        return await self.search_users({"kanka.id": { "$in": kanka_ids }})

    async def search_users_from_foundry_ids(self, foundry_ids):
        return await self.search_users({"foundry._id": { "$in": foundry_ids }})

    async def search_users(self, query):
        resp = requests.request('search', f'{self._config.api.endpoint}/users', json=query)
        self.logger.debug(f'GET {resp.url} - {resp.status_code}')

        if resp.status_code == 200:
            return resp.json()

