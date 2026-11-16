import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import NoReturn
from uuid import UUID

from scaleway import Client
from scaleway.iam.v1alpha1 import IamV1Alpha1API
from werkzeug.exceptions import BadRequest, Conflict, ServiceUnavailable


class ScalewayError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)

    def to_http_error(self) -> NoReturn:
        if self.code in {"invalid_discord_id", "invalid_discord_username"}:
            raise BadRequest(self.code) from None
        if self.code in {"application_not_owned", "group_not_owned",
                         "ambiguous_application"}:
            raise Conflict(self.code) from None
        raise ServiceUnavailable(self.code) from None


_SAFE_TAG_CHARACTER = re.compile(r"[^a-zA-Z0-9._\-/=+@ ]")


class _CredentialLogFilter(logging.Filter):
    def filter(self, record):
        record.msg = re.sub(
            r'("(?:secret_key|access_key)"\s*:\s*)"(?:\\.|[^"\\])*"',
            r'\1"[REDACTED]"',
            record.getMessage(),
        )
        record.args = ()
        return True


_credential_log_filter = _CredentialLogFilter()
_logger = logging.getLogger(__name__)
_logger.addFilter(_credential_log_filter)


def api_key_ttl_seconds(value):
    if (isinstance(value, bool) or not isinstance(value, (str, int))
            or not re.fullmatch(r"[0-9]+", str(value)) or int(value) <= 0):
        raise ValueError("S3_EDITORS_KEY_TTL must be a positive integer")
    try:
        timedelta(seconds=int(value))
    except OverflowError:
        raise ValueError("S3_EDITORS_KEY_TTL is too large") from None
    return int(value)


def _discord_id(value):
    raw = str(value)
    if isinstance(value, bool) or len(raw) > 20 or not raw.isdigit():
        raise ScalewayError("invalid_discord_id")
    identifier = str(int(raw))
    if not 0 < int(identifier) < 2**64:
        raise ScalewayError("invalid_discord_id")
    return identifier


def _username(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ScalewayError("invalid_discord_username")
    return value


def _tag_username(value):
    return _SAFE_TAG_CHARACTER.sub("_", value)[:80] or "user"


def sdk_call(method):
    @wraps(method)
    async def call(*args, **kwargs):
        task = asyncio.create_task(asyncio.to_thread(method, *args, **kwargs))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            try:
                await task
            finally:
                raise asyncio.CancelledError from None
        except ScalewayError:
            raise
        except Exception as error:
            _logger.warning("Scaleway IAM call %s failed: %s: %s",
                            method.__name__, type(error).__name__, error)
            raise ScalewayError("iam_unavailable") from None
    return call


@dataclass(frozen=True)
class Credentials:
    application_id: str
    access_key: str
    secret_key: str = field(repr=False)


class ScalewayService:
    managed_tag = "managed-by=westmarches-discord-bot"

    def __init__(self, config):
        self.ttl_seconds = api_key_ttl_seconds(config.get("ttl_seconds", 14400))
        self.application_prefix = config.get("application_prefix", "westmarches")
        if (not isinstance(self.application_prefix, str)
                or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", self.application_prefix)):
            raise ValueError("S3_EDITORS_APP_PREFIX must be 1-63 lowercase letters, digits or hyphens, starting with a letter or digit")
        log_level = config.get("log_level", "WARNING")
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("SCW_LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL")
        for name in ("scaleway", "scaleway_core"):
            logger = logging.getLogger(name)
            logger.addFilter(_credential_log_filter)
            logger.setLevel(log_level)
        try:
            self.organization_id = str(UUID(config["organization_id"]))
            self.project_id = str(UUID(config["project_id"]))
            self.group_id = str(UUID(config["group_id"]))
            self.api = IamV1Alpha1API(Client(
                access_key=config["access_key"], secret_key=config["secret_key"],
                default_organization_id=self.organization_id,
                default_project_id=self.project_id,
            ))
        except (KeyError, ValueError, TypeError, AttributeError):
            raise ScalewayError("invalid_iam_configuration") from None
        self._lock = asyncio.Lock()

    async def credentials(self, discord_id, discord_username):
        async with self._lock:
            return await self._credentials(
                _discord_id(discord_id), _username(discord_username)
            )

    async def revoke(self, discord_id, discord_username):
        async with self._lock:
            return await self._revoke(
                _discord_id(discord_id), _username(discord_username)
            )

    @sdk_call
    def _credentials(self, discord_id, discord_username):
        application = self._application(discord_id, discord_username, create=True)
        self._group_member(application.id, add=True)

        # Previous keys are left to expire: IAM conditions cannot scope API-key
        # deletion to GM applications, so the manager is not granted that right.
        key = self.api.create_api_key(
            application_id=application.id,
            default_project_id=self.project_id,
            description=f"westmarches-discord:{discord_id}",
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds),
        )

        if key.application_id != application.id or not key.access_key or not key.secret_key:
            raise ScalewayError("credential_creation_failed")

        return Credentials(application.id, key.access_key, key.secret_key)

    @sdk_call
    def _revoke(self, discord_id, discord_username):
        application = self._application(discord_id, discord_username, create=False)
        if application is None:
            return {"revoked": True}

        # Keys only grant S3 access through the editors group membership.
        self._group_member(application.id, add=False)
        return {"revoked": True}

    def _application(self, discord_id, discord_username, create):
        name = f"{self.application_prefix}-gm-{discord_id}"
        identity_tag = f"discord-id={discord_id}"
        matches = [application for application in self.api.list_applications_all(
            organization_id=self.organization_id, name=name
        ) if application.name == name]
        if len(matches) > 1:
            raise ScalewayError("ambiguous_application")
        if not matches:
            if not create:
                return None
            try:
                application = self.api.create_application(
                    organization_id=self.organization_id,
                    name=name,
                    description=f"West Marches Discord application for {discord_username}"[:200],
                    tags=sorted((
                        self.managed_tag,
                        identity_tag,
                        f"discord-username={_tag_username(discord_username)}",
                    )),
                )
            except Exception:
                raise ScalewayError("iam_unavailable") from None
        else:
            application = matches[0]

        tags = set(application.tags or [])
        if (application.organization_id != self.organization_id
                or application.name != name
                or self.managed_tag not in tags
                or identity_tag not in tags):
            raise ScalewayError("application_not_owned")
        return application

    def _group_member(self, application_id, add):
        group = self.api.get_group(group_id=self.group_id)
        if group.organization_id != self.organization_id:
            raise ScalewayError("group_not_owned")
        members = set(group.application_ids or [])
        if add and application_id not in members:
            self.api.add_group_member(group_id=self.group_id, application_id=application_id)
        elif not add and application_id in members:
            self.api.remove_group_member(group_id=self.group_id, application_id=application_id)
