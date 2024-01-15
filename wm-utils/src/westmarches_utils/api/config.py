from dataclasses import dataclass

from westmarches_utils.api import AbstractClientAuth
from westmarches_utils.api.kanka import KankaApiConfig


@dataclass
class WestMarchesApiConfig:
    api_auth: AbstractClientAuth
    management_api_auth: AbstractClientAuth
    kanka: KankaApiConfig

    api_endpoint: str = "http://api:3000"
    mgmnt_api_endpoint: str = "http://management_api:5000"
