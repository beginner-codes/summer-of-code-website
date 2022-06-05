from pydantic import BaseSettings as _BaseSettings, Extra


class BaseSettingsModel(_BaseSettings):
    __config_key__: str | None = None

    class Config:
        extra = Extra.allow
        env_prefix = "SOC_"
