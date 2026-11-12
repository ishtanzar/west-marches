import base64
from unittest.mock import AsyncMock

import pytest

from api import BasicAuth, WestMarchesApi


pytestmark = pytest.mark.disable_auth_mock


def basic(username="foundry_manager", password="testpassword"):
    credentials = f"{username}:{password}".encode("utf-8")
    return "Basic " + base64.b64encode(credentials).decode("ascii")


PROTECTED_ENDPOINTS = [
    ("/", "GET"),
    ("/foundry/restart", "POST"),
    ("/foundry/users", "SEARCH"),
    ("/foundry/users", "POST"),
    ("/foundry/users/user-id", "PUT"),
    ("/backup/list", "GET"),
    ("/backup", "SEARCH"),
    ("/backup/backup-id", "DELETE"),
    ("/backup/perform", "POST"),
    ("/backup/restore/backup-id", "POST"),
    ("/s3/credentials", "POST"),
    ("/s3/credential/revoke", "POST"),
]


@pytest.mark.parametrize("path,method", PROTECTED_ENDPOINTS)
@pytest.mark.parametrize("authorization", [
    None,
    "Bearer testpassword",
    "Digest " + basic().split(" ", 1)[1],
    "Basic not-base64",
    "Basic " + base64.b64encode(b"foundry_manager").decode("ascii"),
    basic(username="other"),
    basic(username="öther"),
    basic(password="wrong"),
    basic(password=""),
])
async def test_protected_endpoints_reject_invalid_auth(app, path, method, authorization):
    headers = {} if authorization is None else {"Authorization": authorization}
    response = await app.test_client().open(path, method=method, headers=headers)
    assert response.status_code == 401
    if path.startswith("/s3/"):
        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["Pragma"] == "no-cache"


async def test_valid_auth_injects_fixed_user(app):
    response = await app.test_client().get("/", headers={"Authorization": basic()})
    assert response.status_code == 200
    assert await response.get_data(as_text=True) == "Hello, foundry_manager!"
    assert callable(app.auth.required)
    assert not hasattr(app.auth, "authenticated")
    assert not hasattr(app.auth, "users")


@pytest.mark.parametrize("password,expected", [
    ("sëcret-密碼-🔑", 200),
    ("sëcret-密碼-🔒", 401),
])
async def test_unicode_password(app, monkeypatch, password, expected):
    monkeypatch.setattr(app.auth, "_password", BasicAuth("sëcret-密碼-🔑")._password)
    response = await app.test_client().get(
        "/", headers={"Authorization": basic(password=password)})
    assert response.status_code == expected
    if expected == 200:
        assert await response.get_data(as_text=True) == "Hello, foundry_manager!"


@pytest.mark.parametrize("password", [None, ""])
def test_missing_or_empty_secret_fails_startup(app, monkeypatch, password):
    if password is None:
        monkeypatch.delenv("MGMNT_API_SECRET", raising=False)
    else:
        monkeypatch.setenv("MGMNT_API_SECRET", password)
    monkeypatch.setattr(WestMarchesApi, "instance", app)
    monkeypatch.setattr(WestMarchesApi, "log", app.log)
    with pytest.raises(ValueError, match="MGMNT_API_SECRET must be set and non-empty"):
        BasicAuth(password)


async def test_auth_failure_logs_no_credentials(app, caplog):
    username = "attacker\nFORGED LOG"
    password = "DO-NOT-LOG"
    response = await app.test_client().get(
        "/", headers={"Authorization": basic(username, password)})
    assert response.status_code == 401
    assert "Invalid authentication" in caplog.text
    assert "attacker" not in caplog.text
    assert "FORGED LOG" not in caplog.text
    assert password not in caplog.text
