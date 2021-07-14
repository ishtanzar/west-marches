import asyncio
import logging.config
import os
from pathlib import Path
from urllib.parse import urlparse

import boto3
import hypercorn.asyncio
import yaml
from montydb import set_storage, MontyClient

from api import WestMarchesApi
from services.agenda import AgendaService
from services.backup import BackupService
from services.chatbot import ChatbotService
from services.database import Engine
from services.discord import DiscordService
from services.docker import FoundryProject
from services.foundryvtt import FoundryService
from services.kanka import KankaService

project_path = os.environ['COMPOSE_DIR']
foundry_data_path = os.environ['FOUNDRY_DATA_PATH']
foundry_endpoint = os.environ['FOUNDRY_ENDPOINT']
backup_bucket = os.environ['BACKUP_S3_BUCKET']
db_endpoint = os.environ['DATABASE_ENDPOINT']
s3_endpoint = os.environ['BACKUP_S3_ENDPOINT'] if 'BACKUP_S3_ENDPOINT' in os.environ.keys() else None
discord_secret = os.environ['DISCORD_SECRET']

with open(os.environ['LOGGING_CONFIG']) as fd:
    config = yaml.safe_load(fd.read())

logging.config.dictConfig(config)
log = logging.getLogger()

db_url = urlparse(db_endpoint)
set_storage(db_url.path, storage=db_url.scheme)
Engine._client = MontyClient(db_url.path)
shutdown_event = asyncio.Event()

app = WestMarchesApi(
    __name__,
    FoundryProject(project_path),
    BackupService(foundry_data_path, backup_bucket, s3=boto3.client('s3', endpoint_url=s3_endpoint)),
    FoundryService(foundry_endpoint),
    DiscordService(discord_secret),
    KankaService()
)


def main():
    server_cfg = hypercorn.Config()
    server_cfg.bind = ['0.0.0.0:5000']
    server_cfg.use_reloader = True

    asyncio.run(hypercorn.asyncio.serve(app, server_cfg))


if __name__ == "__main__":
    main()
