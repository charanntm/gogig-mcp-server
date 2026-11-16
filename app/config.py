from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="GOGIG_")

    host: str = "0.0.0.0"
    port: int = 8100

    api_base_url: str = "http://localhost:8000"
    api_key: str = ""


settings = Settings()
