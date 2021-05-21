import os

import bjoern
from compose.cli.command import get_project
from compose.project import NoSuchService
from flask import Flask


class FoundryProject:

    def __init__(self, compose_file) -> None:
        self.compose_file = compose_file
        self.project = get_project(compose_file)

    def stop(self, service_name):
        self.project.validate_service_names([service_name])
        self.project.stop([service_name])

    def restart(self, service_name):
        self.project.validate_service_names([service_name])
        self.project.restart([service_name])


app = Flask(__name__)
project_path = os.environ['COMPOSE_DIR']
print(project_path)
project = FoundryProject(project_path)


@app.route('/')
def index():
    return 'Hello World'


@app.route('/container/stop/<service_name>', methods=['POST'])
def stop_container(service_name):
    try:
        project.stop(service_name)
    except NoSuchService as nse:
        return nse.msg, 404

    return 'Done', 204


@app.route('/container/restart/<service_name>', methods=['POST'])
def restart_container(service_name):
    try:
        project.restart(service_name)
    except NoSuchService as nse:
        return nse.msg, 404

    return 'Done', 204


def main():
    bjoern.run(app, '127.0.0.1', 5000)


if __name__ == "__main__":
    main()
