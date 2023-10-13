import datetime
import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List

import boto3
import smart_open

from services.database import BackupDocument, BackupState
from utils import get_logger


class BackupService:

    def __init__(self, data_path: str, bucket: str, s3=None) -> None:
        self.log = get_logger(self)
        self.data_dir = Path(data_path)
        self.bucket = bucket
        self._s3 = s3

    @property
    def s3_client(self):
        return self._s3 or boto3.client('s3')

    @s3_client.setter
    def s3_client(self, client):
        self._s3 = client

    def find(self, *args, **kwargs) -> List[BackupDocument]:
        return BackupDocument.find(*args, **kwargs)

    def list(self, sort=None) -> List[BackupDocument]:
        return BackupDocument.find(sort=sort)

    def perform(self, schema):
        base_dir = self.data_dir / schema
        cwd = Path.cwd()
        backup = BackupDocument(datetime.datetime.now(), schema)

        self.log.info('Started backup of %s', base_dir)
        try:
            if base_dir.exists():
                transport_params = {'client': self.s3_client}
                s3_url = "s3://%s/%s" % (self.bucket, backup.archive_name)

                os.chdir(self.data_dir)
                self.log.info('Creating S3 object %s', s3_url)
                with smart_open.open(s3_url, 'wb', transport_params=transport_params) as s3_object, \
                    zipfile.ZipFile(s3_object, 'w', compression=zipfile.ZIP_DEFLATED) as zf_file:
                    path = base_dir.relative_to(Path.cwd())
                    backup.state = BackupState.RUNNING

                    for item in path.glob('**/*'):
                        self.log.debug('Adding %s', item)
                        if item.is_dir():
                            zf_file.write(item)
                        else:
                            with item.open('rb') as fin, zf_file.open(str(item), 'w') as dest:
                                shutil.copyfileobj(fin, dest)

                backup.state = BackupState.SUCCESS
                return backup.archive_name
            else:
                self.log.warning('No such directory to backup %s', base_dir)
        except Exception as ex:
            backup.state = BackupState.FAILED
            self.log.critical(ex)
            raise ex
        finally:
            os.chdir(cwd)
            backup.insert()

    def restore(self, backup_id: str):
        backup = BackupDocument.get({'_id': backup_id})
        if backup:
            self.log.info('Restoring %s', backup_id, extra=backup.asdict(True))

            transport_params = {'client': self.s3_client}
            s3_url = "s3://%s/%s" % (self.bucket, backup.archive_name)

            # TODO: cleanup safeties
            with smart_open.open(s3_url, 'rb', transport_params=transport_params) as s3_object, \
                zipfile.ZipFile(s3_object, compression=zipfile.ZIP_DEFLATED) as zf_file:
                dest_dir = self.data_dir / backup.schema
                cwd = Path.cwd()

                try:
                    with tempfile.TemporaryDirectory(dir=self.data_dir) as tmpdir:
                        tmp_dir = Path(tmpdir)
                        os.chdir(tmp_dir)

                        self.log.debug('Extracting into %s', tmp_dir)
                        zf_file.extractall()

                        fallback_name = dest_dir.with_name(dest_dir.name + '.bak')
                        if dest_dir.exists():
                            self.log.debug('Renaming destination for safety as %s', fallback_name)
                            fallback_dir = dest_dir.rename(fallback_name)

                        extracted = tmp_dir / backup.schema
                        self.log.debug('Moving extracted file %s to destination %s', extracted, dest_dir)
                        extracted.rename(dest_dir)

                        if fallback_name.exists():
                            self.log.debug('Releasing safety')
                            shutil.rmtree(fallback_dir)

                    self.log.info('Successfully restored %s to %s', backup_id, dest_dir)
                except Exception as ex:
                    self.log.critical(ex)
                    raise ex
                finally:
                    os.chdir(cwd)
