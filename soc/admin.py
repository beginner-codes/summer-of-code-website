import subprocess
from typing import Any

from fastapi import Depends
from fastapi.responses import HTMLResponse

from soc.auth_scheme import get_session_from_cookie, get_session_from_header
from soc.context import create_app, inject
from soc.controllers.authentication import Authentication
from soc.templates.jinja import Jinja2
from soc.templates.response import TemplateResponse

admin_app = create_app()


@admin_app.get("/api/v1/db/migrate")
async def migrate_database(session=Depends(get_session_from_header)):
    process = subprocess.Popen(
        ["alembic", "upgrade", "head"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    return {"stdout": stdout, "stderr": stderr}


@admin_app.get("/db", response_class=TemplateResponse)
async def manage_db(session: dict[str, Any] = Depends(get_session_from_cookie)):
    return "manage_db.html", {"email": session["email"]}


@admin_app.get("/login", response_class=HTMLResponse)
async def login(
    template: Jinja2 = inject(Jinja2),
    auth: Authentication = inject(Authentication),
):
    token = auth.create_token(user_id=1, username="Test User")
    response = HTMLResponse(template("login.html"))
    response.set_cookie("sessionid", token)
    return response


@admin_app.get("/logout", response_class=HTMLResponse)
async def logout(template: Jinja2 = inject(Jinja2)):
    response = HTMLResponse(template("logout.html"))
    response.delete_cookie("sessionid")
    return response
