import datetime
import logging
import os
import shutil
import zipfile
from pathlib import Path

import boto3
import smart_open


class BackupService:

    def __init__(self, data_path, bucket, s3=None) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_dir = Path(data_path)
        self.bucket = bucket
        self._s3 = s3

    @property
    def s3_client(self):
        return self._s3 or boto3.client('s3')

    @s3_client.setter
    def s3_client(self, client):
        self._s3 = client

    def perform(self, schema):
        base_dir = self.data_dir / schema
        cwd = Path.cwd()

        self.logger.info('Started backup of %s', base_dir)
        try:
            if base_dir.exists():
                transport_params = {'client': self.s3_client}
                backup_time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%f')
                archive_name = "%s-%s.zip" % (schema, backup_time)
                s3_url = "s3://%s/%s" % (self.bucket, archive_name)

                os.chdir(self.data_dir)
                self.logger.info('Creating S3 object %s', s3_url)
                with smart_open.open(s3_url, 'wb', transport_params=transport_params) as s3_object, \
                    zipfile.ZipFile(s3_object, 'w', compression=zipfile.ZIP_DEFLATED) as zf_file:
                    path = base_dir.relative_to(Path.cwd())

                    for item in path.glob('**/*'):
                        self.logger.debug('Adding %s', item)
                        if item.is_dir():
                            zf_file.write(item)
                        else:
                            with item.open('rb') as fin, zf_file.open(str(item), 'w') as dest:
                                shutil.copyfileobj(fin, dest)

                return archive_name
            else:
                self.logger.warning('No such directory to backup %s', base_dir)
        except Exception as ex:
            self.logger.critical(ex)
            raise ex
        finally:
            os.chdir(cwd)
