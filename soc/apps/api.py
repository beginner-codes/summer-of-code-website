from fastapi import Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from soc.auth_helpers import bearer_token, validate_bearer_token
from soc.context import create_app, inject
from soc.controllers.authentication import Authentication
from soc.database import Database
from soc.entities.sessions import Session
from soc.rate_limiting import RateLimitMiddleware

api_app = create_app()
api_app.middleware("http")(RateLimitMiddleware(api_app))


@api_app.post("/register")
async def register_user(
    data: OAuth2PasswordRequestForm = Depends(),
    email: str = Form(),
    auth=inject(Authentication),
):
    await auth.register_user(data.username, data.password, email)
    return {"detail": "User successfully registered"}


@api_app.get("/challenges", dependencies=[Depends(validate_bearer_token)])
async def get_challenges(db: Database = inject(Database)):
    return {
        "challenges": [
            await challenge.to_dict() for challenge in await db.challenges.get_all()
        ]
    }


class CreateSubmissionPayload(BaseModel):
    description: str
    link: str
    type: str


@api_app.post(
    "/challenges/{challenge_id}/submissions/create",
    dependencies=[Depends(validate_bearer_token)],
)
async def create_submission(
    challenge_id: int,
    submission: CreateSubmissionPayload,
    session: Session = Depends(bearer_token),
    db: Database = inject(Database),
):
    challenge = await db.challenges.get(challenge_id)
    if not challenge.active:
        raise HTTPException(
            400, f"{challenge.title} is no longer open for new submissions."
        )

    submission = await db.challenges.create_submission(
        submission.type,
        submission.link,
        submission.description,
        challenge_id,
        session.user_id,
    )
    return await submission.to_dict()


class VotePayload(BaseModel):
    emoji: str


@api_app.post(
    "/challenges/{challenge_id}/submissions/{submission_id}/vote",
    dependencies=[Depends(validate_bearer_token)],
)
async def add_vote(
    submission_id: int,
    vote: VotePayload,
    session: Session = Depends(bearer_token),
    db: Database = inject(Database),
):
    submission = await db.challenges.get_submission(submission_id)
    if not submission:
        raise HTTPException(400, f"No such submission")

    await submission.add_vote(session.user_id, vote.emoji)


@api_app.delete(
    "/challenges/{challenge_id}/submissions/{submission_id}/vote",
    dependencies=[Depends(validate_bearer_token)],
)
async def delete_vote(
    submission_id: int,
    vote: VotePayload,
    session: Session = Depends(bearer_token),
    db: Database = inject(Database),
):
    submission = await db.challenges.get_submission(submission_id)
    if not submission:
        raise HTTPException(400, f"No such submission")

    await submission.remove_vote(session.user_id, vote.emoji)


@api_app.get("/challenges/active", dependencies=[Depends(validate_bearer_token)])
async def get_active_challenge(db: Database = inject(Database)):
    active_challenge = await db.challenges.get_active()
    return {"challenge": await active_challenge.to_dict() if active_challenge else None}


@api_app.post("/authenticate")
async def authenticate_user(
    data: OAuth2PasswordRequestForm = Depends(),
    auth: Authentication = inject(Authentication),
):
    user = await auth.authenticate_user(data.username, data.password)
    if user:
        token, _ = await auth.create_user_session(user)
        return {"access_token": token}
    else:
        raise HTTPException(403, "Invalid user")
