from pydantic import BaseSettings as _BaseSettings, Extra


class BaseSettingsModel(_BaseSettings):
    class Config:
        extra = Extra.allow
        env_prefix = "SOC_"
