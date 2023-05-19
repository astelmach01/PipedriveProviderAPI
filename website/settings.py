from pydantic import BaseSettings


class Settings(BaseSettings):
    PIPEDRIVE_CLIENT_ID: str
    PIPEDRIVE_CLIENT_SECRET: str
    TELEGRAM_API_URL: str = "https://api.telegram.org/bot"

    class Config:
        env_file = ".env"  # Optional: Load environment variables from a file


settings = Settings()
