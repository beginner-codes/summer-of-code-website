from collections import ChainMap
from typing import Callable, Type, TypeVar, overload, ParamSpec

from bevy import Context
from fastapi import Depends, routing, FastAPI
from fastapi.routing import get_request_handler

from soc.config.settings_provider import SettingsProvider
from soc.database.provider import DatabaseProvider

T = TypeVar("T")
R = TypeVar("R")
P = ParamSpec("P")


class DependencyOverridesProvider:
    def __init__(self, app, **overrides):
        self.overrides = overrides
        self.dependency_overrides = ChainMap(self.overrides, app.dependency_overrides)


class BevyRoute(routing.APIRoute):
    def get_route_handler(self):
        async def custom_handler(request, *args, **kwargs):
            response_class = self.response_class
            overrides_provider = self.dependency_overrides_provider
            overrides = overrides_provider.dependency_overrides
            context = overrides.get(create_context, create_context)().branch()
            if hasattr(self.response_class, "__bevy_context__"):
                response_class = context.bind(response_class)

            handler = get_request_handler(
                dependant=self.dependant,
                body_field=self.body_field,
                status_code=self.status_code,
                response_class=response_class,
                response_field=self.secure_cloned_response_field,
                response_model_include=self.response_model_include,
                response_model_exclude=self.response_model_exclude,
                response_model_by_alias=self.response_model_by_alias,
                response_model_exclude_unset=self.response_model_exclude_unset,
                response_model_exclude_defaults=self.response_model_exclude_defaults,
                response_model_exclude_none=self.response_model_exclude_none,
                dependency_overrides_provider=DependencyOverridesProvider(
                    overrides_provider, create_context=lambda: context
                ),
            )
            return await handler(request, *args, **kwargs)

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
