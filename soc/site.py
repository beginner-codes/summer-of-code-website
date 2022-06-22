from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncEngine

from soc.admin import admin_app
from soc.api import api_app
from soc.config import BaseSettingsModel
from soc.context import create_context
from soc.database.models.base import BaseModel

site = FastAPI()

site.mount("/v1/", api_app)
site.mount("/admin/", admin_app)


class SiteSettings(BaseSettingsModel):
    __config_key__ = "site"

    dev: bool = Field(default=False, env="SOC_SITE_DEV")


@site.on_event("startup")
async def on_start():
    context = site.dependency_overrides.get(create_context, create_context)()
    settings = context.get(SiteSettings)
    if settings.dev:
        database = context.get(AsyncEngine)
        if not database:
            database = context.create(AsyncEngine)
            async with database.begin() as conn:
                await conn.run_sync(BaseModel.metadata.create_all)


@site.get("/", response_class=HTMLResponse)
async def index():
    return "<h1>Hello World</h1>"
