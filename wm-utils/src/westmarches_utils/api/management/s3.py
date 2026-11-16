import asyncio
from dataclasses import dataclass, field
from typing import Literal, TypedDict

import requests

from westmarches_utils.api import AbstractApi
from westmarches_utils.api.exception import ClientException, ServerException


@dataclass(frozen=True)
class Credentials:
    application_id: str
    access_key: str
    secret_key: str = field(repr=False)


class DiscordMember(TypedDict):
    type: Literal["discord"]
    discord_username: str
    discord_id: str


class S3Api(AbstractApi):
    def on_response(self, response):
        if response.status_code >= 400:
            self._logger.warning("S3 credentials request failed (%s)", response.status_code)
            error = ServerException if response.status_code >= 500 else ClientException
            raise error(response)
        return response

    async def _request(self, method, url="", **kwargs):
        if self._auth:
            _, kwargs = self._auth.authenticate(**kwargs)
        kwargs.setdefault("timeout", (5, 20))
        response = await asyncio.to_thread(
            requests.request, method, self._endpoint + url, **kwargs
        )
        return self.on_response(response)

    async def credentials(self, member: DiscordMember) -> Credentials:
        response = await self.post("/s3/credentials", json=member)
        return Credentials(**response.json())

    async def revoke(self, member: DiscordMember) -> dict:
        return (await self.post("/s3/credential/revoke", json=member)).json()
