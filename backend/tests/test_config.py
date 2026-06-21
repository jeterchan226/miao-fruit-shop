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


def test_database_url_can_be_built_from_db_parts(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("DB_USER", "ecommerce_user")
    monkeypatch.setenv("DB_PASSWORD", "p@ss word")
    monkeypatch.setenv("DB_NAME", "ecommerce")
    monkeypatch.setenv("DB_HOST", "/cloudsql/project:asia-east1:db")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    s = Settings()
    assert s.sqlalchemy_database_url == (
        "postgresql+asyncpg://ecommerce_user:p%40ss+word@/ecommerce"
        "?host=%2Fcloudsql%2Fproject%3Aasia-east1%3Adb"
    )
