import urllib.parse
from typing import Any

import sqlalchemy.exc
from fastapi import Cookie, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse

from soc.context import create_app, inject
from soc.controllers.authentication import Authentication, AuthenticationSettings
from soc.database import Database
from soc.discord import Discord
from soc.entities.users import User

auth_app = create_app()


API = "https://discord.com/api/v10"


def _verify_state(
    cookie: str = Cookie(default="", alias="sessionid"), state: str = Query()
):
    if cookie != state:
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
    user = await _create_user(user_data, db)
    return (
        _home_redirect(user, auth)
        if user
        else _manage_db_redirect(user_data, access_token, auth)
    )


async def _create_user(user_data: dict[str, Any], db: Database) -> User | None:
    try:
        return await db.users.create(user_data["username"], "", user_data["email"])
    except sqlalchemy.exc.OperationalError:
        return None


def _home_redirect(user: User, auth: Authentication) -> RedirectResponse:
    response = RedirectResponse("/")
    token = auth.create_user_access_token(user)
    response.set_cookie("sessionid", token, secure=True)
    return response


def _manage_db_redirect(
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
    session_id: str | None = Cookie(default=None, alias="sessionid"),
    auth: Authentication = inject(Authentication),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
):
    if session_id is None:
        session_id = auth.create_token(type="login")

    redirect_uri = urllib.parse.quote_plus(settings.discord.redirect_uri)
    response = RedirectResponse(
        f"https://discord.com/api/oauth2/authorize?"
        f"response_type=code&"
        f"client_id={settings.discord.client_id}&"
        f"scope=identify%20email&"
        f"state={session_id}&"
        f"redirect_uri={redirect_uri}&"
        f"prompt=consent"
    )
    response.set_cookie("sessionid", session_id)
    return response
