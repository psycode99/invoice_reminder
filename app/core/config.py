from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    google_client_id: str
    google_client_secret: str
    secret_key: str
    expiration_minutes: int
    refresh_token_expiration_days: int
    algorithm: str
    resend_api_key: str
    redis_url: str
    redis_backend: str
    from_email_addr: str
    smtp_host: str
    smtp_password: str
    smtp_port: int
    smtp_email: str
    prod: bool = False
    qbo_client_id: str
    qbo_client_secret: str
    qbo_redirect_uri: str
    qbo_environment: str

    class Config:
        env_file = ".env"


settings = Settings()