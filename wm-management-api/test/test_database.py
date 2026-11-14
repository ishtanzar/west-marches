import datetime
from unittest import mock

import pytest
import pytest_asyncio
from sqlalchemy.engine import make_url
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import OperationalError
from sqlalchemy.schema import CreateTable

from services.backup import BackupService
from services.database import (BackupDocument, BackupState, Database, InvalidDatabaseConfig, InvalidQuery,
                               backups_table, build_database_url)


@pytest_asyncio.fixture
async def database():
    db = Database.from_env({'DATABASE_ENDPOINT': 'sqlite+aiosqlite://'})
    yield db
    await db.dispose()


async def seed(database):
    docs = [
        BackupDocument(datetime.datetime(2026, 1, 1, 10), 'worlds', BackupState.SUCCESS),
        BackupDocument(datetime.datetime(2026, 1, 2, 10), 'systems', BackupState.FAILED),
        BackupDocument(datetime.datetime(2026, 1, 3, 10), 'worlds', BackupState.SUCCESS),
    ]
    for doc in docs:
        await doc.insert(database)
    return docs


async def test_insert_get_delete(database):
    backup = BackupDocument(datetime.datetime(2026, 1, 1))
    await backup.insert(database)

    assert len(await BackupDocument.find(database)) == 1
    stored = await BackupDocument.get(database, backup.id)
    assert stored.asdict() == backup.asdict()
    assert stored.asdict()['state'] == 'BackupState.PENDING'
    assert isinstance(stored.asdict(True)['_id'], str)

    await BackupDocument.delete(database, backup.id)
    await BackupDocument.delete(database, backup.id)
    assert await BackupDocument.find(database) == []


async def test_serialization(database):
    backup = BackupDocument(datetime.datetime(2026, 1, 1, 10, 5, 6), state=BackupState.SUCCESS)
    await backup.insert(database)
    data = (await BackupDocument.get(database, backup.id)).asdict(serializable=True)

    assert data['state'] == 'BackupState.SUCCESS'
    assert data['date'] == '2026-01-01T10:05:06Z'
    assert data['unix'] == int(datetime.datetime(2026, 1, 1, 10, 5, 6).timestamp())
    assert set(data) == {'_id', 'date', 'unix', 'schema', 'prefix', 'archive_name', 'state'}


async def test_save_upserts(database):
    backup = BackupDocument(datetime.datetime(2026, 1, 1))
    await backup.save(database)
    backup.state = BackupState.SUCCESS
    await backup.save(database)

    found = await BackupDocument.find(database)
    assert len(found) == 1 and found[0].state == BackupState.SUCCESS


async def test_filters_sort_limit(database):
    docs = await seed(database)

    latest = await BackupDocument.find(database, {'state': 'BackupState.SUCCESS'}, [('date', -1)], 1)
    assert [d.id for d in latest] == [str(docs[2].id)]

    assert len(await BackupDocument.find(database, {'schema': 'worlds'})) == 2
    assert len(await BackupDocument.find(database, {'state': 'SUCCESS'})) == 2
    assert len(await BackupDocument.find(database, {'schema': {'$in': ['systems', 'modules']}})) == 1
    assert len(await BackupDocument.find(database, {'schema': {'$ne': 'worlds'}})) == 1
    assert len(await BackupDocument.find(database, {'date': {'$gte': '2026-01-02T00:00:00', '$lt': '2026-01-03T23:00:00'}})) == 2
    assert len(await BackupDocument.find(database, {'unix': {'$gt': int(docs[0].date.timestamp())}})) == 2
    assert [d.id for d in await BackupDocument.find(database, sort=[('date', 1)])] == [str(d.id) for d in docs]
    assert len(await BackupDocument.find(database, limit=2)) == 2


@pytest.mark.parametrize('query_filter', [
    {'unknown': 1},
    {'schema': {'$regex': '.*'}},
    {'schema': {'$where': 'x'}},
    {'state': 'bogus'},
    {'unix': 'abc'},
    {'schema': {}},
    {'schema': {'$in': []}},
    {'date': 'not a date'},
    {'date': float('inf')},
    {'date': float('nan')},
    {'unix': float('inf')},
    {'unix': 1.5},
    {'unix': 2 ** 63},
    ['schema'],
])
async def test_invalid_filters(database, query_filter):
    with pytest.raises(InvalidQuery):
        await BackupDocument.find(database, query_filter)


async def test_invalid_sort_and_limit(database):
    with pytest.raises(InvalidQuery):
        await BackupDocument.find(database, sort=[('secret', 1)])
    with pytest.raises(InvalidQuery):
        await BackupDocument.find(database, sort=[('date', 2)])
    with pytest.raises(InvalidQuery):
        await BackupDocument.find(database, limit=-1)


async def test_injection_is_parameterized(database):
    await seed(database)
    assert await BackupDocument.find(database, {'schema': "worlds' OR '1'='1"}) == []
    assert len(await BackupDocument.find(database)) == 3


def test_mysql_url_uses_separate_credentials():
    url = build_database_url('mysql+asyncmy://db.example:3306/westmarches', 'user', 'p@ss:/w?rd#')
    assert url.username == 'user' and url.password == 'p@ss:/w?rd#'
    assert (url.host, url.port, url.database) == ('db.example', 3306, 'westmarches')
    assert 'p@ss' not in repr(url) and 'p@ss' not in str(url)
    assert make_url(url.render_as_string(hide_password=False)).password == 'p@ss:/w?rd#'
    Database(url)  # engine creation must not connect


@pytest.mark.parametrize('endpoint,user,password', [
    ('', None, None),
    ('lightning:///data/westmarches.db', None, None),
    ('postgresql+asyncpg://host/db', 'u', 'p'),
    ('mysql://host/db', 'u', 'p'),
    ('mysql+asyncmy://u:p@host/db', 'u', 'p'),
    ('mysql+asyncmy://host/db', None, 'p'),
    ('mysql+asyncmy://host/db', 'u', None),
    ('mysql+asyncmy:///db', 'u', 'p'),
    ('mysql+asyncmy://host', 'u', 'p'),
    ('sqlite+aiosqlite:///x.db', 'u', 'p'),
    ('not a url', None, None),
])
def test_invalid_config(endpoint, user, password):
    with pytest.raises(InvalidDatabaseConfig):
        build_database_url(endpoint, user, password)


def test_sqlite_url():
    url = build_database_url('sqlite+aiosqlite:////opt/data/westmarches.db')
    assert url.database == '/opt/data/westmarches.db'


def test_from_env_requires_endpoint():
    with pytest.raises(InvalidDatabaseConfig):
        Database.from_env({})


async def test_lazy_connection_failure_is_not_fatal(tmp_path):
    db = Database.from_env({'DATABASE_ENDPOINT': f'sqlite+aiosqlite:///{tmp_path}/missing/dir/db.sqlite'})
    with pytest.raises(OperationalError):
        await BackupDocument.find(db)
    await db.dispose()


async def test_file_database_survives_engine_recreation(tmp_path):
    environ = {'DATABASE_ENDPOINT': f'sqlite+aiosqlite:///{tmp_path}/backups.sqlite'}
    backup = BackupDocument(datetime.datetime(2026, 1, 1))
    first = Database.from_env(environ)
    try:
        await backup.insert(first)
    finally:
        await first.dispose()
    second = Database.from_env(environ)
    try:
        assert (await BackupDocument.get(second, backup.id)).asdict() == backup.asdict()
    finally:
        await second.dispose()


def test_mysql_table_compiles():
    ddl = str(CreateTable(backups_table).compile(dialect=mysql.dialect()))
    assert 'DATETIME(6)' in ddl
    assert 'PRIMARY KEY (id)' in ddl


def test_archive_client_is_lazy():
    with mock.patch('services.backup.boto3.client') as client:
        service = BackupService('/unused', 'bucket', s3_endpoint='https://storage.example')
        client.assert_not_called()
        assert service.s3_client is client.return_value
        client.assert_called_once_with('s3', endpoint_url='https://storage.example')


async def test_routes(database, app, client):
    await seed(database)
    service = BackupService('/unused', 'bucket', database=database)

    with mock.patch.object(app, '_backup', service):
        await _check_routes(client)


async def _check_routes(client):
    listing = await (await client.get('/backup/list')).get_json()
    assert [b['schema'] for b in listing['backups']] == ['worlds', 'systems', 'worlds']
    assert listing['backups'][0]['state'] == 'BackupState.SUCCESS'

    latest = await (await client.open('/backup?latest', method='SEARCH')).get_json()
    assert len(latest['backups']) == 1
    assert latest['backups'][0]['date'] == '2026-01-03T10:00:00Z'

    found = await (await client.open('/backup?sort_date=-1&limit=2', method='SEARCH',
                                     json={'schema': 'worlds'})).get_json()
    assert [b['date'] for b in found['backups']] == ['2026-01-03T10:00:00Z', '2026-01-01T10:00:00Z']

    response = await client.open('/backup', method='SEARCH', json={'$where': 'x'})
    assert response.status_code == 400
    for invalid_filter in ([], False, ''):
        response = await client.open('/backup', method='SEARCH', json=invalid_filter)
        assert response.status_code == 400
    response = await client.open('/backup?limit=abc', method='SEARCH')
    assert response.status_code == 400

    victim = listing['backups'][0]['_id']
    assert (await client.delete(f'/backup/{victim}')).status_code == 204
    assert (await client.delete(f'/backup/{victim}')).status_code == 204
    assert len((await (await client.get('/backup/list')).get_json())['backups']) == 2
