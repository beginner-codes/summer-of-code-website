from pydantic import Field

from soc.config import BaseSettingsModel


class DatabaseSettings(BaseSettingsModel):
    __config_key__ = "database"

    host: str = Field(default="", env="SOC_DB_HOST")
    port: int = Field(default=0, env="SOC_DB_PORT")
    database: str = Field(default="", env="SOC_DB_DATABASE")
    username: str = Field(default="", env="SOC_DB_USERNAME")
    password: str = Field(default="", env="SOC_DB_PASSWORD")
    driver: str = Field(default="postgres+asyncpg", env="SOC_DB_DRIVER")

    @property
    def uri(self) -> str:
        uri = [self.driver, "://"]
        if self.username:
            uri.append(self.username)
            if self.password:
                uri.append(f":{self.password}")

            uri.append("@")

        if self.host:
            uri.append(self.host)
            if self.port:
                uri.append(f":{self.port}")

        if self.database:
            uri.append(f"/{self.database}")

        return "".join(uri)
