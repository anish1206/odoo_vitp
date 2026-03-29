from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Reimbursement Management API"
    environment: str = "dev"
    database_url: str = "sqlite:///./dev.db"
    secret_key: str = "change-me-in-env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: str = "http://localhost:5173"
    uploads_dir: str = "./uploads"
    currency_provider: str = "live-with-fallback"
    currency_api_url: str = "https://api.exchangerate.host/latest"
    currency_timeout_seconds: float = 6.0
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_ocr_timeout_seconds: float = 20.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RMS_",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
