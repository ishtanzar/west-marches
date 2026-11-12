import logging.config
import os
import re
from urllib.parse import urlparse

import boto3
import yaml
from montydb import set_storage, MontyClient

from api import BasicAuth, WestMarchesApi
from services.backup import BackupService
from services.database import Engine
from services.discord import DiscordService
from services.docker import FoundryProject
from services.kanka import KankaService
from services.scaleway import ScalewayService
from westmarches_utils.api.foundry import FoundryApi, FoundryApiConfig

compose_files = os.environ['COMPOSE_FILES'] if 'COMPOSE_FILES' in os.environ.keys() else ''
foundry_data_path = os.environ['FOUNDRY_DATA_PATH']
foundry_endpoint = os.environ['FOUNDRY_ENDPOINT']
backup_bucket = os.environ['BACKUP_S3_BUCKET']
db_endpoint = os.environ['DATABASE_ENDPOINT']
s3_endpoint = os.environ['BACKUP_S3_ENDPOINT'] if 'BACKUP_S3_ENDPOINT' in os.environ.keys() else None
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
    import_name=__name__,
    auth=BasicAuth(os.environ.get("MGMNT_API_SECRET")),
    # compose=FoundryProject(re.split(r', ?', compose_files)),
    # backup=BackupService(foundry_data_path, backup_bucket, s3=boto3.client('s3', endpoint_url=s3_endpoint)),
    # foundry=FoundryApi(FoundryApiConfig()),
    # kanka=KankaService(kanka_token, kanka_campaign),
    discord=DiscordService(
        os.environ['DISCORD_BOT_SECRET'],
        os.environ['DISCORD_GM_GUILD_ID'],
        os.environ['DISCORD_BOT_ID'],
    ),
    scaleway=ScalewayService({
        "organization_id": os.environ["SCW_ORGANIZATION_ID"],
        "project_id": os.environ["SCW_PROJECT_ID"],
        "group_id": os.environ["S3_EDITORS_GROUP_ID"],
        "access_key": os.environ["SCW_ACCESS_KEY"],
        "secret_key": os.environ["SCW_SECRET_KEY"],
        "ttl_seconds": os.environ.get("S3_EDITORS_KEY_TTL", "14400"),
        "application_prefix": os.environ.get("S3_EDITORS_APP_PREFIX", "westmarches"),
        "log_level": os.environ.get("SCW_LOG_LEVEL", "WARNING"),
    }),
)


def main():
    app.run('0.0.0.0', 5000, use_reloader=False)


if __name__ == "__main__":
    main()
