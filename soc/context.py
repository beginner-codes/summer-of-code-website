from typing import Callable, Type, TypeVar, overload, ParamSpec

from bevy import Context
from fastapi import Depends

from soc.config.settings_provider import SettingsProvider
from soc.database.provider import DatabaseProvider

T = TypeVar("T")
R = TypeVar("R")
P = ParamSpec("P")


def context() -> Context:
    ctx = Context.factory()
    ctx.add_provider(DatabaseProvider)
    ctx.add_provider(SettingsProvider)
    return ctx


@overload
def inject(obj: Callable[P, R], *, add: bool = True) -> Callable[P, R]:
    ...


@overload
def inject(obj: Type[T], *, add: bool = True) -> T:
    ...


def inject(obj: Callable[P, R] | Type[T], *, add: bool = True) -> Callable[P, R] | T:
    def inject_from_context(ctx: Context = Depends(context)):
        return ctx.get(obj) or ctx.create(obj, add_to_context=add)

    return Depends(inject_from_context)
