from pydantic import Field

from soc.config.base_model import BaseSettingsModel


class TemplateSettings(BaseSettingsModel):
    __config_key__ = "templates"

    directory: str
    environment: dict = Field(default_factory=dict)
