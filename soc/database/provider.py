from typing import Type, TypeVar

from bevy import Inject
from bevy.providers.function_provider import bevy_method
from bevy.providers.type_provider import TypeProvider
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from soc.config.models.config import DatabaseSettings

T = TypeVar("T")


class DatabaseProvider(TypeProvider, priority="high"):
    def __init__(self, *_, **__):
        super().__init__()
        self._create_methods = {
            AsyncEngine: self.create_connection,
            AsyncSession: self.create_session,
            sessionmaker: self.create_session_maker,
        }

    def create(
        self, obj: Type[AsyncEngine], *args, add: bool = False, **kwargs
    ) -> AsyncEngine:
        inst = self._create_methods[obj](*args, **kwargs)
        if add:
            self.add(inst, use_as=obj)

        return inst

    def get(self, obj: Type[T], default: T | None = None) -> T | None:
        if obj is AsyncSession:
            return self.create_session()

        return super().get(obj, default)

    def supports(self, obj: Type[AsyncEngine] | Type[AsyncSession]) -> bool:
        try:
            return obj in self._create_methods
        except TypeError:
            return False

    @bevy_method
    def create_connection(self, settings: DatabaseSettings = Inject) -> AsyncEngine:
        engine = create_async_engine(settings.uri)
        self.bevy.add(engine, use_as=AsyncEngine)
        return engine

    @bevy_method
    def create_session(self, session_factory: sessionmaker = Inject) -> AsyncSession:
        return session_factory()

    @bevy_method
    def create_session_maker(self, engine: AsyncEngine = Inject) -> sessionmaker:
        return sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
