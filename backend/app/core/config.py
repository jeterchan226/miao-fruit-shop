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
    # 放行本專案的 Vercel 部署，搭配 allow_credentials=True 必須收斂、不可放整個
    # vercel.app。兩段：
    #   1) production 別名 frontend-theta-one-22（隨機後綴、無 team slug）→ 精確字面
    #   2) preview/分支 frontend-<...>-jeterchans-projects → 綁全域唯一的 team slug
    # 綁專案名前綴(frontend-)不安全：任何人都能註冊 frontend-* 專案。
    # 可用環境變數 CORS_ORIGIN_REGEX 覆寫（換團隊或自訂網域時）。
    cors_origin_regex: str = (
        r"https://(frontend-theta-one-22"
        r"|frontend(-[a-z0-9]+)*-jeterchans-projects)\.vercel\.app"
    )
    # 只放行本團隊（team slug 全域唯一、別人搶不到）的 Vercel 部署：
    # production 別名 frontend-jeterchans-projects.vercel.app 與
    # preview/分支網址 frontend-<hash>-jeterchans-projects.vercel.app。
    # 綁專案名前綴(frontend-)不安全:任何人都能註冊 frontend-* 專案;故綁 team 後綴。
    # 可用環境變數 CORS_ORIGIN_REGEX 覆寫(例如改團隊或改自訂網域時)。
    cors_origin_regex: str = (
        r"https://frontend(-[a-z0-9]+)*-jeterchans-projects\.vercel\.app"
    )

    # GCS
    gcs_bucket_name: str = ""
    gcs_credentials_b64: str = ""

    # LINE Messaging API
    line_channel_access_token: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        # 去結尾斜線：瀏覽器送的 Origin 不含斜線，設定值誤帶 "/" 會比對失敗。
        return [
            o.strip().rstrip("/")
            for o in self.cors_origins.split(",")
            if o.strip()
        ]

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
