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

    # Clé API pour les appels machine-to-machine (CI/CD → /scans)
    CI_API_KEY: str = "changeme-ci-api-key"

    # MobSF (Mobile Security Framework)
    MOBSF_URL: str = "http://mobsf:8000"
    MOBSF_API_KEY: str = "changeme-mobsf-api-key"

    # Ollama (IA locale)
    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3"

    # AWS / LocalStack
    AWS_REGION: str = "eu-west-3"
    AWS_ENDPOINT_URL: str = ""          # vide = AWS réel ; "http://localstack:4566" pour LocalStack
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"

    class Config:
        env_file = "../../.env"
        extra = "ignore"


settings = Settings()
