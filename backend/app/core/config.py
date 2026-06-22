from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = ""
    db_user: str = ""
    db_password: str = ""
    db_name: str = ""
    db_host: str = ""
    db_port: int = 5432
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    cors_origins: str = "http://localhost:8080"
    # 放行所有 Vercel 部署網址（preview + production），避免每次部署換網址就壞掉。
    cors_origin_regex: str = r"https://.*\.vercel\.app"

    # GCS
    gcs_bucket_name: str = ""
    gcs_credentials_b64: str = ""

    # LINE Messaging API
    line_channel_access_token: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if not (self.db_user and self.db_password and self.db_name and self.db_host):
            raise ValueError("DATABASE_URL 或 DB_USER/DB_PASSWORD/DB_NAME/DB_HOST 必須設定")

        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        if self.db_host.startswith("/"):
            host = quote_plus(self.db_host)
            return f"postgresql+asyncpg://{user}:{password}@/{self.db_name}?host={host}"
        return (
            f"postgresql+asyncpg://{user}:{password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def gcs_enabled(self) -> bool:
        return bool(self.gcs_bucket_name and self.gcs_credentials_b64)


settings = Settings()  # type: ignore[call-arg]
