from typing import Callable, Type, TypeVar, overload, ParamSpec

from bevy import Context
from fastapi import Depends, routing, FastAPI

from soc.config.settings_provider import SettingsProvider
from soc.database.provider import DatabaseProvider

T = TypeVar("T")
R = TypeVar("R")
P = ParamSpec("P")


class BevyRoute(routing.APIRoute):
    def get_route_handler(self):
        get_handler = super().get_route_handler
        handler = None

        async def custom_handler(*args, **kwargs):
            nonlocal handler
            if handler is None:
                if hasattr(self.response_class, "__bevy_context__"):
                    overrides = self.dependency_overrides_provider.dependency_overrides
                    context = overrides.get(create_context, create_context)()
                    self.response_class = context.bind(self.response_class)

                handler = get_handler()

            return await handler(*args, **kwargs)

        return custom_handler


def create_app(*args, **kwargs) -> FastAPI:
    app = FastAPI()
    app.router.route_class = BevyRoute
    return app


def create_context() -> Context:
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
    def inject_from_context(ctx: Context = Depends(create_context)):
        return ctx.get(obj) or ctx.create(obj, add_to_context=add)

    return Depends(inject_from_context)
