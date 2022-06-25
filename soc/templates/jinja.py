from pathlib import Path
from typing import Any

from bevy import Bevy, Inject
from jinja2 import Template
from starlette.templating import Jinja2Templates

from soc.templates.settings import TemplateSettings


class Jinja2(Bevy):
    config: TemplateSettings = Inject

    def __init__(self):
        self.templating = Jinja2Templates(self.directory, **self.settings)

    @property
    def directory(self) -> Path:
        directory = self.config.directory.strip(r"\/")
        return Path(directory).expanduser().resolve()

    @property
    def settings(self) -> dict[str, Any]:
        return {"enable_async": False} | self.config.environment

    def get_template(self, name: str) -> Template:
        return self.templating.get_template(name)
