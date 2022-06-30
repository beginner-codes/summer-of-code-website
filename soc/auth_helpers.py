from typing import Any

import jwt
from fastapi import Depends, HTTPException, Cookie
from fastapi.security import OAuth2PasswordBearer

from soc.config.models.site import SiteSettings
from soc.context import inject
from soc.controllers.authentication import AuthenticationSettings
from soc.database import Database

auth_scheme = OAuth2PasswordBearer(tokenUrl="authenticate")


async def dev_only(settings: SiteSettings = inject(SiteSettings)):
    if not settings.dev:
        raise HTTPException(404)


def parse_token(token: str, settings: AuthenticationSettings) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt.private_key, settings.jwt.algorithm)
    except jwt.exceptions.InvalidSignatureError:
        return {}


async def validate_session(session, settings, db):
    if not session:
        raise HTTPException(401, "No session")

    if "user_id" not in session and "email" not in session:
        raise HTTPException(403, "Invalid session")

    if "user_id" in session:
        roles = await db.users.get_users_roles(session["user_id"])
        if "admin" not in roles:
            raise HTTPException(403, "Not an admin")

    elif session.get("email") != settings.admin_email:
        raise HTTPException(403, "Not an admin")


async def session_cookie(
    session_token: str | None = Cookie(default=None, alias="sessionid"),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
):
    return parse_token(session_token, settings)


async def validate_session_cookie(
    session: dict[str, Any] = Depends(session_cookie),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    db: Database = inject(Database),
):
    await validate_session(session, settings, db)


async def bearer_token(
    session_token: str = Depends(auth_scheme),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
):
    return parse_token(session_token, settings)


async def validate_bearer_token(
    session: dict[str, Any] = Depends(bearer_token),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    db: Database = inject(Database),
):
    try:
        await validate_session(session, settings, db)
    except HTTPException as http_exc:
        http_exc.headers.setdefault("WWW-Authenticate", "Bearer")
        raise http_exc