import json
import logging


class Donations:

    def __init__(self, config):
        self._logger = logging.getLogger(type(self).__name__)
        self._config = config

    async def reset(self):
        self._logger.info('Reset donations cache file')
        with open(self._config.donations.filename, 'w') as fp:
            json.dump({}, fp)

