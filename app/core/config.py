from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://smarttherm:smarttherm@localhost:5432/smarttherm"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "admin123"

    OLLAMA_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OPERATING_EXPENSES_MONTHLY: float = 0.0

    class Config:
        env_file = ".env"


settings = Settings()