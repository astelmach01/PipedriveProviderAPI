from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    PIPEDRIVE_CLIENT_ID: str
    PIPEDRIVE_CLIENT_SECRET: str
    PIPEDRIVE_CALLBACK_URI: str

    ENVIRONMENT: str

    class Config:
        env_file = ".env"

    @property
    def TELEGRAM_API_URL(self):
        if self.ENVIRONMENT == "development":
            return "http://localhost:80/"
        else:
            return os.getenv("TELEGRAM_API_URL")


settings = Settings()
