import json
from pathlib import Path
from types import SimpleNamespace


class Config(SimpleNamespace):

    def get(self, attr: str, default = None):
        full_attr = attr.split('.')
        current = self

        for current_attr in full_attr:
            try:
                current = getattr(current, current_attr)
            except AttributeError:
                return default

        return current

    def set(self, attr: str, value = None):
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


class Cache:

    _data = {}
    _path = None

    def __init__(self, file: Path):
        self._path = file
        if file.exists():
            with open(file) as fp:
                self._data = json.load(fp)

    def __setitem__(self, key, value):
        self._data[key] = value

        with self._path.open('w') as fp:
            json.dump(self._data, fp)

    def __getitem__(self, item):
        if item in self._data:
            return self._data[item]
        else:
            return None

