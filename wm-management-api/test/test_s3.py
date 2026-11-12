import asyncio
import logging
import threading
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from services.discord import DiscordError
from services.scaleway import ScalewayError
from services.scaleway import Credentials, ScalewayService


ORG = "00000000-0000-0000-0000-000000000001"
PROJECT = "00000000-0000-0000-0000-000000000002"
GROUP = "00000000-0000-0000-0000-000000000003"


@pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
def test_sdk_log_level_and_secret_redaction(monkeypatch, caplog, level):
    from requests import Response
    from scaleway_core.api import APILogger

    monkeypatch.setattr("services.scaleway.Client", Mock())
    monkeypatch.setattr("services.scaleway.IamV1Alpha1API", Mock())
    logger = logging.getLogger("scaleway")
    previous_level = logger.level
    previous_core_level = logging.getLogger("scaleway_core").level
    try:
        ScalewayService({
            "organization_id": ORG, "project_id": PROJECT, "group_id": GROUP,
            "access_key": "access", "secret_key": "secret", "log_level": level,
        })
        assert logger.level == getattr(logging, level)
        response = Response()
        response.status_code = 403
        response._content = (
            b'{"secret_key": "one-time-secret", "access_key":"access-value",'
            b'"message":"permission denied", "nested":{"secret_key":"another-secret"}}'
        )
        with caplog.at_level(logging.DEBUG):
            APILogger(logger, 1).log_response(response)
        if level == "DEBUG":
            assert "permission denied" in caplog.text
            assert "HTTP 403" in caplog.text
            assert "[REDACTED]" in caplog.text
        else:
            assert "permission denied" not in caplog.text
        assert "one-time-secret" not in caplog.text
        assert "another-secret" not in caplog.text
        assert "access-value" not in caplog.text
    finally:
        logger.setLevel(previous_level)
        logging.getLogger("scaleway_core").setLevel(previous_core_level)


@pytest.mark.parametrize("level", ["", "debug", "INVALID", None])
def test_invalid_sdk_log_level_fails_before_sdk_initialization(monkeypatch, level):
    client = Mock()
    monkeypatch.setattr("services.scaleway.Client", client)
    with pytest.raises(ValueError, match="SCW_LOG_LEVEL"):
        ScalewayService({"log_level": level})
    client.assert_not_called()


class FakeIAM:
    def __init__(self):
        self.applications = []
        self.keys = []
        self.group_members = []
        self.deleted = []
        self.events = []

    def list_applications_all(self, **kwargs):
        assert kwargs["organization_id"] == ORG
        assert set(kwargs) == {"organization_id", "name"}
        return [app for app in self.applications if app.name == kwargs["name"]]

    def create_application(self, **kwargs):
        application = SimpleNamespace(
            id="application-1",
            name=kwargs["name"],
            organization_id=kwargs["organization_id"],
            tags=kwargs["tags"],
            description=kwargs["description"],
        )
        self.applications.append(application)
        return application

    def get_group(self, **kwargs):
        assert kwargs["group_id"] == GROUP
        return SimpleNamespace(
            organization_id=ORG,
            application_ids=list(self.group_members),
        )

    def add_group_member(self, **kwargs):
        self.events.append("add_member")
        self.group_members.append(kwargs["application_id"])

    def remove_group_member(self, **kwargs):
        self.events.append("remove_member")
        self.group_members.remove(kwargs["application_id"])

    def list_api_keys_all(self, **kwargs):
        assert kwargs["organization_id"] == ORG
        return list(self.keys)

    def create_api_key(self, **kwargs):
        self.events.append("create_key")
        key = SimpleNamespace(
            application_id=kwargs["application_id"],
            access_key="new-access",
            secret_key="one-time-secret",
            expires_at=kwargs["expires_at"],
        )
        self.keys.append(key)
        return key

    def delete_api_key(self, **kwargs):
        self.events.append("delete_key")
        key = next(key for key in self.keys if key.access_key == kwargs["access_key"])
        self.deleted.append(key.access_key)
        self.keys.remove(key)


def service(ttl_seconds=14400, application_prefix="westmarches"):
    instance = object.__new__(ScalewayService)
    instance.organization_id = ORG
    instance.project_id = PROJECT
    instance.group_id = GROUP
    instance.ttl_seconds = ttl_seconds
    instance.application_prefix = application_prefix
    instance.api = FakeIAM()
    instance._lock = asyncio.Lock()
    return instance


@pytest.fixture(autouse=True)
def reset_route_mocks(app):
    app.discord.member.reset_mock()
    app.scaleway.credentials.reset_mock()
    app.scaleway.revoke.reset_mock()


async def test_credentials_replace_all_keys_and_create_owned_application():
    iam = service()
    iam.api.keys.extend([
        SimpleNamespace(application_id="application-1", access_key="old-1"),
        SimpleNamespace(application_id="application-1", access_key="old-2"),
    ])

    result = await iam.credentials("123", "Nöë")

    assert result == Credentials("application-1", "new-access", "one-time-secret")
    assert "one-time-secret" not in repr(result)
    assert iam.api.deleted == ["old-1", "old-2"]
    assert [key.access_key for key in iam.api.keys] == ["new-access"]
    assert iam.api.events == ["add_member", "delete_key", "delete_key", "create_key"]
    application = iam.api.applications[0]
    assert application.name == "westmarches-gm-123"
    assert set(application.tags) == {
        iam.managed_tag, "discord-id=123", "discord-username=N__",
    }
    assert application.organization_id == ORG


async def test_credentials_reject_unowned_application_without_mutation():
    iam = service()
    iam.api.applications.append(SimpleNamespace(
        id="foreign",
        name="westmarches-gm-123",
        organization_id=ORG,
        tags=[],
    ))

    with pytest.raises(ScalewayError, match="application_not_owned"):
        await iam.credentials("123", "name")

    assert iam.api.events == []


async def test_credentials_reject_ambiguous_applications():
    iam = service()
    application = SimpleNamespace(
        id="app", name="westmarches-gm-123",
        organization_id=ORG,
        tags=[
            iam.managed_tag,
            "discord-id=999",
        ],
    )
    iam.api.applications.extend([application, application])

    with pytest.raises(ScalewayError, match="ambiguous_application"):
        await iam.credentials("123", "name")

    assert iam.api.events == []


@pytest.mark.parametrize("organization,tags", [
    (PROJECT, [ScalewayService.managed_tag, "discord-id=123"]),
    (ORG, [ScalewayService.managed_tag, "discord-id=999"]),
    (ORG, ["discord-id=123"]),
])
async def test_credentials_reject_wrong_ownership(organization, tags):
    iam = service()
    iam.api.applications.append(SimpleNamespace(
        id="existing",
        name="westmarches-gm-123",
        organization_id=organization,
        tags=tags,
    ))

    with pytest.raises(ScalewayError, match="application_not_owned"):
        await iam.credentials("123", "name")

    assert iam.api.events == []


async def test_revoke_is_idempotent_when_application_is_absent():
    iam = service()

    assert await iam.revoke("123", "former name") == {"revoked": True}
    assert iam.api.applications == []
    assert iam.api.events == []


async def test_revoke_removes_group_member_and_every_application_key():
    iam = service()
    application = iam.api.create_application(
        organization_id=ORG,
        name="westmarches-gm-123",
        description="",
        tags=[
            iam.managed_tag,
            "discord-id=123",
        ],
    )
    iam.api.group_members.append(application.id)
    iam.api.keys.extend([
        SimpleNamespace(application_id=application.id, access_key="old-1"),
        SimpleNamespace(application_id=application.id, access_key="old-2"),
    ])

    assert await iam.revoke("123", "former name") == {"revoked": True}
    assert iam.api.group_members == []
    assert iam.api.deleted == ["old-1", "old-2"]
    assert iam.api.events == ["remove_member", "delete_key", "delete_key"]


@pytest.mark.parametrize("identifier", ["", "abc", "0", "-123", True, str(2**64)])
async def test_invalid_discord_id_is_rejected(identifier):
    with pytest.raises(ScalewayError, match="invalid_discord_id"):
        await service().credentials(identifier, "name")


@pytest.mark.parametrize("ttl_seconds", [14400, 60])
async def test_api_key_expiry_is_exact_aware_utc(monkeypatch, ttl_seconds):
    now = datetime(2026, 11, 9, 10, 25, 13, 123456, tzinfo=timezone.utc)
    clock = Mock()
    clock.now.return_value = now
    monkeypatch.setattr("services.scaleway.datetime", clock)
    iam = service(ttl_seconds)

    await iam.credentials("123", "name")

    clock.now.assert_called_once_with(timezone.utc)
    expiry = iam.api.keys[0].expires_at
    assert expiry == now + timedelta(seconds=ttl_seconds)
    assert expiry.tzinfo is timezone.utc
    assert (expiry - now).total_seconds() == ttl_seconds


@pytest.mark.parametrize("ttl,expected", [(None, 14400), ("60", 60), (120, 120)])
def test_service_configures_ttl_at_startup(monkeypatch, ttl, expected):
    monkeypatch.setattr("services.scaleway.Client", Mock())
    monkeypatch.setattr("services.scaleway.IamV1Alpha1API", Mock())
    config = {
        "organization_id": ORG, "project_id": PROJECT, "group_id": GROUP,
        "access_key": "access", "secret_key": "secret",
    }
    if ttl is not None:
        config["ttl_seconds"] = ttl
    assert ScalewayService(config).ttl_seconds == expected


@pytest.mark.parametrize("ttl", [
    "", "abc", "1.5", "0", "-1", 0, -1, True, False, 1.5, None, " 60", "9" * 100,
])
def test_invalid_ttl_fails_explicitly_before_sdk_initialization(monkeypatch, ttl):
    client = Mock()
    monkeypatch.setattr("services.scaleway.Client", client)
    with pytest.raises(ValueError, match="S3_EDITORS_KEY_TTL"):
        ScalewayService({"ttl_seconds": ttl})
    client.assert_not_called()


async def test_username_change_reuses_deterministic_application():
    iam = service()
    await iam.credentials("123", "old name")
    await iam.credentials("123", "new name")
    assert len(iam.api.applications) == 1
    assert iam.api.applications[0].name == "westmarches-gm-123"
    assert len(iam.api.keys) == 1


async def test_test_prefix_isolates_issuance_and_revocation_from_production():
    iam = service(application_prefix="wm-test")
    production = SimpleNamespace(
        id="production-app", name="westmarches-gm-123",
        organization_id=ORG,
        tags=[iam.managed_tag, "discord-id=123"],
    )
    production_key = SimpleNamespace(
        application_id=production.id, access_key="production-key",
    )
    iam.api.applications.append(production)
    iam.api.keys.append(production_key)

    def list_api_keys_all(**kwargs):
        assert kwargs["organization_id"] == ORG
        assert kwargs["application_id"] != production.id
        return [
            key for key in iam.api.keys
            if key.application_id == kwargs["application_id"]
        ]

    iam.api.list_api_keys_all = list_api_keys_all

    assert await iam.revoke("123", "Alice") == {"revoked": True}
    assert iam.api.keys == [production_key]
    assert iam.api.events == []

    await iam.credentials("123", "Alice")
    assert iam.api.applications[1].name == "wm-test-gm-123"
    assert production_key in iam.api.keys
    await iam.credentials("123", "Alice")
    assert len(iam.api.applications) == 2
    await iam.revoke("123", "Alice")
    assert iam.api.keys == [production_key]
    assert "production-key" not in iam.api.deleted


@pytest.mark.parametrize("prefix", [None, "", "WM-test", "test app", "-test", "x" * 64, 123])
def test_invalid_application_prefix_fails_before_sdk_initialization(monkeypatch, prefix):
    client = Mock()
    monkeypatch.setattr("services.scaleway.Client", client)
    with pytest.raises(ValueError, match="S3_EDITORS_APP_PREFIX"):
        ScalewayService({"application_prefix": prefix})
    client.assert_not_called()


@pytest.mark.parametrize("prefix", ["westmarches", "wm-test"])
def test_service_configures_application_prefix(monkeypatch, prefix):
    monkeypatch.setattr("services.scaleway.Client", Mock())
    monkeypatch.setattr("services.scaleway.IamV1Alpha1API", Mock())
    config = {
        "organization_id": ORG, "project_id": PROJECT, "group_id": GROUP,
        "access_key": "access", "secret_key": "secret",
    }
    assert ScalewayService(config).application_prefix == "westmarches"
    config["application_prefix"] = prefix
    assert ScalewayService(config).application_prefix == prefix


async def test_cancellation_keeps_sdk_operation_serialized_until_thread_finishes():
    iam = service()
    started = threading.Event()
    release = threading.Event()
    list_applications = iam.api.list_applications_all

    def blocked_list(**kwargs):
        started.set()
        release.wait(timeout=2)
        return list_applications(**kwargs)

    iam.api.list_applications_all = blocked_list
    credentials = asyncio.create_task(iam.credentials("123", "name"))
    assert await asyncio.to_thread(started.wait, 1)
    credentials.cancel()
    revoke = asyncio.create_task(iam.revoke("123", "name"))
    await asyncio.sleep(0)
    assert not revoke.done()
    release.set()

    with pytest.raises(asyncio.CancelledError):
        await credentials
    assert await revoke == {"revoked": True}
    assert len(iam.api.keys) == 0


@pytest.mark.parametrize("service,error,status", [
    ("discord", DiscordError("not_current_gm"), 403),
    ("discord", DiscordError("discord_unavailable"), 503),
    ("scaleway", ScalewayError("application_not_owned"), 409),
    ("scaleway", ScalewayError("iam_unavailable"), 503),
])
async def test_routes_translate_service_errors(app, service, error, status):
    app.discord.member = AsyncMock(return_value="Alice")
    app.scaleway.credentials = AsyncMock()
    if service == "discord":
        app.discord.member.side_effect = error
    else:
        app.scaleway.credentials.side_effect = error
    response = await app.test_client().post("/s3/credentials", json={
        "type": "discord", "discord_username": "Alice", "discord_id": "123",
    })
    assert response.status_code == status
    assert response.mimetype == "text/html"
    assert response.headers["Cache-Control"] == "no-store"
    assert not hasattr(error, "status")


async def test_routes_verify_member_name_and_return_secret_without_cache(app):
    app.discord.member = AsyncMock(return_value="Alice")
    app.scaleway.credentials = AsyncMock(
        return_value=Credentials("app-id", "access", "secret"))
    client = app.test_client()

    response = await client.post("/s3/credentials", json={
        "type": "discord",
        "discord_username": "Alice",
        "discord_id": "123",
    })

    assert response.status_code == 200
    assert await response.get_json() == {
        "application_id": "app-id", "access_key": "access", "secret_key": "secret"
    }
    assert response.headers["Cache-Control"] == "no-store"
    app.discord.member.assert_awaited_once_with("123")
    app.scaleway.credentials.assert_awaited_once_with("123", "Alice")


async def test_routes_reject_username_mismatch_before_credentials(app):
    app.discord.member = AsyncMock(return_value="CurrentName")
    response = await app.test_client().post("/s3/credentials", json={
        "type": "discord",
        "discord_username": "StaleName",
        "discord_id": "123",
    })

    assert response.status_code == 403
    assert response.mimetype == "text/html"
    app.scaleway.credentials.assert_not_awaited()


async def test_revoke_forwards_same_member_without_requiring_current_membership(app):
    app.scaleway.revoke = AsyncMock(return_value={"revoked": True})
    member = {
        "type": "discord",
        "discord_username": "FormerName",
        "discord_id": "123",
    }
    response = await app.test_client().post("/s3/credential/revoke", json=member)

    assert response.status_code == 200
    assert await response.get_json() == {"revoked": True}
    app.scaleway.revoke.assert_awaited_once_with("123", "FormerName")
    app.discord.member.assert_not_awaited()


@pytest.mark.parametrize("path", ["/s3/credentials", "/s3/credential/revoke"])
@pytest.mark.parametrize("invalid_field", [
    {"invocation_message_id": "456"}, {"unexpected": "value"},
])
async def test_routes_reject_extra_member_fields(app, path, invalid_field):
    member = {
        "type": "discord",
        "discord_username": "Alice",
        "discord_id": "123",
        **invalid_field,
    }
    response = await app.test_client().post(path, json=member)

    assert response.status_code == 400
    assert response.mimetype == "text/html"
    app.scaleway.credentials.assert_not_awaited()
    app.scaleway.revoke.assert_not_awaited()


@pytest.mark.parametrize("path", ["/s3/credentials", "/s3/credential/revoke"])
@pytest.mark.parametrize("member", [
    None, [], {},
    {"type": "discord", "discord_username": "Alice"},
    {"type": "other", "discord_username": "Alice", "discord_id": "123"},
    {"type": "discord", "discord_username": "", "discord_id": "123"},
    {"type": "discord", "discord_username": 123, "discord_id": "123"},
    {"type": "discord", "discord_username": "Alice", "discord_id": "invalid"},
])
async def test_routes_reject_invalid_member_fields(app, path, member):
    response = await app.test_client().post(path, json=member)
    assert response.status_code == 400
    app.scaleway.credentials.assert_not_awaited()
    app.scaleway.revoke.assert_not_awaited()
    app.discord.member.assert_not_awaited()
