import json

from pathlib import Path


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
