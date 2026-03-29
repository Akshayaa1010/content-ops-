from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/contentops"
    redis_url: str = "redis://localhost:6379/0"
    groq_api_key: str = ""
    deepl_api_key: str = ""
    secret_key: str = "change-this-in-production-32chars"

    class Config:
        env_file = ".env"

settings = Settings()