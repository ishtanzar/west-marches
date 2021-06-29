import os

import boto3
from compose.project import NoSuchService
from flask import Flask
from flask_htpasswd import HtPasswdAuth

from backup import BackupService
from docker_service import FoundryProject

project_path = os.environ['COMPOSE_DIR']
foundry_data_path = os.environ['FOUNDRY_DATA_PATH']
backup_bucket = os.environ['BACKUP_S3_BUCKET']
s3_endpoint = os.environ['BACKUP_S3_ENDPOINT']

app = Flask(__name__)
app.config['FLASK_HTPASSWD_PATH'] = os.environ['HTPASSWD_PATH']
auth = HtPasswdAuth(app)

s3 = boto3.client('s3', endpoint_url=s3_endpoint)


@app.route('/')
@auth.required
def index(user):
    return "Hello, {}!".format(user)


@app.route('/container/restart/<service_name>', methods=['POST'])
@auth.required
def restart_container(service_name, user):
    try:
        FoundryProject(project_path).restart(service_name)
    except NoSuchService as nse:
        return nse.msg, 404

    return 'Done', 204


@app.route('/backup/perform', methods=['POST'])
@auth.required
def backup_perform(user):
    service_name = 'foundry'
    foundry_project = FoundryProject(project_path)
    backup_service = BackupService(foundry_data_path, backup_bucket, s3=s3)

    try:
        foundry_project.stop(service_name)

        for schema in ['worlds', 'systems', 'modules']:
            backup_service.perform(schema)

        foundry_project.restart(service_name)
    except NoSuchService as nse:
        return nse.msg, 404

    return 'Done', 204
