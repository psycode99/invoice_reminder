from pydantic_settings import BaseSettings, SettingsConfigDict
import os

# BASE_DIR = os.path.dirname(__file__)
# DOTENV = os.path.join(BASE_DIR, ".env")


class Settings(BaseSettings):
    database_url: str
    google_client_id: str
    google_client_secret: str
    secret_key: str
    expiration_minutes: int
    algorithm: str

    class Config:
        env_file = ".env"

    # model_config = SettingsConfigDict(env_file=DOTENV)

settings = Settings()