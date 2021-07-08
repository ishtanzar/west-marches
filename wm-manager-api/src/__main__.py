import logging
import logging.config
import os
import signal
from urllib.parse import urlparse

import bjoern
import boto3
import yaml
from montydb import set_storage, MontyClient

from api import WestMarchesApi
from services.backup import BackupService
from services.database import Engine
from services.docker import FoundryProject
from services.foundryvtt import FoundryService

project_path = os.environ['COMPOSE_DIR']
foundry_data_path = os.environ['FOUNDRY_DATA_PATH']
foundry_endpoint = os.environ['FOUNDRY_ENDPOINT']
backup_bucket = os.environ['BACKUP_S3_BUCKET']
db_endpoint = os.environ['DATABASE_ENDPOINT']
s3_endpoint = os.environ['BACKUP_S3_ENDPOINT'] if 'BACKUP_S3_ENDPOINT' in os.environ.keys() else None

with open(os.environ['LOGGING_CONFIG']) as fd:
    config = yaml.safe_load(fd.read())

logging.config.dictConfig(config)
log = logging.getLogger()

db_url = urlparse(db_endpoint)
set_storage(db_url.path, storage=db_url.scheme)
Engine._client = MontyClient(db_url.path)

app = WestMarchesApi(
    __name__,
    FoundryProject(project_path),
    BackupService(foundry_data_path, backup_bucket, s3=boto3.client('s3', endpoint_url=s3_endpoint)),
    FoundryService(foundry_endpoint)
)


def sigterm_handler(_signo, _stack_frame):
    log.warning('Caught SIGTERM')
    logging.shutdown()
    os.kill(os.getpid(), signal.SIGINT)


def main():
    port = 5000
    ip = '0.0.0.0'
    signal.signal(signal.SIGTERM, sigterm_handler)

    log.info('Starting bjoern on %s:%s', ip, port)
    try:
        bjoern.run(app, ip, port)
    except KeyboardInterrupt:
        log.info('Caught SIGINT')
    finally:
        log.info('Exiting bjoern')


if __name__ == "__main__":
    main()
