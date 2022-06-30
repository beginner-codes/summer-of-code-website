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
from soc.context import create_app, inject
from soc.controllers.authentication import Authentication, AuthenticationSettings
from soc.database import Database
from soc.discord import Discord
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
):
    access_token = await discord.get_access_token(code, settings)
    user_data = await discord.get_user_data(access_token)
    try:
        user = await _log_user_in(user_data, db)
    except sqlalchemy.exc.OperationalError:
        return await _manage_db_redirect(user_data, access_token, auth)
    else:
        return await _home_redirect(user, auth)


async def _log_user_in(user_data: dict[str, Any], db: Database) -> User:
    user = await db.users.get_by_email(user_data["email"])
    if user:
        return user

    return await db.users.create(user_data["username"], "", user_data["email"])


async def _home_redirect(user: User, auth: Authentication) -> RedirectResponse:
    if user.banned:
        raise HTTPException(401, "You've been banned")

    response = RedirectResponse("/")
    token = await auth.create_user_access_token(user)
    response.set_cookie("sessionid", token, secure=True)
    return response


async def _manage_db_redirect(
    user_data: dict[str, Any], access_token: str, auth: Authentication
) -> RedirectResponse:
    response = RedirectResponse("/admin/db")
    token = auth.create_token(
        username=user_data["username"],
        email=user_data["email"],
        access_token=access_token,
    )
    response.set_cookie("sessionid", token, secure=True)
    return response


@auth_app.get("/discord/login", response_class=RedirectResponse)
async def discord_login(
    auth: Authentication = inject(Authentication),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
):
    state = _create_state()
    session_id = auth.create_token(type="login", state=state)
    redirect_uri = urllib.parse.quote_plus(settings.discord.redirect_uri)
    response = RedirectResponse(
        f"https://discord.com/api/oauth2/authorize?"
        f"response_type=code&"
        f"client_id={settings.discord.client_id}&"
        f"scope=identify%20email&"
        f"state={state}&"
        f"redirect_uri={redirect_uri}&"
        f"prompt=consent"
    )
    response.set_cookie("sessionid", session_id)
    return response


def _create_state() -> str:
    state = bytearray(int(time()).to_bytes(4, "little"))
    state.extend(next(counter).to_bytes(4, "little"))
    state.extend(randbytes(34))
    return urlsafe_b64encode(state).decode()
