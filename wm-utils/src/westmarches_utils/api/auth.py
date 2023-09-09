from functools import wraps

from abc import ABC, abstractmethod


class AbstractClientAuth(ABC):

    @abstractmethod
    def authenticate(self, *args, **kwargs):
        pass


class Basic(AbstractClientAuth):

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

    def authenticate(self, *args, **kwargs):
        if 'auth' not in kwargs:
            kwargs['auth'] = self._username, self._password

        return args, kwargs


class APIKey(AbstractClientAuth):

    def __init__(self, api_key=None):
        self.api_key = api_key

    def authenticate(self, *args, **kwargs):
        method = 'ApiKey-v1'
        header = 'Authorization'
        if 'headers' not in kwargs or header not in kwargs['headers']:
            kwargs['headers'] = kwargs['headers'] if 'headers' in kwargs else {}
            kwargs['headers'][header] = method + ' ' + self.api_key

        return args, kwargs
