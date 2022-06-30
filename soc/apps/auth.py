import urllib.parse
from typing import Any

import sqlalchemy.exc
from fastapi import Cookie, HTTPException, Query
from fastapi.responses import RedirectResponse
from httpx import AsyncClient

from soc.context import create_app, inject
from soc.controllers.authentication import Authentication, AuthenticationSettings
from soc.database import Database
from soc.entities.users import User

auth_app = create_app()


API = "https://discord.com/api/v10"


@auth_app.get("/discord")
async def discord_code_auth(
    cookie: str = Cookie(default="", alias="sessionid"),
    code: str = Query(),
    state: str = Query(),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
    db: Database = inject(Database),
    auth: Authentication = inject(Authentication),
):
    if cookie != state:
        raise HTTPException(403, "Invalid state")

    access_token = await _get_access_token(code, settings)
    user_data = await _get_user_data(access_token)
    try:
        user = await db.users.create(user_data["username"], "", user_data["email"])
    except sqlalchemy.exc.OperationalError:
        return _manage_db_redirect(user_data, access_token, auth)
    else:
        return _home_redirect(user, auth)


def _home_redirect(user: User, auth: Authentication) -> RedirectResponse:
    response = RedirectResponse("/")
    session_id = auth.create_user_access_token(user)
    response.set_cookie("sessionid", session_id, secure=True)
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


async def _get_access_token(code: str, settings: AuthenticationSettings) -> str:
    async with AsyncClient() as client:
        resp = await client.post(
            f"{API}/oauth2/token",
            data={
                "client_id": settings.discord.client_id,
                "client_secret": settings.discord.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.discord.redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        data = resp.json()
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, data)

        return data["access_token"]


async def _get_user_data(access_token: str) -> dict[str, Any]:
    async with AsyncClient() as client:
        resp = await client.get(
            f"{API}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = resp.json()
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, data)

        return data


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
