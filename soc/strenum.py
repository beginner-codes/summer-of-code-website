from enum import Enum, auto
from typing import Any


auto = auto


class StrEnum(str, Enum):
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
        return name

    def __str__(self):
        return self.value
