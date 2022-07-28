from typing import Any, Awaitable

import sqlalchemy.exc
from bevy import Bevy, bevy_method, Inject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import update

from soc.database.models.settings import SettingsModel


class Settings(Bevy):
    def __init__(self):
        self._unsynced = {}

    @property
    def synced(self) -> bool:
        return not self._unsynced

    @bevy_method
    async def set(
        self,
        name: str,
        value: list[Any] | dict[str, Any],
        db_session: AsyncSession = Inject,
    ):
        async with db_session.begin():
            await self._add_update_to_session(name, value, db_session)
            await db_session.commit()

    @bevy_method
    async def sync(self, db_session: AsyncSession = Inject):
        async with db_session:
            for name, value in list(self._unsynced.items()):
                await self._add_update_to_session(name, value, db_session)
                del self._unsynced[name]

            await db_session.commit()

    async def _add_update_to_session(
        self, name: str, value: Any, db_session: AsyncSession
    ):
        NOTSET = object()
        existing_value = await self.get(name, NOTSET, use_unsynced_cache=False)
        if existing_value is NOTSET:
            db_session.add(SettingsModel(name=name, value=value))

        else:
            if isinstance(existing_value, dict):
                value = existing_value | value

            await db_session.execute(
                update(SettingsModel)
                .where(SettingsModel.name == name)
                .values(value=value)
            )

    @bevy_method
    async def get(
        self,
        name: str,
        default: Any = None,
        *,
        use_unsynced_cache: bool = True,
        db_session: AsyncSession = Inject,
    ) -> list[Any] | dict[str, Any] | None:
        if use_unsynced_cache and name in self._unsynced:
            return self._unsynced[name]

        return await self._get_from_db(name, default)

    @bevy_method
    async def _get_from_db(
        self, name: str, default: Any = None, db_session: AsyncSession = Inject
    ) -> list[Any] | dict[str, Any] | None:
        async with db_session:
            try:
                cursor = await db_session.execute(
                    select(SettingsModel).where(SettingsModel.name == name)
                )
            except sqlalchemy.exc.OperationalError:
                return default
            else:
                row = cursor.scalars().first()
                return row.value if row else default

    def __getitem__(self, name: str) -> Awaitable[list[Any] | dict[str, Any] | None]:
        return self.get(name)

    def __setitem__(self, name: str, value: list[Any] | dict[str, Any]):
        self._unsynced[name] = value
