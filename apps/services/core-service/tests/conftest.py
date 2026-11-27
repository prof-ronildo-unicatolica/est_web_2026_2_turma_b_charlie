from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db, get_mongo_db
from app.main import app
# Register relationship targets before creating shared metadata.
from app.models.avaliacao import Avaliacao as _Avaliacao
from app.models.tutorial import Base


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@asynccontextmanager
async def test_lifespan(_app):
    yield


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mongo_db():
    database = MagicMock()
    collection = MagicMock()
    collection.create_index = AsyncMock()
    collection.replace_one = AsyncMock()
    collection.delete_one = AsyncMock()

    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[])
    collection.find.return_value = cursor

    database.__getitem__.return_value = collection
    return database


@pytest.fixture(scope="function")
def client(db_session, mongo_db, monkeypatch):
    def override_get_db():
        yield db_session

    def override_get_mongo_db():
        return mongo_db

    monkeypatch.setattr(app.router, "lifespan_context", test_lifespan)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_mongo_db] = override_get_mongo_db
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
