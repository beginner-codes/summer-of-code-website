from typing import Any

from bevy import Bevy, bevy_method, Inject
from fastapi.responses import HTMLResponse

from soc.config.models.site import SiteSettings
from soc.entities.sessions import Session
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
    def _populate_scope(
        self,
        site_settings: SiteSettings = Inject,
        session: Session = Inject
    ) -> dict[str, Any]:
        scope = {}
        if session:
            scope["user"] = {
                "username": session.get("username"),
                "roles": session.get("roles", []),
                "id": session.get("user_id", -1)
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
