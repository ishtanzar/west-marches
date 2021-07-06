import datetime
import uuid
from enum import Enum
from typing import List
from uuid import UUID

from montydb import MontyClient, MontyCollection, MontyCursor


class Engine:
    _client: MontyClient
    _database: str = 'westmarches'

    @classmethod
    def backups(cls) -> MontyCollection:
        return cls._client[cls._database]['backups']


class BackupState(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    FAILED = 'failed'
    SUCCESS = 'success'


class BackupDocument:
    def __init__(self, date: datetime.datetime, schema: str = 'worlds', state: BackupState = BackupState.PENDING,
                 doc_id: uuid.UUID = None, archive_name: str = None) -> None:

        self.id: UUID = doc_id if doc_id else uuid.uuid4()
        self.date: datetime.datetime = date
        self.schema: str = schema
        self.archive_name = archive_name if archive_name else '%s-%s.zip' % (schema, date.strftime('%Y-%m-%d-%H-%M-%f'))
        self.state: BackupState = state

    def asdict(self, serializable=False) -> dict:
        return {
            '_id': str(self.id),
            'date': self.date.strftime('%Y-%m-%d-%H-%M-%f') if serializable else self.date,
            'schema': self.schema,
            'archive_name': self.archive_name,
            'state': str(self.state)
        }

    def insert(self):
        Engine.backups().insert_one(self.asdict())

    @classmethod
    def from_dict(cls, _in: dict) -> "BackupDocument":
        return cls(_in['date'], _in['schema'], _in['state'], _in['_id'], _in['archive_name'])

    @classmethod
    def find(cls, *args, **kwargs) -> List["BackupDocument"]:
        return [cls.from_dict(x) for x in Engine.backups().find(*args, **kwargs)]

    @classmethod
    def get(cls, *args, **kwargs) -> "BackupDocument":
        return cls.from_dict(Engine.backups().find_one(*args, **kwargs))
