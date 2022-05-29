from pathlib import Path
from yaml import safe_load

from bevy import Dependencies
from bevy.function_provider import FunctionProvider


class Config(Dependencies):
    def __init__(self, file_path: str | Path):
        self._path = Path(file_path)
        self._data = {}

        self._load()

    def _load(self):
        _open = self.__bevy__.get(open, provider_type=FunctionProvider)
        with _open(self._path, "rb") as f:
            self._data |= safe_load(f.read())
