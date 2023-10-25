import datetime

from services.database import BackupDocument


def test_backup(monty):
    assert BackupDocument.collection().name == 'backups'

    backup1 = BackupDocument(datetime.datetime.now())
    backup1.insert()

    assert len(BackupDocument.find()) == 1

    BackupDocument.delete(backup1.id)
    assert len(BackupDocument.find()) == 0