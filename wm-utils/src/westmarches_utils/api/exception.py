import requests


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
