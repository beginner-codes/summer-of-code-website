from __future__ import annotations

from typing import Any, Awaitable

from bevy import bevy_method, Inject

import soc.database
from soc.database.models.submissions import SubmissionModel
from soc.entities.users import User
from soc.state_property import state_property


class Submission:
    description, _description, _description_state = state_property(str)

    def __init__(
        self,
        id: int,
        type: str,
        link: str,
        description: str,
        user_id: int,
        challenge_id: int,
    ):
        self._id = id
        self._type = type
        self._description = description
        self._link = link
        self._user_id = user_id
        self._challenge_id = challenge_id

    def __hash__(self):
        return id(self.id)

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"{self._id}, "
            f"{self._type!r}, "
            f"{self._description!r}, "
            f"{self._link!r}, "
            f"{self._user_id},"
            f"{self._challenge_id})"
        )

    @property
    def changed(self) -> bool:
        return self._description_state.changed

    @property
    @bevy_method
    def created_by(self, db: soc.database.Database = Inject) -> Awaitable[User]:
        return db.users.get_by_id(self._user_id)

    @property
    def id(self) -> int:
        return self._id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    @bevy_method
    def submissions(
        self, db: soc.database.Database = Inject
    ) -> Awaitable[list[Submission]]:
        return db.challenges.get_submissions(self.id)

    @bevy_method
    async def sync(self, db: soc.database.Database = Inject):
        if not self.changed:
            return

        await db.challenges.update_submission(self._description)

    async def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "link": self._link,
            "user_id": self._user_id,
            "challenge_id": self._challenge_id,
        }

    @classmethod
    def from_db_model(cls, model: SubmissionModel) -> Submission:
        return cls(
            id=model.id,
            type=model.type,
            description=model.description,
            link=model.link,
            user_id=model.user_id,
            challenge_id=model.challenge_id,
        )
