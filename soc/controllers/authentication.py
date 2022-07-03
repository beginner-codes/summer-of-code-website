import os
import threading
from datetime import datetime
from itertools import count
from time import time

import bcrypt
import jwt
import sqlalchemy.exc
from bevy import Bevy, Inject
from bevy.providers import bevy_method

from soc.config.models.authentication import AuthenticationSettings
from soc.config.models.site import SiteSettings
from soc.database import Database
from soc.database.models.users import UserModel
from soc.entities.sessions import Session
from soc.entities.users import User


class Authentication(Bevy):
    def __init__(self):
        self._counter = count()
        self._counter_lock = threading.Lock()

    @bevy_method
    async def authenticate_user(
        self, name: str, password: str, database: Database = Inject
    ) -> User | None:
        user = await database.users.get_by_name(name)
        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            return user

        return None

    @bevy_method
    async def register_user(
        self,
        name: str,
        password: str,
        email: str,
        settings: AuthenticationSettings = Inject,
        database: Database = Inject,
    ):
        salt = bcrypt.gensalt(settings.salt_rounds, settings.salt_prefix)
        hashed_password = bcrypt.hashpw(password.encode(), salt).decode()
        await database.users.create(name, hashed_password, email)

    @bevy_method
    async def create_user_session(
        self, user: User | UserModel, db: Database = Inject
    ) -> (str, Session):
        session_id = self._create_session_id()
        session = await db.sessions.create(session_id, user.id, username=user.username)
        token = self.create_token(session_id=session_id)
        return token, session

    @bevy_method
    def create_token(self, _settings: AuthenticationSettings = Inject, **data) -> str:
        return jwt.encode(
            data | {"created": int(datetime.now().timestamp())},
            _settings.jwt.private_key,
            _settings.jwt.algorithm,
        )

    @bevy_method
    def _create_session_id(self, site_settings: SiteSettings = Inject) -> int:
        """Creates a bigint that encodes the timestamp, process ID, and a local counter."""
        sections = [
            self._int_to_bytes(int(time()), 4),
            self._int_to_bytes(os.getpid(), 2),
            self._int_to_bytes(self._get_next_counter_value(), 2),
        ]
        if site_settings.dev:
            sections = sections[:1]

        id_bytes = bytearray()
        for section in sections:
            id_bytes.extend(section)

        return int.from_bytes(id_bytes, "big")

    def _get_next_counter_value(self) -> int:
        """Gets the next value from the local counter. This method is thread safe."""
        with self._counter_lock:
            return next(self._counter)

    def _int_to_bytes(self, value: int, num_bytes: int) -> bytes:
        """Takes an integer and masks it to a set number of bytes before converting it to a bytes type."""
        limit = 2 ** (num_bytes * 8)
        return (value % limit).to_bytes(num_bytes, "little")
