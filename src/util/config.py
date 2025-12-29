from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    DATABASE_URL: str 
    redis_url: str
    jwt_secret_key:str
    jwt_algo:str 
    access_token_expiry:int
    refresh_token_expiry:int


    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",  # Adjusted to point to the root directory
        env_file_encoding="utf-8",
    )

config = Config()

class Settings:
    PROJECT_NAME: str = "Scheduling and Notification System"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "Backend for Scheduling and Notification System"
    API_PREFIX: str = "/api/v1"