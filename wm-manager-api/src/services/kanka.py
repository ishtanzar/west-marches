import datetime
import logging

import requests

from utils import get_logger


class KankaService:

    def __init__(self) -> None:
        self._endpoint = 'https://kanka.io/api/1.0/campaigns/67312'
        self._token = '''eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiZTE0NzU1NDM0ZWVlYjFiZTlhYmI1NDI0ODVjOTc2ZjVhOTE4ZjY0N2I4OTM3NzU4ZTQzNDZiODQ0Y2U5OTY2YjI5N2EyNDFjZTBiZWU1NGEiLCJpYXQiOjE2MjU3NjcyNzYuMDM4ODAyLCJuYmYiOjE2MjU3NjcyNzYuMDM4ODE1LCJleHAiOjE2NTczMDMyNzYuMDMxMDA4LCJzdWIiOiI2OTE5NiIsInNjb3BlcyI6W119.vPwp3q2bPlEQi3CFhfbjnCqr0rIEKB9AxuJ4HjXnsU_AGwKelWRPJdq_koqgTEPZKb_QHxw9eUzTr48dypkXDPHZbVgxpazmT8THhfTppzMlHvqlK74FzTHRwIYmOOQDZjSMnhxla62btWgJ6Hp4E1Vuk36KW33-CmGmXy9GpXuoFY_EKgQMuKLBZI6cSDT6eGltQhqo00EK-kEvtRnfAyoQ7mq65cVwiG3RLLJsZi4oa3YUdZO6KlDQNsHmZ92ikoWtcLudS7e3H5Nrgu1IqUv7osLOhei1H4BrgLya0wnQXdzifMRbwICly-WckqweemBnv9vic_AolhS8tYe_tAbUbYtysMNVP8wVkouGWLba-dFz8rBjW6SKSec1Ecqp2dvlHe4YhVK4r5skb4U6EnoUIlXLmT5HmDHPiOVhcT1go0nsM-pqrUk6o10CLxdV7RBzpGskkHDbL1przTlRmUEDu48lQQ4BiIfgfF0iMn4cwmpfb0z64-j6h_EHC_dDabUJEtV1k8ws4vpJSloek8z4eDykdrZKKTAIpcfhAiyJQ02KCr8I41dDVN5DAazHXQvnIwLtT12O0InVWcU-DRzxy_RHNk2u4InkddyU47DDJTu18v9w2-1B5kpt02sS_hgpSVDKjwhB9mFrds5RkYlVc89qk004OFK0wxSoTo0'''
        self.log = get_logger(self)

    def request(self, method, url, **kwargs):
        if 'headers' in kwargs:
            kwargs['headers']['Authorization'] = 'Bearer ' + self._token
        else:
            kwargs['headers'] = {'Authorization': 'Bearer ' + self._token}

        resp: requests.Response = requests.request(method, url, **kwargs)

        if resp.status_code >= 400:
            if resp.headers.get('content-type') == 'application/json':
                response_dict = resp.json()
                message = response_dict['message']
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

    async def create_journal(self, name: str, type: str, date: datetime.datetime):
        resp: requests.Response = self.post(self._endpoint + '/journals', json={
            'name': name,
            'type': type,
            'date': date.strftime('%Y-%m-%d'),
            'tags': [],
        })

        response_dict = resp.json()

        return response_dict['data']['id']

    async def set_journal_tags(self, journal_id: int, tags: [int]):
        endpoint = self._endpoint + '/journals/' + str(journal_id)

        resp: requests.Response = self.get(endpoint)
        name = resp.json()['data']['name']

        resp: requests.Response = self.patch(endpoint, json={
            'name': name,
            'tags': tags
        })
