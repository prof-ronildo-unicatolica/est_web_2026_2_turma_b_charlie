from urllib.parse import urlsplit

from pydantic import ConfigDict, model_validator
from pydantic_settings import BaseSettings

DEVELOPMENT_SECRET_KEY = "development-only-secret-key-not-for-production"


class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True, env_file=".env")

    PROJECT_NAME: str = "Sistema de Reservas - Core Service"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "development"
    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    # Configurações do PostgreSQL
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "hotel_db_dev"
    POSTGRES_PORT: str = "5432"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Configurações do MongoDB
    MONGODB_URL: str = "mongodb://admin:admin123@localhost:27017"
    MONGODB_DB: str = "hotel_mongo_dev"

    # Configurações do RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # Configurações de autenticação de jwt
    SECRET_KEY: str = DEVELOPMENT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def validate_non_development_security(self):
        if self.APP_ENV == "development":
            return self

        if (
            len(self.SECRET_KEY.encode("utf-8")) < 32
            or self.SECRET_KEY == DEVELOPMENT_SECRET_KEY
        ):
            raise ValueError(
                "SECRET_KEY must be unique and at least 32 bytes outside development."
            )

        if self.POSTGRES_PASSWORD == "postgres":
            raise ValueError(
                "POSTGRES_PASSWORD must be changed outside development."
            )

        if urlsplit(self.MONGODB_URL).password == "admin123":
            raise ValueError(
                "MONGODB_URL must not use the development password outside development."
            )

        if urlsplit(self.RABBITMQ_URL).password == "guest":
            raise ValueError(
                "RABBITMQ_URL must not use the guest password outside development."
            )

        if not self.cors_allowed_origins or "*" in self.cors_allowed_origins:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS must contain explicit origins outside development."
            )

        return self


settings = Settings()
