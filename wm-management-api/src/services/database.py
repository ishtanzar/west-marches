import datetime
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional
from uuid import UUID

from montydb import MontyClient, MontyCollection, MontyCursor
from montydb.results import InsertOneResult


class Engine:
    _client: MontyClient
    _database: str = 'westmarches'

    @classmethod
    def backups(cls) -> MontyCollection:
        return cls.collection('backups')

    @classmethod
    def scheduled_sessions(cls) -> MontyCollection:
        return cls.collection('scheduled_sessions')

    @classmethod
    def collection(cls, collection_name) -> MontyCollection:
        return cls._client[cls._database][collection_name]

    @classmethod
    def collections(cls) -> []:
        return cls._client[cls._database].collection_names()

    @classmethod
    def scan(cls, collection_name: str) -> MontyCursor:
        return cls.collection(collection_name).find()

    @classmethod
    def create_collection(cls, collection_name: str, data: Optional[list] = []) -> MontyCollection:
        _col = cls._client[cls._database].create_collection(collection_name)
        if data:
            _col.insert_many(data)
        return _col

    @classmethod
    def drop_collection(cls, collection_name: str):
        cls._client[cls._database].drop_collection(collection_name)


class AbstractDocument(ABC):
    _id: UUID
    _col: MontyCollection

    def __init__(self, col: MontyCollection, doc_id: uuid.UUID = None) -> None:
        self._col = col
        self._id = doc_id if doc_id else uuid.uuid4()

    @property
    def id(self):
        return self._id

    @abstractmethod
    def asdict(self, serializable=False) -> dict:
        pass

    def insert(self):
        result: InsertOneResult = self._col.insert_one(self.asdict())
        self._id = result.inserted_id


class BackupState(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    FAILED = 'failed'
    SUCCESS = 'success'


class BackupDocument(AbstractDocument):
    def __init__(self, date: datetime.datetime, schema: str = 'worlds', state: BackupState = BackupState.PENDING,
                 doc_id: uuid.UUID = None, archive_name: str = None) -> None:
        super().__init__(Engine.backups(), doc_id)

        self.date: datetime.datetime = date
        self.schema: str = schema
        self.archive_name = archive_name if archive_name else '%s-%s.zip' % (schema, date.strftime('%Y-%m-%d-%H-%M-%f'))
        self.state: BackupState = state

    def asdict(self, serializable=False) -> dict:
        return {
            '_id': str(self.id),
            'date': self.date.strftime('%Y-%m-%dT%H:%M:%S%z' + ('%z' if self.date.tzinfo else 'Z')) if serializable else self.date,
            'unix': int(self.date.timestamp()),
            'schema': self.schema,
            'archive_name': self.archive_name,
            'state': str(self.state)
        }

    @classmethod
    def from_dict(cls, _in: dict) -> "BackupDocument":
        return cls(_in['date'], _in['schema'], _in['state'], _in['_id'], _in['archive_name'])

    @classmethod
    def find(cls, *args, **kwargs) -> List["BackupDocument"]:
        return [cls.from_dict(x) for x in Engine.backups().find(*args, **kwargs)]

    @classmethod
    def get(cls, *args, **kwargs) -> "BackupDocument":
        return cls.from_dict(Engine.backups().find_one(*args, **kwargs))


class SessionScheduleDocument(AbstractDocument):
    def __init__(self, date: datetime.datetime, organizer: int, message: dict, journal_id: int = None,
                 doc_id: uuid.UUID = None) -> None:
        super().__init__(Engine.scheduled_sessions(), doc_id)

        self.date: datetime.datetime = date
        self.organizer = organizer
        self.message = message
        self.journal_id = journal_id

    def asdict(self, serializable=False) -> dict:
        return {
            '_id': str(self.id),
            'date': self.date.strftime('%Y-%m-%d-%H-%M-%f') if serializable else self.date,
            'organizer': self.organizer,
            'message': self.message,
            'journal': self.journal_id
        }

    @classmethod
    def from_dict(cls, _in: dict) -> "SessionScheduleDocument":
        return cls(_in['date'], _in['organizer'], _in['message'], _in['journal'], _in['_id'])

    @classmethod
    def find(cls, *args, **kwargs) -> List["SessionScheduleDocument"]:
        return [cls.from_dict(x) for x in Engine.scheduled_sessions().find(*args, **kwargs)]

    @classmethod
    def find_one(cls, *args, **kwargs) -> "SessionScheduleDocument":
        return cls.from_dict(Engine.scheduled_sessions().find_one(*args, **kwargs))
