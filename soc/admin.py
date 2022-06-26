import subprocess
from typing import Any

import jwt
from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse

from soc.auth_scheme import get_session_from_cookie, get_session_from_header
from soc.context import inject
from soc.controllers.authentication import AuthenticationSettings
from soc.templates.jinja import Jinja2

admin_app = FastAPI()


@admin_app.get("/api/v1/db/migrate")
async def migrate_database(session=Depends(get_session_from_header)):
    process = subprocess.Popen(
        ["alembic", "upgrade", "head"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    return {"stdout": stdout, "stderr": stderr}


@admin_app.get("/db", response_class=HTMLResponse)
async def manage_db(
    session: dict[str, Any] = Depends(get_session_from_cookie),
    template: Jinja2 = inject(Jinja2),
):
    return template("manage_db.html", email=session["email"])


@admin_app.get("/login", response_class=HTMLResponse)
async def login(
    template: Jinja2 = inject(Jinja2),
    settings: AuthenticationSettings = inject(AuthenticationSettings),
):
    token = jwt.encode(
        {"email": settings.admin_email},
        settings.jwt.private_key,
        settings.jwt.algorithm,
    )

    response = HTMLResponse(template("login.html"))
    response.set_cookie("sessionid", token)
    return response


@admin_app.get("/logout", response_class=HTMLResponse)
async def logout(template: Jinja2 = inject(Jinja2)):
    response = HTMLResponse(template("logout.html"))
    response.delete_cookie("sessionid")
    return response
