import logging.config
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import boto3
import yaml
from montydb import set_storage, MontyClient

from api import WestMarchesApi
from services.backup import BackupService
from services.chatbot import IntentService
from services.database import Engine
from services.docker import FoundryProject
from services.foundryvtt import FoundryService
from services.kanka import KankaService

compose_files = os.environ['COMPOSE_FILES'] if 'COMPOSE_FILES' in os.environ.keys() else ''
foundry_data_path = os.environ['FOUNDRY_DATA_PATH']
foundry_endpoint = os.environ['FOUNDRY_ENDPOINT']
backup_bucket = os.environ['BACKUP_S3_BUCKET']
db_endpoint = os.environ['DATABASE_ENDPOINT']
s3_endpoint = os.environ['BACKUP_S3_ENDPOINT'] if 'BACKUP_S3_ENDPOINT' in os.environ.keys() else None
model_dir = os.environ['INTENT_MODEL_DIR']
kanka_token = os.environ['KANKA_TOKEN']
kanka_campaign = os.environ['KANKA_CAMPAIGN']

with open(os.environ['LOGGING_CONFIG']) as fd:
    config = yaml.safe_load(fd.read())

logging.config.dictConfig(config)
log = logging.getLogger()

db_url = urlparse(db_endpoint)
set_storage(db_url.path, storage=db_url.scheme)
Engine._client = MontyClient(db_url.path)

app = WestMarchesApi(
    __name__,
    FoundryProject(re.split(r', ?', compose_files)),
    BackupService(foundry_data_path, backup_bucket, s3=boto3.client('s3', endpoint_url=s3_endpoint)),
    FoundryService(foundry_endpoint),
    KankaService(kanka_token, kanka_campaign),
    IntentService(Engine(), Path(model_dir))
)


def main():
    app.run('0.0.0.0', 5000, use_reloader=True)


if __name__ == "__main__":
    main()
