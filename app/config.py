"""Application settings, read from environment variables or a local .env file."""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_KEY = "development-only-key-never-use-this-in-production"
DEMO_PASSWORD = "Training#2026"  # noqa: S105 (printed in the book on purpose)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./devinsight.db"
    secret_key: str = DEVELOPMENT_KEY
    access_token_minutes: int = 120
    # A public demonstration value. The seed script refuses it in production.
    seed_password: str = DEMO_PASSWORD
    log_level: str = "INFO"

    classifier_file: str = "ml/artifacts/category_model.joblib"
    classifier_metrics_file: str = "ml/artifacts/metrics.json"
    suggestion_min_confidence: float = 0.50
    related_min_score: float = 0.10
    # Chosen from labeled pairs by ml/evaluate_similarity.py: best F1, precision 0.90.
    duplicate_min_score: float = 0.20

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def production_needs_a_private_key(self) -> "Settings":
        """Refuse to start in production with a key that anyone can read in the source."""
        if self.is_production and (
            self.secret_key == DEVELOPMENT_KEY or len(self.secret_key) < 32
        ):
            raise ValueError(
                "In production SECRET_KEY must be private and at least 32 characters."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Read the settings once, then reuse the same object everywhere."""
    return Settings()
