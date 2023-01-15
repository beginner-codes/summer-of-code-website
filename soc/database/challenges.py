from __future__ import annotations

import html
from datetime import datetime, timedelta
from typing import Type

import sqlalchemy.exc
import sqlalchemy.orm
from bevy import Bevy, bevy_method, Inject
from fast_protocol import protocol
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func

import soc.entities.submissions as submissions
from soc.database.models.challenges import ChallengeModel
from soc.database.models.submission_status import SubmissionStatusModel
from soc.database.models.submissions import SubmissionModel
from soc.database.models.users import UserModel
from soc.database.models.votes import VoteModel
from soc.entities.challenges import Challenge
from soc.entities.users import User
from soc.events import Events


IDable = protocol("id")


class Challenges(Bevy):
    def __init__(self):
        self._challenge_type: Type[Challenge] = self.bevy.bind(Challenge)
        self._submission_type: Type[submissions.Submission] = self.bevy.bind(
            submissions.Submission
        )
        self._submission_status_type: Type[
            submissions.SubmissionStatus
        ] = self.bevy.bind(submissions.SubmissionStatus)

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
            title=html.escape(title),
            description=html.escape(description),
            start=start,
            end=end,
            user_id=user.id if isinstance(user, User) else user,
        )
        async with db_session.begin():
            db_session.add(model)

        return self._challenge_type.from_db_model(model)

    @bevy_method
    async def get(self, challenge_id: int) -> Challenge | None:
        query = select(ChallengeModel).filter_by(id=challenge_id)
        model = await self._get_first_query_result(query)
        if not model:
            return

        return self._challenge_type.from_db_model(model)

    async def get_active(self) -> Challenge | None:
        now = datetime.utcnow()
        query = select(ChallengeModel).filter(
            ChallengeModel.start <= now, ChallengeModel.end >= now - timedelta(days=1)
        )
        model = await self._get_first_query_result(query)
        if not model:
            return None

        return self._challenge_type.from_db_model(model)

    async def get_upcoming_challenges(self, limit: int = 10) -> list[Challenge]:
        now = datetime.utcnow()
        query = (
            select(ChallengeModel)
            .where(ChallengeModel.end >= now.date())
            .order_by(ChallengeModel.start.asc())
            .limit(limit)
        )
        challenges = await self._get_query_result(query)
        return [self._challenge_type.from_db_model(model) for model in challenges]

    async def get_all(self, ignore_future: bool = False) -> list[Challenge]:
        query = select(ChallengeModel).order_by(
            ChallengeModel.start, ChallengeModel.end
        )
        if ignore_future:
            query = query.where(ChallengeModel.start <= datetime.utcnow())

        result = await self._get_query_result(query, [])
        return [self._challenge_type.from_db_model(row) for row in result]

    @bevy_method
    async def create_submission(
        self,
        type: str,
        link: str,
        description: str,
        challenge: int | Challenge,
        user: int | User,
        db_session: AsyncSession = Inject,
    ) -> submissions.Submission:
        user_id = user if isinstance(user, int) else user.id
        model = SubmissionModel(
            type=type,
            link=html.escape(link),
            description=html.escape(description),
            user_id=user_id,
            challenge_id=challenge if isinstance(challenge, int) else challenge.id,
        )
        async with db_session.begin():
            db_session.add(model)

        submission = self._submission_type.from_db_model(model)
        submission.status = submissions.SubmissionStatus(
            status=submissions.Status.CREATED,
            user_id=user_id,
            submission_id=submission.id,
        )
        await submission.sync()
        return submission

    @bevy_method
    async def set_submission_status(
        self,
        submission: submissions.Submission | SubmissionModel | int,
        status: submissions.Status,
        user: User | int,
        db_session: AsyncSession = Inject,
        events: Events = Inject,
    ) -> submissions.SubmissionStatus:
        model = SubmissionStatusModel(
            status=status,
            submission_id=submission.id if hasattr(submission, "id") else submission,
            user_id=user if isinstance(user, int) else user.id,
        )
        async with db_session.begin():
            db_session.add(model)

        updated_status = submissions.SubmissionStatus.from_db_model(model)
        await events.dispatch(
            "submission.status.changed",
            await self.get_submission(submission, updated_status)
            if isinstance(submission, int)
            else submission,
        )
        return updated_status

    @bevy_method
    async def add_vote_to_submission(
        self,
        submission: int | submissions.Submission,
        user: int | User,
        emoji: str,
        db_session: AsyncSession = Inject,
    ) -> VoteModel:
        model = VoteModel(
            emoji=emoji, user_id=self.get_id(user), submission=self.get_id(submission)
        )
        async with db_session.begin():
            db_session.add(model)

        return model

    @bevy_method
    async def remove_vote_from_submission(
        self,
        submission: int | submissions.Submission,
        user: int | User,
        emoji: str,
        db_session: AsyncSession = Inject,
    ):
        query = delete(VoteModel).filter_by(
            submission=self.get_id(submission), user_id=self.get_id(user), emoji=emoji
        )
        async with db_session.begin():
            await db_session.execute(query)

    @bevy_method
    async def delete_challenge(
        self, challenge: int | Challenge, db_session: AsyncSession = Inject
    ):
        challenge_id = challenge if isinstance(challenge, int) else challenge.id
        async with db_session.begin():
            await db_session.execute(delete(ChallengeModel).filter_by(id=challenge_id))

    async def get_submission_votes(
        self, submission: int | submissions.Submission
    ) -> list[VoteModel]:
        query = select(VoteModel).filter_by(submission=self.get_id(submission))
        result = await self._get_query_result(query, [])
        return list(result)

    async def get_submission(
        self, submission_id: int, status: SubmissionStatusModel | None = None
    ) -> submissions.Submission | None:
        query = select(SubmissionModel).filter_by(id=submission_id)
        model = await self._get_first_query_result(query)
        return self._submission_type.from_db_model(model, status) if model else None

    async def get_submissions(self, challenge_id: int) -> list[submissions.Submission]:
        query = select(SubmissionModel).filter_by(challenge_id=challenge_id)
        result = await self._get_query_result(query, [])
        return [
            self._submission_type.from_db_model(
                row, await self.get_submission_status(row.id)
            )
            for row in result
        ]

    async def get_submission_status(
        self, submission_id: int
    ) -> submissions.SubmissionStatus | None:
        query = (
            select(SubmissionStatusModel)
            .filter_by(submission_id=submission_id)
            .order_by(SubmissionStatusModel.updated.desc())
        )
        model = await self._get_first_query_result(query)
        return self._submission_status_type.from_db_model(model)

    async def get_submission_created_status(
        self, submission_id: int
    ) -> submissions.SubmissionStatus | None:
        query = select(SubmissionStatusModel).filter_by(
            submission_id=submission_id, status=submissions.Status.CREATED
        )
        model = await self._get_first_query_result(query)
        return self._submission_status_type.from_db_model(model)

    @bevy_method
    async def update_submission(
        self, submission_id: int, description: str, db_session: AsyncSession = Inject
    ):
        async with db_session.begin():
            statement = (
                update(SubmissionModel)
                .where(SubmissionModel.id == submission_id)
                .values(description=html.escape(description))
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
        
        if "description" in changed_fields:
            changed_fields["description"] = html.escape(changed_fields["description"])
        
        if "title" in changed_fields:
            changed_fields["title"] = html.escape(changed_fields["title"])

        async with db_session.begin():
            statement = (
                update(ChallengeModel)
                .where(ChallengeModel.id == challenge_id)
                .values(**changed_fields)
            )
            await db_session.execute(statement)
            await db_session.commit()

    @bevy_method
    async def get_leaderboard(
        self, challenge_id: int, db_session: AsyncSession = Inject
    ) -> sqlalchemy.engine.result.ChunkedIteratorResult:
        async with db_session:
            return await db_session.execute(
                select(
                    UserModel.username, func.count(UserModel.username).label("votes")
                )
                .join(SubmissionModel)
                .join(VoteModel)
                .where(SubmissionModel.challenge_id == challenge_id)
                .group_by(SubmissionModel.user_id, UserModel.username)
            )

    @bevy_method
    async def _get_query_result(
        self,
        query: sqlalchemy.orm.Query,
        default=None,
        db_session: AsyncSession = Inject,
    ):
        async with db_session:
            try:
                cursor = await db_session.execute(query)
            except sqlalchemy.exc.OperationalError:
                return default

            result = cursor.scalars()
            if result is None:
                return default

            return result

    async def _get_first_query_result(self, query: sqlalchemy.orm.Query, default=None):
        NOTSET = object()
        result = await self._get_query_result(query, default=NOTSET)
        if result is NOTSET:
            return default

        return result.first()

    def get_id(self, obj: int | IDable) -> int:
        match obj:
            case IDable():
                return obj.id

            case int():
                return obj

            case _:
                raise ValueError(f"Expected an int or an IDable, got {obj!r}")
