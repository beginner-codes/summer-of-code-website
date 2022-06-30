from typing import Any

import jwt
from fastapi import Depends, HTTPException, Cookie
from fastapi.security import OAuth2PasswordBearer
from starlette.status import HTTP_401_UNAUTHORIZED

from soc.config.models.site import SiteSettings
from soc.context import inject
from soc.controllers.authentication import AuthenticationSettings
from soc.database import Database


async def dev_only(settings: SiteSettings = inject(SiteSettings)):
    if not settings.dev:
        raise HTTPException(404)


async def validate_token(token, settings, db):
    if not token:
        raise HTTPException(403, "No session")

    try:
        session = jwt.decode(token, settings.jwt.private_key, settings.jwt.algorithm)
    except jwt.exceptions.InvalidSignatureError:
        session = {}

    if not session or ("user_id" not in session and "email" not in session):
        raise HTTPException(403, "Invalid session")

    if "user_id" in session:
        roles = await db.users.get_users_roles(session["user_id"])
        if "admin" not in roles:
            raise HTTPException(403, "Not an admin")

    elif session.get("email") != settings.admin_email:
        print(repr(session.get("email")), repr(settings.admin_email))
        raise HTTPException(403, "Not an admin")

    return session


async def get_session_from_cookie(
    session_token: str | None = Cookie(default=None, alias="sessionid"),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    db: Database = inject(Database),
):
    return await validate_token(session_token, settings, db)


async def get_session_from_cookie_no_auth(
    session_token: str | None = Cookie(default=None, alias="sessionid"),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    db: Database = inject(Database),
):
    try:
        session = jwt.decode(
            session_token, settings.jwt.private_key, settings.jwt.algorithm
        )
    except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
        return {}
    else:
        return session


async def bearer_token(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="authenticate")),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    db: Database = inject(Database),
):
    return await validate_token(token, settings, db)


def auth_scheme(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="authenticate")),
    settings=inject(AuthenticationSettings),
) -> dict[str, Any]:
    try:
        data = jwt.decode(token, settings.jwt.private_key, settings.jwt.algorithm)
    except jwt.exceptions.DecodeError:
        data = {}

    if data.get("user_id") is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return data
