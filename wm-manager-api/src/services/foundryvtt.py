import json
import logging

import smart_open

from utils import get_logger


class FoundryService:

    def __init__(self, endpoint: str = 'http://foundry') -> None:
        self.log = get_logger(self)
        self._endpoint = endpoint

    def find_actors(self):
        with smart_open.open('%s/actors' % self._endpoint) as fp:
            roster: dict = json.load(fp)
            return roster['actors']
