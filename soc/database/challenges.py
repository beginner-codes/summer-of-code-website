from datetime import datetime
from typing import Type

import sqlalchemy.exc
from bevy import Bevy, bevy_method, Inject
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from soc.database.models.challenges import ChallengeModel
from soc.database.models.submission_status import SubmissionStatusModel
from soc.database.models.submissions import SubmissionModel
from soc.entities.challenges import Challenge
from soc.entities.submissions import Submission, Status, SubmissionStatus
from soc.entities.users import User


class Challenges(Bevy):
    def __init__(self):
        self._challenge_type: Type[Challenge] = self.bevy.bind(Challenge)
        self._submission_type: Type[Submission] = self.bevy.bind(Submission)
        self._submission_status_type: Type[SubmissionStatus] = self.bevy.bind(
            SubmissionStatus
        )

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
    async def create_submission(
        self,
        type: str,
        link: str,
        description: str,
        challenge: int | Challenge,
        user: int | User,
        db_session: AsyncSession = Inject,
    ) -> Submission:
        user_id = user if isinstance(user, int) else user.id
        model = SubmissionModel(
            type=type,
            link=link,
            description=description,
            user_id=user_id,
            challenge_id=challenge if isinstance(challenge, int) else challenge.id,
        )
        async with db_session.begin():
            db_session.add(model)

        submission = self._submission_type.from_db_model(model)
        submission.status = SubmissionStatus(
            status=Status.CREATED, user_id=user_id, submission_id=submission.id
        )
        await submission.sync()
        return submission

    @bevy_method
    async def set_submission_status(
        self,
        submission: Submission | SubmissionModel,
        status: Status,
        user: User | int,
        db_session: AsyncSession = Inject,
    ):
        model = SubmissionStatusModel(
            status=status,
            submission_id=submission.id,
            user_id=user if isinstance(user, int) else user.id,
        )
        async with db_session.begin():
            db_session.add(model)

    @bevy_method
    async def get_submissions(
        self, challenge_id: int, session: AsyncSession = Inject
    ) -> list[Submission]:
        query = select(SubmissionModel).filter_by(challenge_id=challenge_id)
        async with session:
            cursor = await session.execute(query)
            return [
                self._submission_type.from_db_model(
                    row, await self.get_submission_status(row.id)
                )
                for row in cursor.scalars()
            ]

    @bevy_method
    async def get_submission_status(
        self, submission_id: int, db_session: AsyncSession = Inject
    ) -> SubmissionStatus | None:
        query = select(SubmissionStatusModel).order_by(
            SubmissionStatusModel.updated.desc()
        )
        async with db_session:
            try:
                cursor = await db_session.execute(query)
            except sqlalchemy.exc.OperationalError:
                return
            else:
                model = cursor.scalars().first()

        return self._submission_status_type.from_db_model(model)

    @bevy_method
    async def update_submission(
        self, submission_id: int, description: str, db_session: AsyncSession = Inject
    ):
        async with db_session.begin():
            statement = (
                update(SubmissionModel)
                .where(SubmissionModel.id == submission_id)
                .values(description=description)
            )
            await db_session.execute(statement)
            await db_session.commit()

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
