import os

import bjoern
from compose.cli.command import get_project
from compose.project import NoSuchService
from flask import Flask
from flask_htpasswd import HtPasswdAuth


class FoundryProject:

    def __init__(self, compose_file) -> None:
        self.compose_file = compose_file
        self.project = get_project(compose_file, project_name='west-marches')

    def stop(self, service_name):
        self.project.validate_service_names([service_name])
        self.project.stop([service_name])

    def restart(self, service_name):
        self.project.validate_service_names([service_name])
        self.project.restart([service_name])


project_path = os.environ['COMPOSE_DIR']

app = Flask(__name__)
app.config['FLASK_HTPASSWD_PATH'] = os.environ['HTPASSWD_PATH']
auth = HtPasswdAuth(app)


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


def main():
    bjoern.run(app, '0.0.0.0', 5000)


if __name__ == "__main__":
    main()
