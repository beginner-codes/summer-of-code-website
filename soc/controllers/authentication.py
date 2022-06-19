from typing import TypedDict

import bcrypt
import jwt
from bevy import Bevy, Inject
from bevy.providers import bevy_method
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from soc.config import BaseSettingsModel
from soc.database.models.users import UserModel


class AuthTokenDict(TypedDict):
    user_id: int
    username: str


class JWTSettings(BaseSettingsModel):
    private_key: str = Field(default=None, env="SOC_JWT_PRIVATE_KEY")
    public_key: str = Field(default=None, env="SOC_JWT_PUBLIC_KEY")
    algorithm: str = Field(default="HS256", env="SOC_JWT_ALGORITHM")


class AuthenticationSettings(BaseSettingsModel):
    __config_key__ = "authentication"

    salt_rounds: int = Field(default=12, env="SOC_AUTH_SALT_ROUNDS")
    salt_prefix: bytes = Field(default=b"2b", env="SOC_AUTH_SALT_PREFIX")
    jwt: JWTSettings = Field(default_factory=JWTSettings)


class Authentication(Bevy):
    @bevy_method
    async def authenticate_user(
        self, name: str, password: str, session: AsyncSession = Inject()
    ) -> UserModel | None:
        async with session.begin():
            result = await session.execute(UserModel.select(username=name))
            user: UserModel | None = result.scalars().first()

        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            return user

        return None

    @bevy_method
    async def register_user(
        self,
        name: str,
        password: str,
        email: str,
        settings: AuthenticationSettings = Inject(),
    ):
        salt = bcrypt.gensalt(settings.salt_rounds, settings.salt_prefix)
        hashed_password = bcrypt.hashpw(password.encode(), salt).decode()
        await self._create_user(name, email, hashed_password)

    @bevy_method
    async def _create_user(
        self,
        name: str,
        email: str,
        hashed_password: str,
        session: AsyncSession = Inject,
    ):
        async with session.begin():
            session.add(
                UserModel(
                    username=name,
                    password=hashed_password,
                    email=email,
                )
            )

    @bevy_method
    async def create_access_token(
        self, user: UserModel, settings: AuthenticationSettings = Inject
    ) -> str:
        return jwt.encode(
            {"user_id": user.id, "username": user.username}, settings.jwt.private_key
        )
