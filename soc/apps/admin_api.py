import subprocess
from datetime import datetime
from typing import Any

from fastapi import Depends
from pydantic import BaseModel, Field

from soc.auth_helpers import bearer_token, require_roles, validate_bearer_token
from soc.context import create_app, inject
from soc.database import Database
from soc.discord import Discord
from soc.entities.sessions import Session


admin_api = create_app()


@admin_api.get(
    "/db/migrate",
    dependencies=[Depends(validate_bearer_token), Depends(require_roles("ADMIN"))],
)
async def migrate_database(
    session: dict[str, Any] = Depends(bearer_token),
    db: Database = inject(Database),
    discord: Discord = inject(Discord),
):
    output, success = _run_alembic()
    if success and "access_token" in session:
        await _setup_user(session, db, discord)

    return {"output": output, "success": success}


class CreateChallengePayload(BaseModel):
    title: str
    description: str
    start: datetime
    end: datetime


@admin_api.post(
    "/challenges/create",
    dependencies=[Depends(validate_bearer_token), Depends(require_roles("ADMIN"))],
)
async def create_challenge(
    challenge_data: CreateChallengePayload,
    session: Session = Depends(bearer_token),
    db: Database = inject(Database),
):
    data = {"user": session.user_id} | challenge_data.dict()
    data["start"] = data["start"]
    data["end"] = data["end"]
    challenge = await db.challenges.create(**data)
    return await challenge.to_dict()


def _run_alembic() -> (str, bool):
    process = subprocess.Popen(
        ["alembic", "upgrade", "head"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    return (stderr or stdout), process.returncode == 0


async def _setup_user(session: dict[str, Any], db: Database, discord: Discord):
    user = await db.users.get_by_email(session["email"])
    if not user:
        user_data = await discord.get_user_data(session["access_token"])
        user = await db.users.create(user_data["username"], "", user_data["email"])

    roles = await user.get_roles()
    if "ADMIN" not in roles:
        await user.set_roles(["ADMIN", *roles])


class BanRequest(BaseModel):
    ids: list[int] = Field(default_factory=list)


@admin_api.post(
    "/users/ban",
    dependencies=[
        Depends(validate_bearer_token),
        Depends(require_roles("ADMIN", "MOD")),
    ],
)
async def ban_users(bans: BanRequest, db: Database = inject(Database)):
    await db.users.ban(*bans.ids)
    return {"success": True}


@admin_api.post(
    "/users/unban",
    dependencies=[
        Depends(validate_bearer_token),
        Depends(require_roles("ADMIN", "MOD")),
    ],
)
async def unban_users(ban: BanRequest, db: Database = inject(Database)):
    await db.users.unban(*ban.ids)
    return {"success": True}
