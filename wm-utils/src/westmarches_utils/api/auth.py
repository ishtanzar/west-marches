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


class AuthorizationHeader(AbstractClientAuth):

    def __init__(self, api_key=None, method='Bearer', header='Authorization'):
        self._api_key = api_key
        self._method = method
        self._header = header

    def authenticate(self, *args, **kwargs):
        if 'headers' not in kwargs or self._header not in kwargs['headers']:
            kwargs['headers'] = kwargs['headers'] if 'headers' in kwargs else {}
            kwargs['headers'][self._header] = self._method + ' ' + self._api_key

        return args, kwargs


class Bearer(AuthorizationHeader):

    def __init__(self, api_key=None):
        super().__init__(api_key)


class APIKey(AuthorizationHeader):

    def __init__(self, api_key=None):
        super().__init__(api_key, method='ApiKey-v1')
