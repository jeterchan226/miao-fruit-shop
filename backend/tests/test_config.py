from app.core.config import Settings


def test_cors_origins_list_splits_and_trims(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:8080, https://miao.example ")
    s = Settings()
    assert s.cors_origins_list == ["http://localhost:8080", "https://miao.example"]


def test_defaults_apply(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.delenv("JWT_EXPIRE_MINUTES", raising=False)
    s = Settings()
    assert s.jwt_algorithm == "HS256"
    assert s.jwt_expire_minutes == 480
