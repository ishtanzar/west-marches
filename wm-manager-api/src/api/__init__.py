import logging
import os
from functools import wraps
from logging import Logger

import time
from passlib.apache import HtpasswdFile
from quart import Quart, Response, request, abort

from services.agenda import AgendaService
from services.backup import BackupService
from services.chatbot import ChatbotService
from services.discord import DiscordService
from services.docker import FoundryProject
from services.foundryvtt import FoundryService
from services.kanka import KankaService


class BasicAuth:
    def __init__(self, htpasswd):
        self.users = HtpasswdFile(htpasswd)
        self.log = logging.getLogger(type(self).__name__)

    def required(self, func):
        @wraps(func)
        async def decorated(*args, **kwargs):
            is_valid, user = self.authenticate()
            if not is_valid:
                self.log.warning('Invalid login from %s', user)
                abort(401)
            kwargs['user'] = user
            return await func(*args, **kwargs)
        return decorated

    def authenticate(self):
        is_valid = False
        user = None

        if request.authorization:
            user = request.authorization.username
            is_valid = self.users.check_password(user, request.authorization.password)

        return is_valid, user


class WestMarchesApi(Quart):
    _auth: BasicAuth
    _compose: FoundryProject
    _backup: BackupService
    _chatbot: ChatbotService

    instance: "WestMarchesApi"
    log: Logger

    def __init__(
        self, import_name: str, compose: FoundryProject,
        backup: BackupService, foundry: FoundryService,
        discord: DiscordService, kanka: KankaService,
    ) -> None:
        super().__init__(import_name)
        WestMarchesApi.instance = self
        WestMarchesApi.log = logging.getLogger(type(self).__name__)

        self._compose = compose
        self._backup = backup
        self._foundry = foundry
        self._discord = discord
        self._kanka = kanka
        self._auth = BasicAuth(os.environ['HTPASSWD_PATH'])

        self.setup_routes()

        self.before_request(lambda: self.on_request())
        self.after_request(lambda resp: self.on_response(resp))

    @property
    def auth(self) -> BasicAuth:
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

    @property
    def discord(self) -> DiscordService:
        return self._discord

    @property
    def kanka(self) -> KankaService:
        return self._kanka

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
        })

        return response
