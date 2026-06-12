from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Remote Control System"
    SECRET_KEY: str = "change-this-secret-key"
    GATEWAY_WS_URL: str = "ws://localhost:8765"

    class Config:
        env_file = ".env"

settings = Settings()
