import urllib.parse
from base64 import urlsafe_b64encode
from itertools import count
from random import randbytes
from time import time
from typing import Any

import sqlalchemy.exc
from fastapi import HTTPException, Query, Depends
from fastapi.responses import RedirectResponse

from soc.auth_helpers import session_cookie
from soc.config.models.site import SiteSettings
from soc.context import create_app, inject
from soc.controllers.authentication import Authentication, AuthenticationSettings
from soc.database import Database
from soc.discord import Discord
from soc.entities.sessions import Session
from soc.entities.users import User

counter = count()

auth_app = create_app()


API = "https://discord.com/api/v10"


def _verify_state(
    state: str = Query(), cookie: dict[str, Any] = Depends(session_cookie)
):
    if cookie["state"] != state:
        raise HTTPException(403, "Invalid state")


@auth_app.get("/discord", dependencies=[Depends(_verify_state)])
async def discord_code_auth(
    code: str = Query(),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    db: Database = inject(Database),
    auth: Authentication = inject(Authentication),
    discord: Discord = inject(Discord),
    session: Session = Depends(session_cookie),
):
    access_token = await discord.get_access_token(code, settings)
    user_data = await discord.get_user_data(access_token)
    try:
        user = await _log_user_in(user_data, db)
    except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ProgrammingError):
        return await _manage_db_redirect(user_data, access_token, auth)
    else:
        return await _home_redirect(user, session)


async def _log_user_in(user_data: dict[str, Any], db: Database) -> User:
    user = await db.users.get_by_email(user_data["email"])
    if user:
        return user

    if user_data.get("avatar"):
        file_type = "gif" if user_data["avatar"].startswith("a_") else "png"
        avatar = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.{file_type}"
    else:
        avatar = f"https://cdn.discordapp.com/embed/avatars/{int(user_data['discriminator']) % 5}.png"

    return await db.users.create(user_data["username"], "", user_data["email"], avatar)


async def _home_redirect(user: User, session: Session) -> RedirectResponse:
    if user.banned:
        raise HTTPException(401, "You've been banned")

    response = RedirectResponse("/")
    session.user_id = user.id
    session["username"] = user.username
    session["roles"] = await user.get_roles()
    await session.sync()
    return response


async def _manage_db_redirect(
    user_data: dict[str, Any], access_token: str, auth: Authentication
) -> RedirectResponse:
    response = RedirectResponse("/admin/db")
    token = auth.create_token(
        type="dbless",
        username=user_data["username"],
        email=user_data["email"],
        access_token=access_token,
    )
    response.set_cookie(
        "sessionid", token, secure=True, expires=7 * 24 * 60 * 60, httponly=True
    )
    return response


@auth_app.get("/discord/login", response_class=RedirectResponse)
async def discord_login(
    auth: Authentication = inject(Authentication),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    site_settings: SiteSettings = inject(SiteSettings),
):
    state = _create_state()
    session_id, session = await auth.create_guest_session(state=state)
    redirect_uri = urllib.parse.quote_plus(settings.discord.redirect_uri)
    response = RedirectResponse(
        f"https://discord.com/api/oauth2/authorize?"
        f"response_type=code&"
        f"client_id={settings.discord.client_id}&"
        f"scope=identify%20email&"
        f"state={state}&"
        f"redirect_uri={redirect_uri}&"
        "prompt=consent"
    )
    response.set_cookie(
        "sessionid",
        session_id,
        secure=not site_settings.dev,
        expires=7 * 24 * 60 * 60,
        httponly=True,
    )
    return response


def _create_state() -> str:
    state = bytearray(int(time()).to_bytes(4, "little"))
    state.extend(next(counter).to_bytes(4, "little"))
    state.extend(randbytes(34))
    return urlsafe_b64encode(state).decode()
