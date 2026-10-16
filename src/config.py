"""Configuration module for RetailSync.

Loads environment variables from .env and provides typed settings.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class DatabaseConfig:
    """Database connection and fallback configuration."""
    user: str = os.getenv("POSTGRES_USER", "retailsync_user")
    password: str = os.getenv("POSTGRES_PASSWORD", "retailsync_secure_pass")
    db: str = os.getenv("POSTGRES_DB", "retailsync_dw")
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}",
    )
    sqlite_db_path: str = os.getenv("SQLITE_DB_PATH", "data/retailsync.db")


@dataclass(frozen=True)
class LLMConfig:
    """LLM provider configuration with fallback."""
    provider: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    api_key: str = os.getenv("LLM_API_KEY", "")
    model: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    batch_size: int = int(os.getenv("LLM_BATCH_SIZE", "20"))
    timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "15"))


@dataclass(frozen=True)
class AlertConfig:
    """Alerting configuration for Telegram and Email."""
    channel: str = os.getenv("ALERT_CHANNEL", "none").lower()  # telegram, email, none
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    recipient: str = os.getenv("ALERT_EMAIL_RECIPIENT", "")


@dataclass(frozen=True)
class Settings:
    """Global project settings."""
    base_dir: Path = BASE_DIR
    data_raw_dir: Path = BASE_DIR / os.getenv("DATA_RAW_DIR", "data/raw")
    logs_dir: Path = BASE_DIR / "logs"
    sql_dir: Path = BASE_DIR / "src" / "sql"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    api_base_url: str = os.getenv("API_BASE_URL", "https://dummyjson.com/products")
    db: DatabaseConfig = DatabaseConfig()
    llm: LLMConfig = LLMConfig()
    alert: AlertConfig = AlertConfig()


settings = Settings()
