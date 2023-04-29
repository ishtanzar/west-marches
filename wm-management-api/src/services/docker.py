from python_on_whales import DockerClient
from python_on_whales.utils import run

from utils import get_logger


class NoSuchService(Exception):

    def __init__(self, service):
        self._service = service

    @property
    def msg(self):
        return f'No such service {self._service}'


class FoundryProject:

    def __init__(self, compose_files) -> None:
        self.log = get_logger(self)
        self.compose_files = compose_files

        docker = DockerClient(compose_files=compose_files, compose_project_name="west-marches")
        self.compose = docker.compose

    def _validate_service(self, service):
        return service in self.compose.config().services

    def stop(self, service_name):
        if self._validate_service(service_name):
            self.log.info("Stopping docker-compose service %s", service_name)
            self.compose.stop(service_name)
        else:
            raise NoSuchService(service_name)

    def restart(self, service_name):
        if self._validate_service(service_name):
            self.log.info("Restarting docker-compose service %s", service_name)

            cmd = self.compose.docker_compose_cmd + ['restart']
            cmd.add_flag('--no-deps', True)
            cmd += [service_name]

            run(cmd)
        else:
            raise NoSuchService(service_name)
