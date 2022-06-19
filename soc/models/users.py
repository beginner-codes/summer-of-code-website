from __future__ import annotations

import dataclasses
import datetime

from bevy import Bevy

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
