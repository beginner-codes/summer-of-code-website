from typing import Type, TypeVar

from bevy import Inject
from bevy.providers.function_provider import bevy_method
from bevy.providers.injection_priority_helpers import high_priority
from bevy.providers.type_provider import TypeProvider
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from soc.database.config import DatabaseSettings


# Aliases for more understandable annotations
Database = AsyncEngine
Session = AsyncSession

T = TypeVar("T")


class DatabaseProvider(TypeProvider):
    create_and_insert = high_priority

    def __init__(self, *_, **__):
        super().__init__()
        self._create_methods = {
            Database: self.create_connection,
            Session: self.create_session,
        }

    def create(
        self, obj: Type[Database], *args, add: bool = False, **kwargs
    ) -> Database:
        inst = self._create_methods[obj](*args, **kwargs)
        if add:
            self.add(inst, use_as=obj)

        return inst

    def get(self, obj: Type[T], default: T | None = None) -> T | None:
        if obj is Session:
            return self.create_session()

        return super().get(obj, default)

    def supports(self, obj: Type[Database] | Type[Session]) -> bool:
        try:
            return obj in self._create_methods
        except TypeError:
            return False

    @bevy_method
    def create_connection(self, settings: DatabaseSettings = Inject) -> Database:
        engine = create_async_engine(settings.uri)
        self.bevy.add(engine, use_as=Database)
        self.bevy.add(
            sessionmaker(engine, expire_on_commit=False, class_=Session),
            use_as=sessionmaker,
        )
        return engine

    @bevy_method
    def create_session(self, session_factory: sessionmaker = Inject) -> Session:
        return session_factory()
