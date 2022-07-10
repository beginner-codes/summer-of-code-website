from fastapi import Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from soc.auth_helpers import bearer_token, validate_bearer_token
from soc.context import create_app, inject
from soc.controllers.authentication import Authentication
from soc.database import Database
from soc.entities.sessions import Session

api_app = create_app()


@api_app.post("/register")
async def register_user(
    data: OAuth2PasswordRequestForm = Depends(),
    email: str = Form(),
    auth=inject(Authentication),
):
    await auth.register_user(data.username, data.password, email)
    return {"detail": "User successfully registered"}


@api_app.get("/challenges")
async def get_challenges(db: Database = inject(Database)):
    return {"challenges": await db.challenges.get_all()}


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
    submission = await db.challenges.create_submission(
        submission.type,
        submission.link,
        submission.description,
        challenge_id,
        session.user_id,
    )
    return await submission.to_dict()


@api_app.get("/challenges/active")
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
