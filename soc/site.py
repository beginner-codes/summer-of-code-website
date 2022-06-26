from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncEngine

from soc.admin import admin_app
from soc.api import api_app
from soc.auth_scheme import get_session_from_cookie_no_auth
from soc.config import BaseSettingsModel
from soc.context import create_context
from soc.context import inject
from soc.templates.jinja import Jinja2

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


@site.get("/", response_class=HTMLResponse)
async def index(
    session: dict = Depends(get_session_from_cookie_no_auth),
    template: Jinja2 = inject(Jinja2),
):
    return template(
        "index.html", username=session.get("username", "<i>NOT LOGGED IN</i>")
    )
