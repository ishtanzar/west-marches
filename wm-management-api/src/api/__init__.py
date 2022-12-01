import asyncio
import logging
import os
import threading
from functools import wraps
from logging import Logger
from typing import Optional, Any

import hypercorn
import time
from passlib.apache import HtpasswdFile
from quart import Quart, Response, request, abort

from services.backup import BackupService
from services.chatbot import IntentService
from services.discord import DiscordService
from services.docker import FoundryProject
from services.foundryvtt import FoundryService
from services.kanka import KankaService
from utils import get_logger


class BasicAuth:
    def __init__(self, htpasswd):
        self.users = HtpasswdFile(htpasswd)
        self.log = get_logger(self)

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
    _intent_service: IntentService
    _task: asyncio.Future

    instance: "WestMarchesApi"
    log: Logger

    def __init__(
        self, import_name: str, compose: FoundryProject,
        backup: BackupService, foundry: FoundryService,
        kanka: KankaService, intent_service: IntentService
    ) -> None:
        super().__init__(import_name)
        WestMarchesApi.instance = self
        WestMarchesApi.log = get_logger(self)

        self._compose = compose
        self._backup = backup
        self._foundry = foundry
        self._kanka = kanka
        self._intent_service = intent_service
        self._auth = BasicAuth(os.environ['HTPASSWD_PATH'])

        self.setup_routes()

    def run(self, host: Optional[str] = None, port: Optional[int] = None, debug: Optional[bool] = None,
            use_reloader: bool = True, loop: Optional[asyncio.AbstractEventLoop] = None, ca_certs: Optional[str] = None,
            certfile: Optional[str] = None, keyfile: Optional[str] = None, **kwargs: Any) -> None:

        if loop is None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        bg_loop = asyncio.new_event_loop()
        threading.Thread(target=bg_loop.run_forever, daemon=True).start()

        fut = asyncio.run_coroutine_threadsafe(self.setup(), loop=bg_loop)
        self._task = asyncio.wrap_future(fut, loop=loop)
        # bg_loop.call_soon_threadsafe(self._task)

        super().run(host, port, use_reloader=use_reloader, loop=loop)

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
    def kanka(self) -> KankaService:
        return self._kanka

    @property
    def intents(self) -> IntentService:
        return self._intent_service

    async def setup(self):
        self._intent_service.setup(self._task)

    @staticmethod
    def setup_routes() -> None:
        WestMarchesApi.log.debug('setup_routes')
        import api.foundry.routes
        import api.backups.routes
        import api.intents.routes
        # import api.sessions.routes
        import api.reports.routes
        import api.routes
