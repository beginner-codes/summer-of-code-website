import json
from typing import Type

import sqlalchemy.exc
from bevy import Bevy, bevy_method, Inject
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from soc.database.models.sessions import SessionModel
from soc.entities.sessions import Session


class Sessions(Bevy):
    def __init__(self):
        self._session_type: Type[Session] = self.bevy.bind(Session)

    @bevy_method
    async def create(
        self,
        session_id: int,
        user_id: int = -1,
        db_session: AsyncSession = Inject,
        **values
    ) -> Session:
        session_model = SessionModel(
            id=session_id, user_id=user_id, values=json.dumps(values)
        )
        async with db_session.begin():
            db_session.add(session_model)

        return self._session_type.from_db_model(session_model)

    @bevy_method
    async def get(
        self, session_id: int, db_session: AsyncSession = Inject
    ) -> Session | None:
        query = select(SessionModel).filter_by(id=session_id)
        async with db_session:
            try:
                cursor = await db_session.execute(query)
            except sqlalchemy.exc.OperationalError:
                return
            else:
                session_model = cursor.scalars().first()

        if not session_model:
            return

        return self._session_type.from_db_model(session_model)

    @bevy_method
    async def set_user(
        self, session_id: int, user_id: int, db_session: AsyncSession = Inject
    ):
        async with db_session.begin():
            statement = (
                update(SessionModel)
                .where(SessionModel.id == session_id)
                .values(user_id=user_id)
            )
            await db_session.execute(statement)
            await db_session.commit()

    @bevy_method
    async def update(
        self, session_id: int, db_session: AsyncSession = Inject, **values
    ):
        async with db_session.begin():
            statement = (
                update(SessionModel)
                .where(SessionModel.id == session_id)
                .values(values=json.dumps(values))
            )
            await db_session.execute(statement)
            await db_session.commit()
