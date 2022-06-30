from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine

from soc.admin import admin_app
from soc.api import api_app
from soc.auth import auth_app
from soc.authentication_deps import get_session_from_cookie_no_auth
from soc.config.models.site import SiteSettings
from soc.context import create_app, create_context
from soc.templates.response import TemplateResponse

site = create_app()


site.mount("/v1/", api_app)
site.mount("/admin/", admin_app)
site.mount("/auth/", auth_app)


@site.on_event("startup")
async def on_start():
    context = site.dependency_overrides.get(create_context, create_context)()
    settings = context.get(SiteSettings)
    if settings.dev:
        database = context.get(AsyncEngine)
        if not database:
            database = context.create(AsyncEngine)


@site.get("/", response_class=TemplateResponse)
async def index(session: dict = Depends(get_session_from_cookie_no_auth)):
    return "index.html", {"username": session.get("username", "<i>NOT LOGGED IN</i>")}
