import hashlib
import pathlib
import unittest
import zipfile

import boto3
import smart_open
from localstack.services import infra

from backup import BackupService


class TestBackupService(unittest.TestCase):
    backup_bucket = "my-bucket"
    resources = pathlib.Path(__file__).parent / 'resources'

    @classmethod
    def setUpClass(cls) -> None:
        infra.start_infra(asynchronous=True, apis=["s3"])

    def sha1_file(self, fp):
        hash = hashlib.sha1()

        while True:
            data = fp.read(65536)
            if not data:
                break
            hash.update(data)

        return hash

    def test_upload(self):
        readme_path = self.resources / 'worlds/my-test-world/README.txt'
        with open(readme_path, 'rb') as f:
            readme_hash = self.sha1_file(f)

        s3 = boto3.client('s3', endpoint_url="http://localhost:4566")
        """ :type: pyboto3.s3 """

        s3.create_bucket(Bucket=self.backup_bucket)

        service = BackupService(self.resources, self.backup_bucket, s3=s3)
        backup = service.perform('worlds')

        self.assertTrue(any(s3.list_objects_v2(Bucket=self.backup_bucket, Prefix=backup)['Contents']))

        with smart_open.open('s3://%s/%s' % (self.backup_bucket, backup), 'rb',
                             transport_params={'client': s3}) as zf_in:
            with zipfile.ZipFile(zf_in, compression=zipfile.ZIP_DEFLATED) as zf:
                root = zipfile.Path(zf)
                zipped_readme = root / readme_path.relative_to(self.resources)

                self.assertTrue(zipped_readme.exists())

                with zipped_readme.open() as readme_fp:
                    self.assertEqual(readme_hash.hexdigest(), self.sha1_file(readme_fp).hexdigest())

    def tearDown(self) -> None:
        infra.stop_infra()
