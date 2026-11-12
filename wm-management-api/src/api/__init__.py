from logging import Logger

import hmac
from functools import wraps
from inspect import getfullargspec
from quart import Quart, request, abort
from typing import Optional

from services.backup import BackupService
from services.discord import DiscordService
from services.docker import FoundryProject
from services.kanka import KankaService
from services.scaleway import ScalewayService
from utils import get_logger
from westmarches_utils.api.foundry import FoundryApi


class BasicAuth:
    def __init__(self, password):
        if not password:
            raise ValueError("MGMNT_API_SECRET must be set and non-empty")
        self._password = password.encode("utf-8")
        self.log = get_logger(self)

    def required(self, func):
        @wraps(func)
        async def decorated(*args, **kwargs):
            is_valid, user = self.authenticate()
            if not is_valid:
                self.log.warning('Invalid authentication')
                abort(401)

            argspec = getfullargspec(func)

            if 'user' in argspec.args:
                kwargs['user'] = user

            return await func(*args, **kwargs)
        return decorated

    def authenticate(self):
        authorization = request.authorization
        if (
            authorization is not None
            and authorization.type == "basic"
            and authorization.username == "foundry_manager"
            and authorization.password is not None
            and hmac.compare_digest(
                authorization.password.encode("utf-8"), self._password
            )
        ):
            return True, "foundry_manager"
        return False, None


class WestMarchesApi(Quart):
    _auth: BasicAuth
    _compose: FoundryProject
    _backup: BackupService
    instance: "WestMarchesApi"
    log: Logger

    def __init__(
        self, *,
        import_name: str,
        auth: BasicAuth,
        compose: Optional[FoundryProject] = None,
        backup: Optional[BackupService] = None,
        foundry: Optional[FoundryApi] = None,
        kanka: Optional[KankaService] = None,
        discord: DiscordService,
        scaleway: ScalewayService
    ) -> None:
        super().__init__(import_name)
        WestMarchesApi.instance = self
        WestMarchesApi.log = get_logger(self)

        self._compose = compose
        self._backup = backup
        self._foundry = foundry
        self._kanka = kanka
        self._discord = discord
        self._scaleway = scaleway
        self._auth = auth

        self.before_serving(self.discord.start)
        self.setup_routes()
        self.after_serving(self.discord.close)

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

    @property
    def discord(self) -> DiscordService:
        return self._discord

    @property
    def scaleway(self) -> ScalewayService:
        return self._scaleway

    @staticmethod
    def setup_routes() -> None:
        WestMarchesApi.log.debug('setup_routes')
        import api.foundry.routes
        import api.backups.routes
        import api.reports.routes
        import api.routes
        import api.s3.routes
