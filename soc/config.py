from pathlib import Path

from bevy import Dependencies
from bevy.function_provider import FunctionProvider
from pydantic import BaseSettings, Extra
from yaml import safe_load


class Config(Dependencies):
    def __init__(self, *file_paths: str | Path):
        self._paths = tuple(Path(file_path) for file_path in file_paths)
        self._data = {}

        self._load()

    def _load(self):
        _open = self.__bevy__.get(open, provider_type=FunctionProvider)
        for path in self._paths:
            with _open(path, "rb") as f:
                self._data |= safe_load(f.read())
