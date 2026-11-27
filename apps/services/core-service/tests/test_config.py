import pytest
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.main import app


def test_cors_allowed_origins_are_split_and_trimmed():
    settings = Settings(
        CORS_ALLOWED_ORIGINS="https://app.example, https://admin.example "
    )

    assert settings.cors_allowed_origins == [
        "https://app.example",
        "https://admin.example",
    ]


def test_application_uses_configured_cors_origins():
    middleware = next(
        item for item in app.user_middleware if item.cls is CORSMiddleware
    )

    assert middleware.kwargs["allow_origins"] == settings.cors_allowed_origins


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("SECRET_KEY", "development-only-secret-key-not-for-production"),
        ("SECRET_KEY", "short"),
        ("POSTGRES_PASSWORD", "postgres"),
        ("MONGODB_URL", "mongodb://admin:admin123@mongodb:27017"),
        ("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"),
        ("CORS_ALLOWED_ORIGINS", "*"),
        ("CORS_ALLOWED_ORIGINS", " , "),
    ],
)
def test_production_settings_reject_development_defaults(field, value):
    settings_values = {
        "APP_ENV": "production",
        "SECRET_KEY": "s" * 48,
        "POSTGRES_PASSWORD": "postgres-production-secret",
        "MONGODB_URL": "mongodb://service:mongodb-production-secret@mongodb:27017",
        "RABBITMQ_URL": "amqp://service:rabbitmq-production-secret@rabbitmq:5672/",
        "CORS_ALLOWED_ORIGINS": "https://app.example",
    }
    settings_values[field] = value

    with pytest.raises(ValidationError):
        Settings(**settings_values)


def test_production_settings_accept_explicit_credentials_and_origins():
    settings = Settings(
        APP_ENV="production",
        SECRET_KEY="s" * 48,
        POSTGRES_PASSWORD="postgres-production-secret",
        MONGODB_URL="mongodb://service:mongodb-production-secret@mongodb:27017",
        RABBITMQ_URL="amqp://service:rabbitmq-production-secret@rabbitmq:5672/",
        CORS_ALLOWED_ORIGINS="https://app.example",
    )

    assert settings.cors_allowed_origins == ["https://app.example"]
