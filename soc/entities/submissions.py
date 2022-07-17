from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable

from bevy import Bevy, bevy_method, Inject

import soc.database
from soc.database.models.submission_status import SubmissionStatusModel
from soc.database.models.submissions import SubmissionModel
from soc.entities.users import User
from soc.state_property import state_property
from soc.strenum import StrEnum, auto


class Status(StrEnum):
    CREATED = auto()
    APPROVED = auto()
    DISAPPROVED = auto()
    NONE = auto()


@dataclass(frozen=True)
class SubmissionStatus:
    status: Status
    user_id: int
    submission_id: int
    id: int = -1
    updated: datetime = datetime.fromtimestamp(0)

    @property
    def valid(self) -> bool:
        return self.id != -1

    async def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "updated": self.updated,
            "status": self.status,
            "user_id": self.user_id,
            "submission_id": self.submission_id,
        }

    @classmethod
    def from_db_model(cls, model: SubmissionStatusModel | SubmissionStatus | None) -> SubmissionStatus:
        match model:
            case SubmissionStatusModel():
                return SubmissionStatus(
                    Status(model.status),
                    model.user_id,
                    model.submission_id,
                    model.id,
                    model.updated,
                )

            case SubmissionStatus():
                return model

            case _:
                return SubmissionStatus(
                    Status.NONE, -1, -1, -1, datetime.fromtimestamp(0)
                )


class Submission(Bevy):
    description, _description, _description_state = state_property(str)
    status, _status, _status_state = state_property(SubmissionStatus)

    def __init__(
        self,
        id: int,
        type: str,
        link: str,
        description: str,
        user_id: int,
        challenge_id: int,
        status: SubmissionStatus | None = None,
    ):
        self._id = id
        self._type = type
        self._description = description
        self._link = link
        self._user_id = user_id
        self._challenge_id = challenge_id
        self._status = status

    def __hash__(self):
        return self.id

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"{self._id}, "
            f"{self._type!r}, "
            f"{self._description!r}, "
            f"{self._link!r}, "
            f"{self._user_id},"
            f"{self._challenge_id}, "
            f"{self._status})"
        )

    @property
    def changed(self) -> bool:
        return self._description_state.changed or self._status_state.changed

    @property
    @bevy_method
    def created_by(self, db: soc.database.Database = Inject) -> Awaitable[User]:
        return db.users.get_by_id(self._user_id)

    @property
    def id(self) -> int:
        return self._id

    @property
    def type(self) -> str:
        return self._type

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def votes(self) -> Awaitable[dict[str, set[int]]]:
        return self._build_votes_dict()

    @bevy_method
    async def _build_votes_dict(self, db: soc.database.Database = Inject) -> dict[str, set[int]]:
        user_votes = await db.challenges.get_submission_votes(self)
        votes = defaultdict(set)
        for vote in user_votes:
            votes[vote.emoji].add(vote.user_id)

        return votes

    @bevy_method
    async def add_vote(self, user: int | User, emoji: str, db: soc.database.Database = Inject):
        await db.challenges.add_vote_to_submission(self.id, user, emoji)

    @bevy_method
    async def remove_vote(self, user: int | User, emoji: str, db: soc.database.Database = Inject):
        await db.challenges.remove_vote_from_submission(self.id, user, emoji)

    @bevy_method
    async def sync(self, db: soc.database.Database = Inject):
        if not self.changed:
            return

        if self._description_state.changed:
            await db.challenges.update_submission(self._description)
            self._description_state.changed = False

        if self._status_state.changed:
            self._status = await db.challenges.set_submission_status(
                self, self._status.status, self._status.user_id
            )
            self._status_state.changed = False

    async def to_dict(self, expand_user: bool = False) -> dict[str, Any]:
        data = {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "link": self._link,
            "user_id": self._user_id,
            "challenge_id": self._challenge_id,
            "status": await self.status.to_dict(),
            "votes": await self.votes,
            "created_by": await (await self.created_by).to_dict() if expand_user else None
        }
        return data

    @classmethod
    def from_db_model(
        cls, model: SubmissionModel, status: SubmissionStatus | None = None
    ) -> Submission:
        return cls(
            id=model.id,
            type=model.type,
            description=model.description,
            link=model.link,
            user_id=model.user_id,
            challenge_id=model.challenge_id,
            status=SubmissionStatus.from_db_model(status),
        )
