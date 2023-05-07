import requests

from utils import get_logger


class FoundryApiException:
    pass


class FoundryService:

    def __init__(self, endpoint: str = 'http://foundry') -> None:
        self.log = get_logger(self)
        self._endpoint = endpoint

    def _request(self, method, url, **kwargs) -> requests.Response:
        self.log.debug(
            'req_method=%s, req_url=%s, req_headers=%s, req_json=%s',
            method,
            url,
            str(kwargs['headers'] if 'headers' in kwargs else {}),
            str(kwargs['json'] if 'json' in kwargs else {})
        )

        resp: requests.Response = requests.request(method, url, **kwargs)
        self.log.info('%s %s - %i', method.upper(), url, resp.status_code)

        self.log.debug(
            'resp_code=%i, resp_headers=%s, resp_body=%s',
            resp.status_code,
            str(resp.headers),
            resp.text
        )

        if resp.status_code >= 400:
            self.log.warning('Failed to get %s', url,
                             extra={'status_code': resp.status_code, 'response': resp})

        return resp

    def get(self, path, **kwargs) -> requests.Response:
        return self._request('get', self._endpoint + path, **kwargs)

    def post(self, path, **kwargs) -> requests.Response:
        return self._request('post', self._endpoint + path, **kwargs)

    def put(self, path, **kwargs) -> requests.Response:
        return self._request('put', self._endpoint + path, **kwargs)
