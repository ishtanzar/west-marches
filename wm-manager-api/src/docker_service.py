import logging

from compose.cli.command import get_project


class FoundryProject:

    def __init__(self, compose_file) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.compose_file = compose_file
        self.project = get_project(compose_file, project_name='west-marches')

    def stop(self, service_name):
        self.project.validate_service_names([service_name])
        self.logger.info("Stopping docker-compose service %s", service_name)
        self.project.stop([service_name])

    def restart(self, service_name):
        self.project.validate_service_names([service_name])
        self.logger.info("Restarting docker-compose service %s", service_name)
        self.project.restart([service_name])
