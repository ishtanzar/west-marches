import json
from typing import Optional

import requests
import smart_open

from utils import get_logger


class FoundryApiException:
    pass


class FoundryService:

    def __init__(self, endpoint: str = 'http://foundry') -> None:
        self.log = get_logger(self)
        self._endpoint = endpoint

    def find_actors(self):
        with smart_open.open('%s/api/actors' % self._endpoint) as fp:
            return json.load(fp)

    def add_user(self, name: str):
        resp: requests.Response = requests.post('%s/api/users' % self._endpoint, json={
            'name': name
        })

        if resp.status_code >= 400:
            self.log.warning('Failed to create user', extra={'status_code': resp.status_code, 'response': resp})

        resp_json = resp.json()
        return resp_json['user_id']

    def update_user(self, user_id: str, name: Optional[str] = None, role: Optional[int] = None):
        resp: requests.Response = requests.put('%s/api/users/%s' % (self._endpoint, user_id), json={
            'name': name,
            'role': role
        })

        if resp.status_code >= 400:
            self.log.warning('Failed to update user', extra={'status_code': resp.status_code, 'response': resp})
