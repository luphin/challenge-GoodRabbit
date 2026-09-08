from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "API de Turnos Laborales"
    app_version: str = "0.1.0"
    environment: str = "dev"
    api_port: int = 8000


settings = Settings()
