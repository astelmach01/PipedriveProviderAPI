from pydantic import BaseSettings


class Settings(BaseSettings):
    PIPEDRIVE_CLIENT_ID: str
    PIPEDRIVE_CLIENT_SECRET: str

    ENVIRONMENT: str

    class Config:
        env_file = ".env"

    @property
    def TELEGRAM_API_URL(self):
        if self.ENVIRONMENT == "development":
            return "http://localhost:8080/"
        else:
            return "https://telegram-api.herokuapp.com/"


settings = Settings()
