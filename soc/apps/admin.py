import subprocess
from typing import Any

from fastapi import Depends, Query
from fastapi.responses import HTMLResponse

from soc.auth_helpers import (
    bearer_token,
    dev_only,
    session_cookie,
    validate_bearer_token,
    validate_session_cookie,
)
from soc.context import create_app, inject
from soc.controllers.authentication import Authentication
from soc.database import Database
from soc.discord import Discord
from soc.templates.jinja import Jinja2
from soc.templates.response import TemplateResponse

admin_app = create_app()


@admin_app.get("/api/v1/db/migrate", dependencies=[Depends(validate_bearer_token)])
async def migrate_database(
    session: dict[str, Any] = Depends(bearer_token),
    db: Database = inject(Database),
    discord: Discord = inject(Discord),
):
    output, success = _run_alembic()
    if success:
        await _setup_user(session, db, discord)

    return {"output": output, "success": success}


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


@admin_app.get(
    "/db",
    response_class=TemplateResponse,
    dependencies=[Depends(validate_session_cookie)],
)
async def manage_db(session: dict[str, Any] = Depends(session_cookie)):
    return "manage_db.html", {"email": session["email"]}


@admin_app.get("/login", response_class=HTMLResponse, dependencies=[Depends(dev_only)])
async def login(
    role: str = Query("ADMIN"),
    template: Jinja2 = inject(Jinja2),
    auth: Authentication = inject(Authentication),
    db: Database = inject(Database),
):
    user = await db.users.get_by_id(1)
    if not user:
        user = await db.users.create("Test User", "", "testuser@beginner.codes")

    role = role.upper()
    roles = await user.get_roles()
    if role not in roles:
        await user.set_roles([role, *roles])

    token = auth.create_user_access_token(user)
    response = HTMLResponse(template("login.html"))
    response.set_cookie("sessionid", token)
    return response
