from typing import Any

from fastapi import Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from soc.apps.admin_api import admin_api
from soc.auth_helpers import (
    dev_only,
    session_cookie,
    validate_session_cookie,
)
from soc.auth_helpers import require_roles
from soc.context import create_app, inject
from soc.controllers.authentication import Authentication
from soc.database import Database
from soc.database.models.base import BaseModel
from soc.templates.jinja import Jinja2
from soc.templates.response import TemplateResponse

admin_app = create_app()
admin_app.mount("/api/v1", admin_api)


@admin_app.get(
    "/db",
    response_class=TemplateResponse,
    dependencies=[Depends(validate_session_cookie), Depends(require_roles("ADMIN"))],
)
async def manage_db(session: dict[str, Any] = Depends(session_cookie)):
    return "manage_db.html", {
        "email": session.get("email"),
        "username": session.get("username"),
    }


@admin_app.get("/login", response_class=HTMLResponse, dependencies=[Depends(dev_only)])
async def login(
    role: str = Query("ADMIN"),
    template: Jinja2 = inject(Jinja2),
    auth: Authentication = inject(Authentication),
    db: Database = inject(Database),
    engine: AsyncEngine = inject(AsyncEngine),
):
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    user = await db.users.get_by_id(1)
    if not user:
        user = await db.users.create("Test User", "", "testuser@beginner.codes")

    role = role.upper()
    roles = await user.get_roles()
    if role not in roles:
        await user.set_roles([role, *roles])

    token = await auth.create_user_access_token(user)
    response = HTMLResponse(template("login.html"))
    response.set_cookie("sessionid", token)
    return response
