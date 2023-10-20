from logging import Logger

import asyncio
import os
import threading
from functools import wraps
from inspect import getfullargspec
from passlib.apache import HtpasswdFile
from quart import Quart, request, abort
from typing import Optional, Any

from services.backup import BackupService
from services.docker import FoundryProject
from services.kanka import KankaService
from utils import get_logger
from westmarches_utils.api.foundry import FoundryApi


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

            argspec = getfullargspec(func)

            if 'user' in argspec.args:
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
    _task: asyncio.Future

    instance: "WestMarchesApi"
    log: Logger

    def __init__(
        self, import_name: str, compose: FoundryProject,
        backup: BackupService, foundry: FoundryApi,
        kanka: KankaService
    ) -> None:
        super().__init__(import_name)
        WestMarchesApi.instance = self
        WestMarchesApi.log = get_logger(self)

        self._compose = compose
        self._backup = backup
        self._foundry = foundry
        self._kanka = kanka
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
    def foundryvtt(self) -> FoundryApi:
        return self._foundry

    @property
    def kanka(self) -> KankaService:
        return self._kanka

    async def setup(self):
        pass

    @staticmethod
    def setup_routes() -> None:
        WestMarchesApi.log.debug('setup_routes')
        import api.foundry.routes
        import api.backups.routes
        import api.reports.routes
        import api.routes
