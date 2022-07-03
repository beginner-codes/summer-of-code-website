from typing import Any

import jwt
from fastapi import Depends, HTTPException, Cookie
from fastapi.security import OAuth2PasswordBearer

from soc.config.models.site import SiteSettings
from soc.context import inject
from soc.controllers.authentication import AuthenticationSettings
from soc.database import Database
from soc.entities.sessions import Session

auth_scheme = OAuth2PasswordBearer(tokenUrl="authenticate")


async def dev_only(settings: SiteSettings = inject(SiteSettings)):
    if not settings.dev:
        raise HTTPException(404)


def require_roles(*roles):
    roles = set(roles)

    async def roles_check(
        session: dict[str, Any] = Depends(session_cookie),
        db: Database = inject(Database),
        settings: AuthenticationSettings = inject(AuthenticationSettings),
    ):
        if "email" in session:
            roles_match = session["email"] == settings.admin_email

        else:
            await validate_session(session, settings, db)
            user = await db.users.get_by_id(session.user_id)
            user_roles = set(await user.get_roles())
            roles_match = bool(user_roles & roles)

        if not roles_match:
            raise HTTPException(403, "You must be a mod or admin to access this")

    return roles_check


def parse_token(token: str, settings: AuthenticationSettings) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt.private_key, settings.jwt.algorithm)
    except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
        return {}


async def validate_session(session: Session | None, settings, db):
    if not session or session.empty:
        raise HTTPException(401, "No session")

    if session.user_id == -1 and "email" not in session:
        print(session)
        raise HTTPException(403, "Invalid session")

    if session.user_id != -1:
        roles = await db.users.get_roles(session.user_id)

    elif session.get("email") != settings.admin_email:
        raise HTTPException(403, "Not an admin")


async def get_session_data(session_info: dict[str, Any], db: Database) -> Session:
    return await db.sessions.get(session_info.get("session_id", -1))


async def session_cookie(
    session_token: str | None = Cookie(default=None, alias="sessionid"),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    db: Database = inject(Database),
):
    session_info = parse_token(session_token, settings)
    if session_info.get("type") == "dbless":
        return Session(-1, -1, False, None, session_info)

    data = await get_session_data(session_info, db)
    return data


async def validate_session_cookie(
    session: Session = Depends(session_cookie),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    db: Database = inject(Database),
):
    await validate_session(session, settings, db)


async def bearer_token(
    session_token: str = Depends(auth_scheme),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    db: Database = inject(Database),
):
    session_info = parse_token(session_token, settings)
    if session_info.get("type") == "dbless":
        return Session(-1, -1, False, None, session_info)

    return await get_session_data(session_info, db)


async def validate_bearer_token(
    session: Session = Depends(bearer_token),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    db: Database = inject(Database),
):
    try:
        await validate_session(session, settings, db)
    except HTTPException as http_exc:
        if not http_exc.headers:
            http_exc.headers = {}

        http_exc.headers.setdefault("WWW-Authenticate", "Bearer")
        raise http_exc
