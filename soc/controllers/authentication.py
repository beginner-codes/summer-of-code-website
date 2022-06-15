import bcrypt
from bevy import Bevy, Inject
from bevy.providers import bevy_method
from pydantic import Field

from soc.config import BaseSettingsModel
from soc.database import Session
from soc.database.models.users import User


class AuthenticationSettings(BaseSettingsModel):
    __config_key__ = "authentication"

    salt_rounds: int = Field(default=12, env="SOC_AUTH_SALT_ROUNDS")
    salt_prefix: str = Field(default="2b", env="SOC_AUTH_SALT_PREFIX")


class Authentication(Bevy):
    @bevy_method
    async def authenticate_user(
        self, name: str, password: str, session: Session = Inject()
    ) -> User | None:
        async with session.begin():
            result = await session.execute(User.select().where(User.name == name))
            user: User | None = result.scalars().first()

        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            return user

        return None

    @bevy_method
    async def register_user(
        self,
        name: str,
        password: str,
        email: str,
        session: Session = Inject(),
        settings: AuthenticationSettings = Inject(),
    ):
        salt = bcrypt.gensalt(settings.salt_rounds, settings.salt_prefix.encode())
        hashed_password = bcrypt.hashpw(password.encode(), salt).decode()
        async with session.begin():
            session.add(
                User(
                    name=name,
                    password=hashed_password,
                    email=email,
                )
            )

    async def create_access_token(self, user: User) -> str:
        return "ACCESS TOKEN"