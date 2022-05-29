from pydantic import Field

from soc.config import BaseSettingsModel


class DatabaseSettings(BaseSettingsModel):
    port: int = Field(env="SOC_DB_PORT")
    host: str = Field(env="SOC_DB_HOST")
    name: str = Field(env="SOC_DB_NAME")
    username: str = Field(env="SOC_DB_USERNAME")
    password: str = Field(env="SOC_DB_PASSWORD")

    @property
    def uri(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
