"""Application configuration loaded from environment variables (.env)."""

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    postgres_user: str = "fopilot"
    postgres_password: str = "change_me"
    postgres_db: str = "fopilot"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str | None = None

    # Business config
    ep_annual_limit: int = 10_091_049  # ліміт ЄП, 3 група, 2026
    # Minimum days into the year before a run-rate forecast is trusted (ADR-015).
    ep_forecast_min_days: int = 30
    # Daily capacity used as the utilization denominator (ADR-016).
    work_hours_per_day: int = 8

    # External APIs
    nbu_rate_url: str = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"

    @computed_field
    @property
    def sqlalchemy_url(self) -> str:
        """Assemble the SQLAlchemy DSN, preferring an explicit DATABASE_URL if set."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
