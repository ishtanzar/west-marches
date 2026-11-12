import datetime

from uuid import UUID

from services.database import BackupDocument


def test_backup(monty):
    assert BackupDocument.collection().name == 'backups'

    backup1 = BackupDocument(datetime.datetime(2026, 1, 1))
    assert isinstance(backup1.id, UUID)
    backup1.insert()
    assert isinstance(backup1.id, str)

    assert len(BackupDocument.find()) == 1
    assert BackupDocument.get({"_id": backup1.id}).asdict() == backup1.asdict()

    BackupDocument.delete(backup1.id)
    assert len(BackupDocument.find()) == 0