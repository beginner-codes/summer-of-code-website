from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncEngine

from soc.api import api_app
from soc.config import BaseSettingsModel
from soc.context import create_context
from soc.database.models.base import BaseModel

site = FastAPI()

site.mount("/v1/", api_app)


class SiteSettings(BaseSettingsModel):
    __config_key__ = "site"

    dev: bool = Field(default=False, env="SOC_SITE_DEV")


@site.on_event("startup")
async def on_start():
    context = create_context()
    settings = context.get(SiteSettings)
    if settings.dev:
        database = context.create(AsyncEngine)
        async with database.begin() as conn:
            await conn.run_sync(BaseModel.metadata.drop_all)
            await conn.run_sync(BaseModel.metadata.create_all)


@site.get("/", response_class=HTMLResponse)
async def index():
    return "<h1>Hello World</h1>"
