from pathlib import Path
from unittest import mock

import os
import pytest
from unittest.mock import Mock, AsyncMock
from montydb import MontyClient

from api import BasicAuth, WestMarchesApi
from services.database import Engine

resources = Path(__file__).parent / 'resources'

@pytest.fixture(autouse=True)
def mock_basic_auth(request):
    if 'disable_auth_mock' in request.keywords:
        yield
    else:
        with mock.patch('api.BasicAuth.authenticate', return_value=(True, 'foundry_manager')):
            yield


@pytest.fixture(scope='session')
def app():
    from services.discord import DiscordService

    with mock.patch.dict(os.environ, {'MGMNT_API_SECRET': 'testpassword'}):
        discord = AsyncMock()
        discord.validate_member = DiscordService.validate_member
        app = WestMarchesApi(
            import_name=__name__,
            auth=BasicAuth("testpassword"),
            compose=Mock(),
            backup=Mock(),
            foundry=Mock(),
            kanka=Mock(),
            discord=discord,
            scaleway=AsyncMock()
        )

        yield app

@pytest.fixture(scope='session')
def client(app):
    yield app.test_client()

@pytest.fixture(scope='session')
def runner(app):
    yield app.test_cli_runner()

@pytest.fixture(scope='session')
def monty():
    monty = MontyClient(':memory:')
    Engine._client = monty

    yield monty
