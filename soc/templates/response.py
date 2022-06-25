from typing import Any, Mapping

from bevy import Bevy, Inject
from fastapi.responses import HTMLResponse
from jinja2 import Template
from starlette.background import BackgroundTask

from soc.templates.jinja import Jinja2


class TemplateResponse(HTMLResponse, Bevy):
    jinja2: Jinja2 = Inject

    def __init__(
        self,
        template: str,
        content: Any = None,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ):
        super().__init__(content, status_code, headers, media_type, background)
        self._template_name = template

    @property
    def template(self) -> Template:
        return self.jinja2.get_template(self._template_name)

    def render(self, content: Any) -> bytes:
        return self.template.render(**content).encode()
