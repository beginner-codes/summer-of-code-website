from typing import Any

from bevy import Bevy, bevy_method, Inject
from fastapi import HTTPException
from httpx import AsyncClient

from soc.config.models.authentication import AuthenticationSettings


class Discord(Bevy):
    API = "https://discord.com/api/v10"

    @bevy_method
    async def get_access_token(
        self, code: str, settings: AuthenticationSettings = Inject
    ) -> str:
        async with AsyncClient() as client:
            resp = await client.post(
                f"{self.API}/oauth2/token",
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

    async def get_user_data(self, access_token: str) -> dict[str, Any]:
        async with AsyncClient() as client:
            resp = await client.get(
                f"{self.API}/users/@me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            data = resp.json()
            if resp.status_code != 200:
                raise HTTPException(resp.status_code, data)

            return data
