import json
from dotwiz import DotWiz
from pathlib import Path


class Config(DotWiz):

    def get(self, attr: str, default=None):
        full_attr = attr.split('.')
        current = self

        for current_attr in full_attr:
            try:
                current = getattr(current, current_attr)
            except AttributeError:
                return default

        return current

    def set(self, attr: str, value=None):
        full_attr = attr.split('.')
        current = self

        for current_attr in full_attr[:-1]:
            try:
                current = current[current_attr]
            except KeyError:
                current.__dict__[current_attr] = next_attr = Config()
                current = next_attr

        current.__dict__[full_attr[-1]] = value

    @staticmethod
    def load(path):
        with Path(path).open() as fp:
            return json.load(fp, object_hook=lambda x: Config(x))

