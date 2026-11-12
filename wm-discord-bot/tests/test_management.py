from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from westmarches.commands.management import ManagementCommands
from westmarches_utils.api.management.s3 import Credentials, S3Api


class ConfigValue:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self

    def __await__(self):
        async def get():
            return self.value.copy() if isinstance(self.value, list) else self.value
        return get().__await__()

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *args):
        pass


@pytest.fixture
def command():
    command = ManagementCommands()
    command.config = SimpleNamespace(
        messages=ConfigValue({"management.s3.credentials": "Access: %s\nSecret: %s"}),
    )
    command.wm_api = SimpleNamespace(management=SimpleNamespace(s3=AsyncMock()))
    return command


@pytest.fixture
def context():
    dm = SimpleNamespace(delete=AsyncMock())
    return SimpleNamespace(
        author=SimpleNamespace(
            id=123,
            name="ExampleUser",
            send=AsyncMock(return_value=dm),
        ),
        message=SimpleNamespace(add_reaction=AsyncMock()),
        send=AsyncMock(),
    )


async def test_s3_password_sends_credentials_to_dm(command, context):
    client = command.wm_api.management.s3
    client.credentials.return_value = Credentials("app", "access", "one-time-secret")

    await command.s3_passwd(context)

    client.credentials.assert_awaited_once_with({
        "type": "discord",
        "discord_username": "ExampleUser",
        "discord_id": "123",
    })
    context.author.send.assert_awaited_once_with(
        "Access: access\nSecret: one-time-secret"
    )
    context.author.send.return_value.delete.assert_awaited_once_with(delay=30)


async def test_password_command_rejects_incomplete_response(command, context):
    command.wm_api.management.s3.credentials.return_value = Credentials("app", "access", "")

    await ManagementCommands.command_s3_passwd.callback(
        command, context
    )

    context.author.send.assert_not_awaited()
    context.send.assert_awaited_once()
    context.message.add_reaction.assert_not_awaited()


async def test_password_command_surfaces_sanitized_api_failure(command, context, caplog):
    command.wm_api.management.s3.credentials.side_effect = RuntimeError(
        "one-time-secret must not be logged"
    )

    await ManagementCommands.command_s3_passwd.callback(
        command, context
    )

    context.send.assert_awaited_once_with(
        "S3 credentials could not be issued. Contact an administrator before using Object Storage."
    )
    context.message.add_reaction.assert_not_awaited()
    context.author.send.assert_not_awaited()
    assert "one-time-secret" not in caplog.text


async def test_password_command_reacts_only_after_success(command, context):
    command.wm_api.management.s3.credentials.return_value = Credentials(
        "app", "access", "one-time-secret"
    )

    await ManagementCommands.command_s3_passwd.callback(
        command, context
    )

    context.message.add_reaction.assert_awaited_once_with("\U00002705")
    context.send.assert_not_awaited()


async def test_management_s3_client_uses_only_credentials_and_revoke_routes():
    api = S3Api("https://management.example")
    member = {
        "type": "discord",
        "discord_username": "ExampleUser",
        "discord_id": "123",
    }
    api.post = AsyncMock(side_effect=[
        SimpleNamespace(json=lambda: {
            "application_id": "app",
            "access_key": "access",
            "secret_key": "one-time-secret",
        }),
        SimpleNamespace(json=lambda: {"revoked": True}),
    ])

    credentials = await api.credentials(member)
    revoked = await api.revoke(member)

    assert credentials == Credentials("app", "access", "one-time-secret")
    assert "one-time-secret" not in repr(credentials)
    assert revoked == {"revoked": True}
    assert api.post.await_args_list[0].args == ("/s3/credentials",)
    assert api.post.await_args_list[0].kwargs == {"json": member}
    assert api.post.await_args_list[1].args == ("/s3/credential/revoke",)
    assert api.post.await_args_list[1].kwargs == {"json": member}
