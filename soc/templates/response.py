from typing import Any

from bevy import Bevy, bevy_method, Inject
from fastapi import Request
from fastapi.responses import HTMLResponse

from soc.auth_helpers import parse_token
from soc.config.models.authentication import AuthenticationSettings
from soc.config.models.site import SiteSettings
from soc.templates.jinja import Jinja2


class TemplateResponse(HTMLResponse, Bevy):
    @bevy_method
    def __init__(
        self,
        data: tuple[str, dict[str, Any]] = None,
        status_code: int = 200,
        headers=None,
        media_type=None,
        background=None,
        render_template: Jinja2 = Inject,
    ):
        template_name, template_scope = self._process_data(data)
        content = render_template(template_name, **self._populate_scope(), **template_scope)
        super().__init__(content, status_code, headers, media_type, background)

    @bevy_method
    def _populate_scope(self, request: Request = Inject, auth_settings: AuthenticationSettings = Inject,
                        site_settings: SiteSettings = Inject) -> dict[str, Any]:
        scope = {}
        session = parse_token(request.cookies.get("sessionid"), auth_settings)
        if session:
            scope["user"] = {
                "username": session.get("username"),
                "roles": session.get("roles", [])
            }

        if site_settings.dev:
            scope["dev"] = True

        return scope

    def _process_data(self, data):
        match data:
            case (str() as template, dict() as scope):
                return template, scope
            case str() as template:
                return template, {}
            case _:
                return "", {}
