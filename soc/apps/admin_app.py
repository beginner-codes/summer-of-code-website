from typing import Any

from fastapi import Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from soc.apps.admin_api import admin_api
from soc.auth_helpers import (
    dev_only,
    require_roles,
    session_cookie,
    validate_session_cookie,
)
from soc.context import create_app, inject
from soc.controllers.authentication import Authentication
from soc.database import Database
from soc.database.models.base import BaseModel
from soc.database.settings import Settings
from soc.templates.jinja import Jinja2
from soc.templates.response import TemplateResponse


admin_app = create_app()
admin_app.mount("/api/v1", admin_api)


@admin_app.get(
    "/dashboard",
    response_class=TemplateResponse,
    dependencies=[Depends(require_roles("ADMIN", "MOD"))],
)
async def dashboard(
    page: int = Query(1, gt=0),
    num: int = Query(25, gt=0),
    db: Database = inject(Database),
):
    start = (page - 1) * num
    scope = {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "roles": await user.get_roles(),
                "banned": user.banned,
            }
            for user in await db.users.get_all(start, num)
        ]
    }
    return "admin/dashboard.html", scope


@admin_app.get(
    "/db",
    response_class=TemplateResponse,
    dependencies=[Depends(validate_session_cookie), Depends(require_roles("ADMIN"))],
)
async def manage_db(session: dict[str, Any] = Depends(session_cookie)):
    return "admin/manage_db.html", {
        "email": session.get("email"),
        "username": session.get("username"),
    }


@admin_app.get(
    "/challenges",
    response_class=TemplateResponse,
    dependencies=[
        Depends(validate_session_cookie),
        Depends(require_roles("ADMIN", "MOD")),
    ],
)
async def challenges(db: Database = inject(Database)):
    return "admin/challenges.html", {
        "challenges": [
            await challenge.to_dict() for challenge in await db.challenges.get_all()
        ]
    }


@admin_app.get(
    "/challenges/create",
    response_class=TemplateResponse,
    dependencies=[Depends(validate_session_cookie), Depends(require_roles("ADMIN"))],
)
async def create_challenge(db: Database = inject(Database)):
    return "admin/create_challenge.html", {"challenges": await db.challenges.get_all()}


@admin_app.get(
    "/challenges/{challenge_id}",
    response_class=TemplateResponse,
    dependencies=[
        Depends(validate_session_cookie),
        Depends(require_roles("ADMIN", "MOD")),
    ],
    name="admin-view-challenge",
)
async def show_challenge(challenge_id: int, db: Database = inject(Database)):
    return "admin/challenge.html", {
        "challenge": await (await db.challenges.get(challenge_id)).to_dict(
            expand_submissions=True
        )
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

    token, _ = await auth.create_user_session(user)
    response = HTMLResponse(
        template("admin/login.html", user={"username": user.username, "id": user.id})
    )
    response.set_cookie(
        "sessionid", token, secure=True, httponly=True, expires=7 * 24 * 60 * 60
    )
    return response


@admin_app.get(
    "/settings",
    response_class=TemplateResponse,
    dependencies=[
        Depends(validate_session_cookie),
        Depends(require_roles("ADMIN")),
    ],
)
async def settings_page(settings: Settings = inject(Settings)):
    return "admin/settings.html", {
        "announcement_webhooks": await settings.get("announcement_webhooks", {})
    }
