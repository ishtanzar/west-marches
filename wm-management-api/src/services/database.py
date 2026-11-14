import asyncio
import datetime
import math
import uuid
from enum import Enum
from typing import Any, List, Mapping, Optional, Self, Sequence, Tuple

from sqlalchemy import BigInteger, Column, DateTime, Index, MetaData, String, Table, delete, select
from sqlalchemy.dialects import mysql, sqlite
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import StaticPool

ALLOWED_DRIVERS = ('mysql+asyncmy', 'sqlite+aiosqlite')


class InvalidDatabaseConfig(ValueError):
    pass


class InvalidQuery(ValueError):
    pass


class BackupState(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    FAILED = 'failed'
    SUCCESS = 'success'


def build_database_url(endpoint: str, username: Optional[str] = None, password: Optional[str] = None) -> URL:
    """Build the SQLAlchemy URL; credentials never travel inside the endpoint string."""
    if not endpoint:
        raise InvalidDatabaseConfig('DATABASE_ENDPOINT is required')
    try:
        url = make_url(endpoint)
    except (ArgumentError, ValueError) as ex:
        raise InvalidDatabaseConfig('DATABASE_ENDPOINT is not a valid database URL') from ex

    driver = url.drivername
    if driver not in ALLOWED_DRIVERS:
        raise InvalidDatabaseConfig(f'DATABASE_ENDPOINT driver must be one of {", ".join(ALLOWED_DRIVERS)}')
    if url.username or url.password:
        raise InvalidDatabaseConfig(
            'DATABASE_ENDPOINT must not embed credentials; use DATABASE_USERNAME and DATABASE_PASSWORD')

    if driver == 'sqlite+aiosqlite':
        if username or password:
            raise InvalidDatabaseConfig('SQLite does not accept DATABASE_USERNAME / DATABASE_PASSWORD')
        if url.host or url.port:
            raise InvalidDatabaseConfig('SQLite endpoint must not define a host')
        return url

    if not url.host:
        raise InvalidDatabaseConfig('MySQL endpoint requires a host')
    if not url.database:
        raise InvalidDatabaseConfig('MySQL endpoint requires a database name')
    if not username or not password:
        raise InvalidDatabaseConfig('MySQL requires DATABASE_USERNAME and DATABASE_PASSWORD')
    return URL.create(
        drivername=driver, username=username, password=password,
        host=url.host, port=url.port, database=url.database, query=url.query)


metadata = MetaData()

backups_table = Table(
    'backups', metadata,
    Column('id', String(36), primary_key=True),
    Column('date', DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    Column('unix', BigInteger, nullable=False),
    Column('schema', String(32), nullable=False),
    Column('prefix', String(255), nullable=False, default=''),
    Column('archive_name', String(255), nullable=False),
    Column('state', String(64), nullable=False),
    Index('ix_backups_date', 'date'),
    Index('ix_backups_state', 'state'),
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4',
)


class Database:
    """Lazy async SQLAlchemy engine: no connection (nor schema creation) happens before first use."""

    def __init__(self, url: URL) -> None:
        self.url = url
        options: dict = {'pool_pre_ping': True}
        if url.drivername.startswith('sqlite') and url.database in (None, '', ':memory:'):
            options.update(poolclass=StaticPool, connect_args={'check_same_thread': False})
        elif url.drivername == 'mysql+asyncmy':
            options.update(pool_size=2, max_overflow=0, pool_timeout=10,
                           connect_args={'connect_timeout': 10})
        self.engine: AsyncEngine = create_async_engine(url, **options)
        self._ready = False
        self._lock = asyncio.Lock()

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> Self:
        return cls(build_database_url(
            environ.get('DATABASE_ENDPOINT', ''),
            environ.get('DATABASE_USERNAME') or None,
            environ.get('DATABASE_PASSWORD') or None))

    async def ensure_schema(self):
        if self._ready:
            return
        async with self._lock:
            if not self._ready:
                async with self.engine.begin() as conn:
                    await conn.run_sync(metadata.create_all)
                self._ready = True

    def begin(self):
        return self.engine.begin()

    async def dispose(self):
        await self.engine.dispose()


def _local_naive(value: datetime.datetime) -> datetime.datetime:
    if value.tzinfo is not None:
        return value.astimezone().replace(tzinfo=None)
    return value


def _parse_state(value: Any) -> str:
    if isinstance(value, BackupState):
        return str(value)
    if isinstance(value, str):
        for state in BackupState:
            if value in (str(state), state.name, state.value):
                return str(state)
    raise InvalidQuery(f'Invalid backup state: {value!r}')


def _parse_date(value: Any) -> datetime.datetime:
    if isinstance(value, datetime.datetime):
        return _local_naive(value)
    if isinstance(value, bool):
        raise InvalidQuery('Invalid date value')
    if isinstance(value, (int, float)):
        try:
            return datetime.datetime.fromtimestamp(value)
        except (ValueError, OverflowError, OSError) as ex:
            raise InvalidQuery('Invalid date value') from ex
    if isinstance(value, str):
        try:
            return _local_naive(datetime.datetime.fromisoformat(value))
        except ValueError as ex:
            raise InvalidQuery(f'Invalid date value: {value!r}') from ex
    raise InvalidQuery('Invalid date value')


def _parse_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidQuery(f'Invalid integer value: {value!r}')
    if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
        raise InvalidQuery(f'Invalid integer value: {value!r}')
    if not -(2 ** 63) <= value < 2 ** 63:
        raise InvalidQuery('Integer value is outside the database range')
    return int(value)


def _parse_str(value: Any) -> str:
    if not isinstance(value, str):
        raise InvalidQuery(f'Invalid string value: {value!r}')
    return value


# Public field -> (column, value parser)
_FIELDS = {
    '_id': ('id', _parse_str),
    'id': ('id', _parse_str),
    'date': ('date', _parse_date),
    'unix': ('unix', _parse_int),
    'schema': ('schema', _parse_str),
    'prefix': ('prefix', _parse_str),
    'archive_name': ('archive_name', _parse_str),
    'state': ('state', _parse_state),
}

_OPERATORS = {
    '$eq': lambda c, v: c == v,
    '$ne': lambda c, v: c != v,
    '$gt': lambda c, v: c > v,
    '$gte': lambda c, v: c >= v,
    '$lt': lambda c, v: c < v,
    '$lte': lambda c, v: c <= v,
}


def build_conditions(query_filter: Optional[Mapping[str, Any]]) -> list:
    """Translate the supported subset of the historical filter format; anything else is rejected."""
    if query_filter is None:
        return []
    if not isinstance(query_filter, Mapping):
        raise InvalidQuery('Filter must be an object')

    conditions = []
    for field, expected in query_filter.items():
        if field not in _FIELDS:
            raise InvalidQuery(f'Unsupported filter field: {field}')
        column_name, parser = _FIELDS[field]
        column = backups_table.c[column_name]

        if isinstance(expected, Mapping):
            if not expected:
                raise InvalidQuery(f'Empty operator object for field: {field}')
            for operator, operand in expected.items():
                if operator == '$in':
                    if not isinstance(operand, (list, tuple)) or not operand:
                        raise InvalidQuery('$in requires a non-empty list')
                    conditions.append(column.in_([parser(v) for v in operand]))
                elif operator in _OPERATORS:
                    conditions.append(_OPERATORS[operator](column, parser(operand)))
                else:
                    raise InvalidQuery(f'Unsupported filter operator: {operator}')
        else:
            conditions.append(column == parser(expected))
    return conditions


def build_ordering(sort: Optional[Sequence[Tuple[str, int]]]) -> list:
    ordering = []
    for item in sort or []:
        try:
            field, direction = item
        except (TypeError, ValueError) as ex:
            raise InvalidQuery('Sort entries must be (field, direction)') from ex
        if field not in _FIELDS:
            raise InvalidQuery(f'Unsupported sort field: {field}')
        if direction not in (1, -1) or isinstance(direction, bool):
            raise InvalidQuery('Sort direction must be 1 or -1')
        column = backups_table.c[_FIELDS[field][0]]
        ordering.append(column.asc() if direction == 1 else column.desc())
    return ordering


class BackupDocument:

    def __init__(self, date: datetime.datetime, schema: str = 'worlds', state: BackupState | str = BackupState.PENDING,
                 doc_id: uuid.UUID | str = None, archive_name: str = None, prefix: str = 'foundry/') -> None:
        self._id = doc_id if doc_id is not None else uuid.uuid4()
        self.date: datetime.datetime = date
        self.prefix: str = prefix
        self.schema: str = schema
        self.archive_name = archive_name if archive_name else f'{schema}-{date.strftime("%Y-%m-%d-%H-%M-%f")}.zip'
        self.state: BackupState | str = state

    @property
    def id(self) -> uuid.UUID | str:
        return self._id

    def asdict(self, serializable=False) -> dict:
        return {
            '_id': str(self.id),
            'date': self.date.strftime('%Y-%m-%dT%H:%M:%S%z' + ('%z' if self.date.tzinfo else 'Z')) if serializable else self.date,
            'unix': int(self.date.timestamp()),
            'schema': self.schema,
            'prefix': self.prefix,
            'archive_name': self.archive_name,
            'state': str(self.state)
        }

    @classmethod
    def from_dict(cls, _in: dict) -> Self:
        prefix = _in['prefix'] if 'prefix' in _in else ''
        return cls(_in['date'], _in['schema'], _in['state'], _in['_id'], _in['archive_name'], prefix)

    def _row(self) -> dict:
        date = _local_naive(self.date)
        return {
            'id': str(self.id),
            'date': date,
            'unix': int(date.timestamp()),
            'schema': self.schema,
            'prefix': self.prefix,
            'archive_name': self.archive_name,
            'state': str(self.state),
        }

    @classmethod
    def _from_row(cls, row) -> Self:
        state: BackupState | str = row.state
        for candidate in BackupState:
            if row.state == str(candidate):
                state = candidate
        return cls(row.date, row.schema, state, row.id, row.archive_name, row.prefix)

    async def insert(self, database: Database):
        await database.ensure_schema()
        async with database.begin() as conn:
            await conn.execute(backups_table.insert().values(**self._row()))

    async def save(self, database: Database):
        """Insert or fully replace the stored document in one transaction."""
        await database.ensure_schema()
        row = self._row()
        if database.url.drivername == 'mysql+asyncmy':
            statement = mysql.insert(backups_table).values(**row)
            statement = statement.on_duplicate_key_update(
                **{key: statement.inserted[key] for key in row if key != 'id'})
        else:
            statement = sqlite.insert(backups_table).values(**row)
            statement = statement.on_conflict_do_update(
                index_elements=['id'],
                set_={key: statement.excluded[key] for key in row if key != 'id'})
        async with database.begin() as conn:
            await conn.execute(statement)

    @classmethod
    async def find(cls, database: Database, filter: Optional[Mapping[str, Any]] = None,
                   sort: Optional[Sequence[Tuple[str, int]]] = None, limit: int = 0) -> List[Self]:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            raise InvalidQuery('Limit must be a non-negative integer')
        statement = select(backups_table).where(*build_conditions(filter)).order_by(*build_ordering(sort))
        if limit:
            statement = statement.limit(limit)
        await database.ensure_schema()
        async with database.begin() as conn:
            result = await conn.execute(statement)
            return [cls._from_row(row) for row in result]

    @classmethod
    async def get(cls, database: Database, doc_id: uuid.UUID | str) -> Optional[Self]:
        found = await cls.find(database, {'_id': str(doc_id)}, limit=1)
        return found[0] if found else None

    @classmethod
    async def delete(cls, database: Database, uid: uuid.UUID | str):
        await database.ensure_schema()
        async with database.begin() as conn:
            await conn.execute(delete(backups_table).where(backups_table.c.id == str(uid)))
