from pydantic import Field

from soc.config.base_model import BaseSettingsModel


class JWTSettings(BaseSettingsModel):
    private_key: str = Field(default=None, env="SOC_JWT_PRIVATE_KEY")
    public_key: str = Field(default=None, env="SOC_JWT_PUBLIC_KEY")
    algorithm: str = Field(default="HS256", env="SOC_JWT_ALGORITHM")


class DiscordSettings(BaseSettingsModel):
    client_id: str = Field(default="", env="SOC_DISCORD_CLIENT_ID")
    client_secret: str = Field(default="", env="SOC_DISCORD_CLIENT_SECRET")
    redirect_uri: str = Field(default="", env="SOC_DISCORD_REDIRECT_URI")


class AuthenticationSettings(BaseSettingsModel):
    __config_key__ = "authentication"

    salt_rounds: int = Field(default=12, env="SOC_AUTH_SALT_ROUNDS")
    salt_prefix: bytes = Field(default=b"2b", env="SOC_AUTH_SALT_PREFIX")
    admin_email: str = Field(default="", env="SOC_AUTH_ADMIN_EMAIL")
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    discord: DiscordSettings = Field(default_factory=DiscordSettings)
