from typing import Type

from bevy import Bevy, Inject
from bevy.providers.function_provider import bevy_method
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from soc.database.models.roles import RoleModel
from soc.database.models.users import UserModel
from soc.entities.users import User


class Users(Bevy):
    def __init__(self):
        self._user_type: Type[User] = self.bevy.bind(User)

    @bevy_method
    async def create(
        self,
        username: str,
        password: str,
        email: str,
        avatar: str | None = None,
        session: AsyncSession = Inject,
    ) -> User:
        user_model = UserModel(
            username=username, password=password, email=email, avatar=avatar
        )
        async with session.begin():
            session.add(user_model)

        return self._user_type.from_db_model(user_model)

    async def get_by_email(self, email: str) -> User | None:
        return await self.get_by(email=email)

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.get_by(id=user_id)

    async def get_by_name(self, username: str) -> User | None:
        return await self.get_by(username=username)

    @bevy_method
    async def get_by(self, session: AsyncSession = Inject, **fields) -> User | None:
        query = select(UserModel).filter_by(**fields)
        async with session:
            cursor = await session.execute(query)
            user_model = cursor.scalars().first()

        if not user_model:
            return

        return self._user_type.from_db_model(user_model)

    @bevy_method
    async def get_roles(
        self, user_id: int, session: AsyncSession = Inject
    ) -> list[str]:
        query = select(RoleModel).filter_by(user_id=user_id)
        async with session:
            cursor = await session.execute(query)
            return [row.type for row in cursor.scalars()]

    @bevy_method
    async def set_roles(
        self,
        user_id: int,
        roles: list[str],
        session: AsyncSession = Inject,
    ):
        async with session.begin():
            for role in roles:
                session.add(RoleModel(type=role, user_id=user_id))
