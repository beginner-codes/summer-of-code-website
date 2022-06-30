from pydantic import Field

from soc.config.base_model import BaseSettingsModel


class SiteSettings(BaseSettingsModel):
    __config_key__ = "site"

    dev: bool = Field(default=False, env="SOC_SITE_DEV")
