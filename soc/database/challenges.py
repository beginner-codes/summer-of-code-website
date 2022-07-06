from datetime import datetime
from typing import Type

import sqlalchemy.exc
from bevy import Bevy, bevy_method, Inject
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from soc.database.models.challenges import ChallengeModel
from soc.entities.challenges import Challenge
from soc.entities.users import User


class Challenges(Bevy):
    def __init__(self):
        self._challenge_type: Type[Challenge] = self.bevy.bind(Challenge)

    @bevy_method
    async def create(
        self,
        title: str,
        description: str,
        start: datetime,
        end: datetime,
        user: int | User,
        db_session: AsyncSession = Inject,
    ) -> Challenge:
        model = ChallengeModel(
            title=title,
            description=description,
            start=start,
            end=end,
            user_id=user.id if isinstance(user, User) else user,
        )
        async with db_session.begin():
            db_session.add(model)

        return self._challenge_type.from_db_model(model)

    @bevy_method
    async def get(
        self, challenge_id: int, db_session: AsyncSession = Inject
    ) -> Challenge | None:
        query = select(ChallengeModel).filter_by(id=challenge_id)
        async with db_session:
            try:
                cursor = await db_session.execute(query)
            except sqlalchemy.exc.OperationalError:
                return
            else:
                model = cursor.scalars().first()

        if not model:
            return

        return self._challenge_type.from_db_model(model)

    @bevy_method
    async def get_active(self, db_session: AsyncSession = Inject) -> Challenge | None:
        now = datetime.utcnow()
        query = select(ChallengeModel).filter(
            ChallengeModel.start <= now, ChallengeModel.end >= now
        )
        async with db_session:
            try:
                cursor = await db_session.execute(query)
            except sqlalchemy.exc.OperationalError:
                return
            else:
                model = cursor.scalars().first()

        if not model:
            return

        return self._challenge_type.from_db_model(model)

    @bevy_method
    async def get_all(self, session: AsyncSession = Inject) -> list[Challenge]:
        query = select(ChallengeModel).order_by(
            ChallengeModel.start, ChallengeModel.end
        )
        async with session:
            cursor = await session.execute(query)
            return [self._challenge_type.from_db_model(row) for row in cursor.scalars()]

    @bevy_method
    async def update(
        self, challenge_id: int, db_session: AsyncSession = Inject, **fields
    ):
        disallowed_fields = {"created", "id", "user_id"}
        changed_fields = {
            field_name: field_value
            for field_name, field_value in fields.items()
            if field_name not in disallowed_fields
        }

        async with db_session.begin():
            statement = (
                update(ChallengeModel)
                .where(ChallengeModel.id == challenge_id)
                .values(**changed_fields)
            )
            await db_session.execute(statement)
            await db_session.commit()
