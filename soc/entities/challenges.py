from __future__ import annotations

import dataclasses
import datetime
from datetime import datetime, timedelta
from typing import Any, Awaitable

import pendulum
from bevy import Bevy, bevy_method, Inject

import soc.database
import soc.entities.submissions as submissions
from soc.database.models.challenges import ChallengeModel
from soc.entities.users import User
from soc.state_property import state_property


@dataclasses.dataclass
class LeaderboardEntry:
    username: str
    votes: int


class Challenge(Bevy):
    title, _title, _title_state = state_property(str)
    description, _description, _description_state = state_property(str)
    start, _start, _start_state = state_property(datetime)
    end, _end, _end_state = state_property(datetime)

    def __init__(
        self,
        id: int,
        title: str,
        description: str,
        created: datetime,
        start: datetime,
        end: datetime,
        user_id: int,
    ):
        self._id = id
        self._title = title
        self._description = description
        self._created = pendulum.instance(created)
        self._start = pendulum.instance(start)
        self._end = pendulum.instance(end)
        self._user_id = user_id

    def __hash__(self):
        return id(self.id)

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"{self._id}, "
            f"{self._title!r}, "
            f"{self._description!r}, "
            f"{self._created.isoformat() if self._created else None!r}, "
            f"{self._start.isoformat() if self._start else None!r}, "
            f"{self._end.isoformat() if self._end else None!r}, "
            f"{self._user_id})"
        )

    @property
    def active(self) -> bool:
        return self.start <= pendulum.now() < self.end + timedelta(days=1)

    @property
    def changed(self) -> bool:
        return (
            self._title_state.changed
            or self._description_state.changed
            or self._start_state.changed
            or self._end_state.changed
        )

    @property
    def created(self) -> datetime:
        return self._created

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
    ) -> Awaitable[list[submissions.Submission]]:
        return db.challenges.get_submissions(self.id)

    @bevy_method
    async def delete(self, db: soc.database.Database = Inject):
        await db.challenges.delete_challenge(self)

    @bevy_method
    async def get_leaderboard(
        self, db: soc.database.Database = Inject
    ) -> list[LeaderboardEntry]:
        return [
            LeaderboardEntry(entry.username, entry.votes)
            for entry in await db.challenges.get_leaderboard(self.id)
        ]

    @bevy_method
    async def sync(self, db: soc.database.Database = Inject):
        if not self.changed:
            return

        changes = {}
        if self._title_state.changed:
            changes["title"] = self._title
            self._title_state.changed = False

        if self._description_state.changed:
            changes["description"] = self._description
            self._description_state.changed = False

        if self._start_state.changed:
            changes["start"] = self._start
            self._start_state.changed = False

        if self._end_state.changed:
            changes["end"] = self._end
            self._end_state.changed = False

        await db.challenges.update(**changes)

    async def to_dict(self, expand_submissions: bool = False) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created": self.created.date(),
            "start": self.start.date(),
            "end": self.end.date(),
            "user": await (await self.created_by).to_dict(),
            "active": self.active,
            "submissions": [
                await submission.to_dict(expand_user=expand_submissions)
                for submission in await self.submissions
            ],
        }

    @classmethod
    def from_db_model(cls, model: ChallengeModel) -> Challenge:
        return cls(
            id=model.id,
            title=model.title,
            description=model.description,
            created=model.created,
            start=model.start,
            end=model.end,
            user_id=model.user_id,
        )
