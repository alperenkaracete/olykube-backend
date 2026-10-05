import os
import sys
import types

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Uygulama import edilmeden önce: gerçek Postgres/Chroma/.env yerine test ortamı
os.environ["SQLALCHEMY_DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key"

# chroma_client import anında ChromaDB sunucusuna bağlanır; testlerde sahte collection kullan
fake_chroma = types.ModuleType("services.chroma_client")
fake_chroma.collection = None
sys.modules["services.chroma_client"] = fake_chroma

import main  # noqa: E402
import models  # noqa: E402
import auth.token  # noqa: E402
from services import rate_limiter  # noqa: E402


class FakeRedis:
    """Rate limiter'ın kullandığı incr/expire'ı bellekte taklit eder."""

    def __init__(self):
        self.store = {}

    def incr(self, key):
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, key, seconds):
        return True


class DownRedis:
    """Erişilemeyen Redis: her çağrıda bağlantı hatası fırlatır."""

    def __init__(self):
        self.calls = 0

    def incr(self, key):
        self.calls += 1
        raise redis.exceptions.ConnectionError("Redis kapalı")

    def expire(self, key, seconds):
        raise redis.exceptions.ConnectionError("Redis kapalı")


@pytest.fixture
def fake_redis(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(rate_limiter, "r", fake)
    monkeypatch.setattr(rate_limiter, "_redis_down_until", 0.0)
    return fake


@pytest.fixture
def down_redis(monkeypatch):
    down = DownRedis()
    monkeypatch.setattr(rate_limiter, "r", down)
    monkeypatch.setattr(rate_limiter, "_redis_down_until", 0.0)
    return down


@pytest.fixture
def client(fake_redis):
    # Her test için temiz bir in-memory SQLite veritabanı
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    models.Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[main.get_db] = override_get_db
    main.app.dependency_overrides[auth.token.get_db] = override_get_db
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    client.post("/register", json={"email": "test@olykube.dev", "password": "s3cret"})
    token = client.post(
        "/login", json={"email": "test@olykube.dev", "password": "s3cret"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
