from __future__ import annotations

import datetime
from datetime import datetime
from typing import Awaitable

from bevy import Bevy, bevy_method, Inject

import soc.database
from soc.database.models.challenges import ChallengeModel
from soc.entities.users import User
from soc.state_property import state_property


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
        self._created = created
        self._start = start
        self._end = end
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
