import json
from pathlib import Path
from types import SimpleNamespace


class Config:
    __data__ = object()

    @staticmethod
    def get():
        return Config.__data__

    @staticmethod
    def load(path):
        with Path(path).open() as fp:
            Config.__data__ = json.load(fp, object_hook=lambda x: SimpleNamespace(**x))
        return Config.__data__


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

