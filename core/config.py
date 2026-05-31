from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    postgres_db: str = "apiforgekit"
    postgres_user: str = "apiforgekit"
    postgres_password: str = "apiforgekit"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str = "postgresql+psycopg://apiforgekit:apiforgekit@localhost:5432/apiforgekit"
    app_host: str = "127.0.0.1"
    app_port: int = 8080
    log_path: Path = ROOT_DIR / "logs" / "lead_tests.jsonl"
    contexts_dir: Path = ROOT_DIR / "exports" / "contexts"
    blueprints_dir: Path = ROOT_DIR / "exports" / "blueprints"

    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
