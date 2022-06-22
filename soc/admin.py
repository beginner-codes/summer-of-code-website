from typing import Any

import jwt
from fastapi import FastAPI, HTTPException, Depends, Cookie
from fastapi.responses import HTMLResponse

from soc.auth_scheme import AuthenticationSettings
from soc.context import inject
from soc.database import Database

admin_app = FastAPI()


async def check_cookie(
    session_token: str | None = Cookie(default=None, alias="sessionid"),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    db: Database = inject(Database),
):
    if not session_token:
        raise HTTPException(403, "No session")

    try:
        session = jwt.decode(
            session_token, settings.jwt.private_key, settings.jwt.algorithm
        )
    except jwt.exceptions.InvalidSignatureError:
        session = {}

    if not session or ("user_id" not in session and "email" not in session):
        raise HTTPException(403, "Invalid session")

    if "user_id" in session:
        roles = await db.users.get_users_roles(session["user_id"])
        if "admin" not in roles:
            raise HTTPException(403, "Not an admin")

    elif session.get("email") != settings.admin_email:
        raise HTTPException(403, "Not an admin")

    return session


@admin_app.get("/db", response_class=HTMLResponse)
async def manage_db(cookie: dict[str, Any] = Depends(check_cookie)):
    return "Hello World"
