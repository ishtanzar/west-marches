import logging
import os
from logging import Logger

import time
from flask import Flask, Response, request
from flask_htpasswd import HtPasswdAuth

from services.backup import BackupService
from services.docker import FoundryProject
from services.foundryvtt import FoundryService


class WestMarchesApi(Flask):
    _auth: HtPasswdAuth
    _compose: FoundryProject
    _backup: BackupService

    instance: "WestMarchesApi"
    log: Logger

    def __init__(self, import_name: str, compose: FoundryProject, backup: BackupService, foundry: FoundryService) \
            -> None:
        super().__init__(import_name)
        WestMarchesApi.instance = self
        WestMarchesApi.log = logging.getLogger(type(self).__name__)

        self.config['FLASK_HTPASSWD_PATH'] = os.environ['HTPASSWD_PATH']

        self._compose = compose
        self._backup = backup
        self._foundry = foundry
        self._auth = HtPasswdAuth(self)

        self.setup_routes()

        self.before_request(lambda: self.on_request())
        self.after_request(lambda resp: self.on_response(resp))

    @property
    def auth(self) -> HtPasswdAuth:
        return self._auth

    @property
    def compose(self) -> FoundryProject:
        return self._compose

    @property
    def backup(self) -> BackupService:
        return self._backup

    @property
    def foundryvtt(self) -> FoundryService:
        return self._foundry

    @staticmethod
    def setup_routes() -> None:
        WestMarchesApi.log.debug('setup_routes')
        import api.routes

    @staticmethod
    def on_request():
        WestMarchesApi.log.debug('on_request')
        request.start_time = time.time()

    def on_response(self, response: Response) -> Response:
        WestMarchesApi.log.debug("on_response")

        msg = ""
        if response.status_code >= 400:
            msg = response.get_data(True)

        WestMarchesApi.log.info(msg, extra={
            'exec_time': time.time() - request.start_time,
            'useragent': request.user_agent,
            'http_method': request.method,
            'request_scheme': request.scheme,
            'http_status': response.status_code,
            'url': request.url,
            'content_type': response.mimetype,
            'query_string': request.query_string,
            'data': request.data,
            'referrer': request.referrer,
            'user': request.remote_user if request.remote_user else '',
        })

        return response
