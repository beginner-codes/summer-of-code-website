from __future__ import annotations

from typing import Any, cast, Generic, TypeVar, Type
from weakref import WeakKeyDictionary

T = TypeVar("T")


class StateProperty(Generic[T]):
    def __init__(self):
        self._instances: WeakKeyDictionary[Any, _StateProperty[T]] = WeakKeyDictionary()

    def __get__(self, instance, owner):
        return self.get(instance)

    def get(self, instance):
        if instance not in self._instances:
            self._instances[instance] = _StateProperty[T]()

        return self._instances[instance]


class _UnmonitoredProperty(Generic[T]):
    def __init__(self, state: StateProperty):
        self._state_property = state

    def __get__(self, instance, owner):
        state = self._state_property.get(instance)
        return state.value

    def __set__(self, instance, value):
        state = self._state_property.get(instance)
        state.value = value


class _MonitoredProperty(_UnmonitoredProperty):
    def __set__(self, instance, value):
        super().__set__(instance, value)
        state = self._state_property.get(instance)
        state.changed = True


class _StateProperty(Generic[T]):
    def __init__(self):
        self.changed = False
        self.value = None


def state_property(t: Type[T]) -> tuple[T, T, StateProperty[T]]:
    state = StateProperty[T]()
    return (
        cast(T, _MonitoredProperty(state)),
        cast(T, _UnmonitoredProperty(state)),
        state,
    )
