from __future__ import annotations

from typing import Iterable, Generic, TypeVar, Type, cast

T = TypeVar("T")


class StateProperty(Generic[T]):
    def __init__(self):
        self.changed = False
        self.value = None

    def __iter__(self) -> Iterable:
        return iter(
            (
                property(self._getter, self._setter),
                property(self._getter, self._direct_setter),
                self,
            )
        )

    def _getter(self, _) -> T:
        return self._value

    def _setter(self, _, value: T):
        self._direct_setter(_, value)
        self.changed = True

    def _direct_setter(self, _, value: T):
        self._value = value


def state_property(t: Type[T]) -> tuple[T, T, StateProperty[T]]:
    return cast(tuple[T, T, StateProperty[T]], StateProperty[T]())
