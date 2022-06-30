import urllib.parse

import sqlalchemy.exc
from fastapi import Cookie, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse
from httpx import AsyncClient

from soc.context import create_app, inject
from soc.controllers.authentication import Authentication, AuthenticationSettings
from soc.database import Database

auth_app = create_app()


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

    api = "https://discord.com/api/v10"
    async with AsyncClient() as client:
        resp = await client.post(
            f"{api}/oauth2/token",
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
            return JSONResponse(
                {
                    "a": settings.discord.client_id,
                    "b": settings.discord.client_secret,
                    "data": data,
                },
                resp.status_code,
            )

        resp = await client.get(
            f"{api}/users/@me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        user_data = resp.json()

    try:
        user = await db.users.create(user_data["username"], "", user_data["email"])
    except sqlalchemy.exc.OperationalError:
        response = RedirectResponse("/admin/db")
        session_id = auth.create_token(
            username=user_data["username"],
            email=user_data["email"],
            access_token=data["access_token"],
        )
    else:
        response = RedirectResponse("/")
        session_id = auth.create_user_access_token(user)

    response.set_cookie("sessionid", session_id, secure=True)
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
