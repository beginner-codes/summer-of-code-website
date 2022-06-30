from __future__ import annotations

import dataclasses
import datetime

from bevy import Bevy, bevy_method, Inject

import soc.database
from soc.database.models.users import UserModel


@dataclasses.dataclass
class User(Bevy):
    id: int
    username: str
    email: str
    password: str
    avatar: str | None
    joined: datetime.datetime
    banned: bool

    @bevy_method
    async def get_roles(self, db: soc.database.Database = Inject) -> list[str]:
        return await db.users.get_roles(self.id)

    @bevy_method
    async def set_roles(self, roles: list[str], db: soc.database.Database = Inject):
        await db.users.set_roles(self.id, roles)

    @classmethod
    def from_db_model(cls, model: UserModel) -> User:
        return cls(
            id=model.id,
            username=model.username,
            email=model.email,
            password=model.password,
            avatar=model.avatar,
            joined=model.joined,
            banned=model.banned,
        )
