from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    cors_origins: str = "http://localhost:8080"

    # GCS
    gcs_bucket_name: str = ""
    gcs_credentials_b64: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def gcs_enabled(self) -> bool:
        return bool(self.gcs_bucket_name and self.gcs_credentials_b64)


settings = Settings()  # type: ignore[call-arg]
