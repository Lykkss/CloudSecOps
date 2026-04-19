from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_PORT: int = 8000

    # JWT
    SECRET_KEY: str = "changeme-local-dev-secret-key-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # PostgreSQL
    DATABASE_URL: str = "postgresql://cloudsecops:changeme-local-dev@localhost:5432/cloudsecops"

    class Config:
        env_file = "../../.env"
        extra = "ignore"


settings = Settings()
