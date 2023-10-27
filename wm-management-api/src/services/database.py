import datetime
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from montydb import MontyClient, MontyCollection, MontyCursor
from montydb.results import InsertOneResult
from typing import List, Optional, Type, Self
from uuid import UUID


class Engine:
    _client: MontyClient
    _database: str = 'westmarches'

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

    def __init__(self, doc_id: uuid.UUID = None) -> None:
        self._id = doc_id if doc_id else uuid.uuid4()

    @property
    def id(self):
        return self._id

    @abstractmethod
    def asdict(self, serializable=False) -> dict:
        pass

    def insert(self):
        result: InsertOneResult = type(self).collection().insert_one(self.asdict())
        self._id = result.inserted_id

    @classmethod
    @abstractmethod
    def from_dict(cls, _in: dict) -> Self:
        pass

    @classmethod
    @abstractmethod
    def collection(cls) -> MontyCollection:
        pass

    @classmethod
    def find(cls, *args, **kwargs) -> List[Self]:
        return [cls.from_dict(x) for x in cls.collection().find(*args, **kwargs)]

    @classmethod
    def get(cls, *args, **kwargs) -> Self:
        return cls.from_dict(cls.collection().find_one(*args, **kwargs))

    @classmethod
    def delete(cls, uid: str):
        cls.collection().delete_one({'_id': uid})


class BackupState(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    FAILED = 'failed'
    SUCCESS = 'success'


class BackupDocument(AbstractDocument):

    def __init__(self, date: datetime.datetime, schema: str = 'worlds', state: BackupState = BackupState.PENDING,
                 doc_id: uuid.UUID = None, archive_name: str = None, prefix: str = 'foundry/') -> None:
        super().__init__(doc_id)

        self.date: datetime.datetime = date
        self.prefix: str = prefix
        self.schema: str = schema
        self.archive_name = archive_name if archive_name else f'{schema}-{date.strftime("%Y-%m-%d-%H-%M-%f")}.zip'
        self.state: BackupState = state

    @classmethod
    def collection(cls):
        return Engine.collection('backups')

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
