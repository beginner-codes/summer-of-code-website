from collections import defaultdict

from bevy import Context
from fastapi import Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncEngine

from soc.apps.admin_app import admin_app
from soc.apps.api import api_app
from soc.apps.auth import auth_app
from soc.auth_helpers import session_cookie
from soc.config.models.site import SiteSettings
from soc.context import create_app, create_context, inject
from soc.database import Database
from soc.entities.sessions import Session
from soc.templates.jinja import Jinja2
from soc.templates.response import TemplateResponse

site = create_app()
site.mount("/v1/", api_app)
site.mount("/admin/", admin_app)
site.mount("/auth/", auth_app)
site.mount("/static", StaticFiles(directory="static"), name="static")


@site.on_event("startup")
async def on_start():
    context: Context = site.dependency_overrides.get(create_context, create_context)()
    settings = context.get(SiteSettings) or context.create(
        SiteSettings, add_to_context=True
    )
    if settings.dev:
        database = context.get(AsyncEngine)
        if not database:
            context.create(AsyncEngine)


@site.get("/", response_class=TemplateResponse)
async def index(
    db: Database = inject(Database), session: Session = Depends(session_cookie)
):
    challenge = await db.challenges.get_active()
    scope = {"challenge": None}
    if challenge:
        scope["challenge"] = await challenge.to_dict(expand_submissions=True)
        scope["challenge"]["formatted_start"] = challenge.start.format("dddd, MMMM Do ")
        scope["challenge"]["formatted_end"] = challenge.end.format("dddd, MMMM Do ")
        scope["user_votes"] = defaultdict(set)
        if session:
            for submission in scope["challenge"]["submissions"]:
                for emoji, voters in submission["votes"].items():
                    if session.user_id in voters:
                        scope["user_votes"][submission["id"]].add(emoji)

    return "index.html", scope


@site.get("/challenges", response_class=TemplateResponse)
async def challenges(db: Database = inject(Database)):
    return "challenges.html", {"challenges": await db.challenges.get_all()}


@site.get(
    "/challenges/{challenge_id}/create-submission", response_class=TemplateResponse
)
async def challenges(challenge_id: int, db: Database = inject(Database)):
    challenge = await db.challenges.get(challenge_id)
    if not challenge.active:
        return "error.html", {
            "reason": f"{challenge.title} is no longer open for new submissions.",
            "title": "Submissions Are Closed",
        }

    return "create_submission.html", {"challenge": await challenge.to_dict()}


@site.get("/logout", response_class=HTMLResponse)
async def logout(template: Jinja2 = inject(Jinja2)):
    response = HTMLResponse(template("logout.html"))
    response.delete_cookie("sessionid")
    return response
