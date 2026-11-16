from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.discord import DiscordError, DiscordService


@pytest.mark.asyncio
async def test_rest_client_login_and_close(monkeypatch):
    service = DiscordService("token", "123", "456")
    assert service.client.intents.value == 0
    login = AsyncMock()

    async def static_login(token):
        assert token == "token"
        return {
            "id": "456", "username": "bot", "discriminator": "0",
            "avatar": None, "bot": True,
        }

    login.side_effect = static_login
    monkeypatch.setattr(service.client.http, "static_login", login)
    monkeypatch.setattr(
        service.client.http, "application_info",
        AsyncMock(return_value={
            "id": "456", "name": "bot", "description": "", "icon": None,
            "flags": 0, "bot_public": True, "bot_require_code_grant": False,
            "owner": {
                "id": "789", "username": "owner", "discriminator": "0",
                "avatar": None,
            },
            "verify_key": "public-key",
        }),
    )
    try:
        await service.start()
        login.assert_awaited_once_with("token")
        assert str(service.client.user.id) == "456"
    finally:
        await service.close()
    assert service.client.is_closed()


@pytest.mark.asyncio
@pytest.mark.parametrize("identity", [
    None,
    SimpleNamespace(id=789, bot=True),
    SimpleNamespace(id=456, bot=False),
])
async def test_login_rejects_invalid_bot_identity(identity):
    service = DiscordService("token", "123", "456")
    await service.client.close()
    service.client = SimpleNamespace(login=AsyncMock(), user=identity)
    with pytest.raises(DiscordError, match="discord_bot_configuration"):
        await service.start()
    service.client.login.assert_awaited_once_with("token")
