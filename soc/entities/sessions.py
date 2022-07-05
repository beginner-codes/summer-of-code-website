from __future__ import annotations

import datetime
import json
from collections.abc import MutableMapping
from datetime import datetime
from typing import Any

from bevy import Bevy, bevy_method, Inject

import soc.database
from soc.database.models.sessions import SessionModel
from soc.state_property import state_property


class Session(MutableMapping, Bevy):
    user_id, _user_id, _user_id_state = state_property(int)
    revoked, _revoked, _revoked_state = state_property(bool)

    def __init__(
        self,
        id: int,
        user_id: int,
        revoked: bool,
        created: datetime,
        values: dict[str, Any],
    ):
        self._id = id
        self._user_id = user_id
        self._revoked = revoked
        self._created = created
        self._values = values
        self._values_changed = False

    def __delitem__(self, key):
        del self._values[key]
        self._values_changed = True

    def __eq__(self, other):
        return isinstance(other, type(self)) and other.id == self.id

    def __getitem__(self, item):
        return self._values[item]

    def __hash__(self):
        return id(self.id)

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __repr__(self):
        return (
            f"{type(self).__name__}({self._id}, {self._user_id}, {self._revoked}, {self._created.isoformat() if self._created else None!r}, "
            f"**{self._values})"
        )

    def __setitem__(self, key, value):
        self._values[key] = value
        self._values_changed = True

    @property
    def id(self) -> int:
        return self._id

    @property
    def created(self) -> datetime:
        return self._created

    @property
    def empty(self) -> bool:
        return self.user_id == -1 and not self._values

    @bevy_method
    async def sync(self, db: soc.database.Database = Inject):
        if self._values_changed:
            await db.sessions.update(self.id, **self._values)
            self._values_changed = False

        if self._user_id_state.changed:
            await db.sessions.set_user(self.id, self.user_id)
            self._user_id_state.changed = False

        if self._revoked_state.changed:
            await db.sessions.revoke(self.id)
            self._revoked_state.changed = False

    @classmethod
    def from_db_model(cls, model: SessionModel) -> Session:
        return cls(
            id=model.id,
            user_id=model.user_id,
            revoked=model.revoked,
            created=model.created,
            values=json.loads(model.values),
        )
