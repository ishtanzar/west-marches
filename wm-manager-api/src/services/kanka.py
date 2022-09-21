import datetime
import logging

import requests

from utils import get_logger


class KankaService:

    def __init__(self, token, campaign, endpoint='https://kanka.io') -> None:
        self._token = token
        self._campaign = campaign
        self._public_url = endpoint + '/fr/campaign/' + campaign
        self._api_endpoint = endpoint + '/api/1.0/campaigns/' + campaign
        self.log = get_logger(self)

    def request(self, method, url, **kwargs):
        if 'headers' in kwargs:
            kwargs['headers']['Authorization'] = 'Bearer ' + self._token
        else:
            kwargs['headers'] = {'Authorization': 'Bearer ' + self._token}

        resp: requests.Response = requests.request(method, url, **kwargs)

        if resp.status_code >= 400:
            if resp.headers.get('content-type') == 'application/json':
                message = resp.json()
            else:
                message = resp.text

            self.log.warning(message, extra={'status_code': resp.status_code, 'response': resp})

        return resp

    def get(self, url, params=None, **kwargs):
        return self.request('get', url, params=params, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.request('post', url, data=data, json=json, **kwargs)

    def patch(self, url, data=None, json=None, **kwargs):
        return self.request('patch', url, data=data, json=json, **kwargs)

    async def create_journal(self, name: str, content: str, journal_type: str, date: datetime.datetime, tags=None):
        resp: requests.Response = self.post(self._api_endpoint + '/journals', json={
            'name': name,
            'type': journal_type,
            'content': content,
            'date': date.strftime('%Y-%m-%d'),
            'tags': tags if tags else [],
        })

        response_dict = resp.json()

        return response_dict['data']

    async def set_journal_tags(self, journal_id: int, tags: [int]):
        endpoint = self._api_endpoint + '/journals/' + str(journal_id)

        resp: requests.Response = self.get(endpoint)
        name = resp.json()['data']['name']

        resp: requests.Response = self.patch(endpoint, json={
            'name': name,
            'tags': tags
        })

    async def set_entity_attribute(self, entity_id, name, value, private=False):
        resp = self.post('%s/entities/%s/attributes' % (self._api_endpoint, entity_id), json={
            'name': name,
            'value': value,
            'entity_id': entity_id,
            'is_private': private
        })

    async def find_journal(self, **params):
        resp = self.get('%s/journals' % self._api_endpoint, params=params)
        journals = resp.json()['data']

        for journal in journals:
            journal['url'] = '%s/journals/%s' % (self._public_url, journal['id'])

        return journals
