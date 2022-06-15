from typing import Callable, Type, TypeVar, ParamSpec

from bevy import Context
from fastapi import Depends

from soc.config.settings_provider import SettingsProvider
from soc.database.database import DatabaseProvider

T = TypeVar("T")
R = TypeVar("R")
P = ParamSpec("P")
InjectType = Callable[P, R] | Type[T]
InjectValue = Callable[P, R] | T


def context() -> Context:
    ctx = Context.factory()
    ctx.add_provider(DatabaseProvider)
    ctx.add_provider(SettingsProvider)
    return ctx


def inject(obj: InjectType, *, add: bool = True) -> InjectValue:
    def inject_from_context(ctx: Context = Depends(context)):
        return ctx.get(obj) or ctx.create(obj, add_to_context=add)

    return Depends(inject_from_context)
