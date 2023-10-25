from pathlib import Path
from unittest import mock

import os
import pytest
from unittest.mock import Mock, AsyncMock
from montydb import MontyClient

from api import WestMarchesApi
from services.database import Engine

resources = Path(__file__).parent / 'resources'

@pytest.fixture(autouse=True)
def mock_basic_auth(request):
    if 'disable_auth_mock' in request.keywords:
        yield
    else:
        with mock.patch('passlib.apache.HtpasswdFile.check_password') as check_password, \
            mock.patch('werkzeug.sansio.request.Request.authorization') as authorization:

            check_password.return_value = True
            authorization.username.return_value = 'my_user'

            yield


@pytest.fixture(scope='session')
def app():
    with mock.patch.dict(os.environ, {'HTPASSWD_PATH': '/dev/null'}):
        app = WestMarchesApi(
            __name__,
            Mock(),
            Mock(),
            Mock(),
            Mock()
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
