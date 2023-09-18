import json

from pathlib import Path

from types import SimpleNamespace


class Config(SimpleNamespace):

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
                current = getattr(current, current_attr)
            except AttributeError:
                setattr(current, current_attr, next_attr := Config())
                current = next_attr

        setattr(current, full_attr[-1], value)

    @staticmethod
    def load(path):
        with Path(path).open() as fp:
            return json.load(fp, object_hook=lambda x: Config(**x))

