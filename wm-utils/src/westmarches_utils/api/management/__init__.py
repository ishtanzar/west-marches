from typing import Optional

from westmarches_utils.api import AbstractApi, AbstractClientAuth
from westmarches_utils.api.management.foundry import FoundryApi
from westmarches_utils.api.management.intents import IntentsApi
from westmarches_utils.api.management.reports import ReportsApi
from westmarches_utils.api.management.sessions import SessionApi


class ManagementApi(AbstractApi):

    def __init__(self, endpoint: str, auth: Optional[AbstractClientAuth] = None) -> None:
        super().__init__(endpoint, auth)

        self._sessions = SessionApi(endpoint, auth)
        self._foundry = FoundryApi(endpoint, auth)
        self._intents = IntentsApi(endpoint, auth)
        self._reports = ReportsApi(endpoint, auth)

    @property
    def foundry(self) -> FoundryApi:
        return self._foundry

    @property
    def sessions(self) -> SessionApi:
        return self._sessions

    @property
    def intents(self):
        return self._intents

    @property
    def reports(self):
        return self._reports
