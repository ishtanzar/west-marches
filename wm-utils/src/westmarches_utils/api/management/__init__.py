from westmarches_utils.api.abstract import AbstractApi
from westmarches_utils.api.config import ManagementApiConfig
from westmarches_utils.api.management.foundry import FoundryApi
from westmarches_utils.api.management.intents import IntentsApi
from westmarches_utils.api.management.reports import ReportsApi
from westmarches_utils.api.management.sessions import SessionApi
from westmarches_utils.api.management.s3 import S3Api


class ManagementApi(AbstractApi):

    def __init__(self, config: ManagementApiConfig) -> None:
        endpoint, auth = config.endpoint, config.auth
        super().__init__(endpoint, auth)

        self._sessions = SessionApi(endpoint, auth)
        self._foundry = FoundryApi(endpoint, auth)
        self._intents = IntentsApi(endpoint, auth)
        self._reports = ReportsApi(endpoint, auth)
        self._s3 = S3Api(endpoint, auth)

    @property
    def s3(self) -> S3Api:
        return self._s3

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
