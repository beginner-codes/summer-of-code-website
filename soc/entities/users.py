from __future__ import annotations

import datetime
from typing import Any

import pydantic
from bevy import Bevy, bevy_method, Inject

import soc.database
from soc.database.models.users import UserModel


class User(pydantic.BaseModel, Bevy):
    id: int = pydantic.Field()
    username: str
    email: str
    password: str
    avatar: str | None
    joined: datetime.datetime
    banned: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.avatar = (
            self.avatar
            or "/static/res/account_circle_FILL0_wght400_GRAD0_opsz48-white.png"
        )

    def __hash__(self):
        return id(self.id)

    def __eq__(self, other):
        return isinstance(other, type(self)) and other.id == self.id

    @bevy_method
    async def get_roles(self, db: soc.database.Database = Inject) -> list[str]:
        return await db.users.get_roles(self.id)

    @bevy_method
    async def set_roles(self, roles: list[str], db: soc.database.Database = Inject):
        await db.users.set_roles(self.id, roles)

    @bevy_method
    async def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "avatar": self.avatar,
            "joined": self.joined.isoformat(),
            "banned": self.banned,
            "roles": await self.get_roles(),
        }

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
