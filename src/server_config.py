from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    """Server configuration settings loaded from environment variables."""

    api_access_token: str = Field(
        ..., description="Access token for API authentication", env="API_ACCESS_TOKEN"
    )
    api_base_url: str = Field(
        "https://api.football-data.org/v4",
        description="Base URL for the API",
        env="API_BASE_URL",
    )
    nebius_api_key: str = Field(
        ...,
        description="API key for Nebius API",
        env="NEBIUS_API_KEY",
    )
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
