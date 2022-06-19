from pathlib import Path
from typing import Type, TypeVar

from bevy import Bevy
from yaml import safe_load

from soc.config.base_model import BaseSettingsModel

T = TypeVar("T", bound=BaseSettingsModel)


class Config(Bevy):
    default_paths = ("production.config.yaml", "development.config.yaml")

    def __init__(self, *file_paths: str | Path):
        super().__init__()
        self._paths = tuple(
            Path(file_path) for file_path in file_paths or self.default_paths
        )
        self._data = {}

        self._load()

    def get(self, model: Type[T], key: str | None = None) -> T:
        data = self._data.get(key, {}) if key else self._data
        return model(**data)

    def _load(self):
        _open = self.bevy.get(open)
        for path in self._paths:
            try:
                f = _open(path, "rb")
            except FileNotFoundError:
                pass
            else:
                with f:
                    self._data |= safe_load(f.read())
