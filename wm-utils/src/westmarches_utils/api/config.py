from dataclasses import dataclass

from westmarches_utils.api.auth import AbstractClientAuth
from westmarches_utils.api.kanka import KankaApiConfig


@dataclass
class ManagementApiConfig:
    auth: AbstractClientAuth
    endpoint: str = "http://management_api:5000"


@dataclass
class WestMarchesApiConfig:
    api_auth: AbstractClientAuth
    management: ManagementApiConfig
    kanka: KankaApiConfig

    api_endpoint: str = "http://api:3000"
