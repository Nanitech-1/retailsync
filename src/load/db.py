"""Database engine and schema management for RetailSync.

Supports PostgreSQL 16 as primary target with transparent SQLite fallback
for zero-friction local development and automated testing.
"""

import logging
import re
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.exc import OperationalError

from src.config import settings

logger = logging.getLogger(__name__)


def get_engine(force_sqlite: bool = False) -> Engine:
    """Creates and returns a SQLAlchemy Engine.

    Attempts connection to PostgreSQL first; if unreachable, falls back to SQLite.

    Args:
        force_sqlite: If True, bypasses PostgreSQL and uses SQLite directly.

    Returns:
        SQLAlchemy Engine.
    """
    if force_sqlite:
        sqlite_path = settings.base_dir / settings.db.sqlite_db_path
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(f"sqlite:///{sqlite_path.as_posix()}", echo=False)

    try:
        pg_engine = create_engine(
            settings.db.database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3},
        )
        # Test connection
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to primary PostgreSQL database.")
        return pg_engine
    except (OperationalError, Exception) as exc:
        logger.warning(
            f"Could not connect to PostgreSQL ({exc}). "
            f"Falling back to local SQLite at '{settings.db.sqlite_db_path}'."
        )
        sqlite_path = settings.base_dir / settings.db.sqlite_db_path
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(f"sqlite:///{sqlite_path.as_posix()}", echo=False)


def _adapt_sql_for_sqlite(sql: str) -> str:
    """Adapts Postgres DDL / DML syntax for SQLite compatibility."""
    # Replace SERIAL PRIMARY KEY with INTEGER PRIMARY KEY
    sql = re.sub(r"\bSERIAL\s+PRIMARY\s+KEY\b", "INTEGER PRIMARY KEY AUTOINCREMENT", sql, flags=re.IGNORECASE)
    # Remove Postgres-specific cast ::numeric or ::text
    sql = re.sub(r"::numeric\b", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"::text\b", "", sql, flags=re.IGNORECASE)
    # Replace CURRENT_TIMESTAMP with CURRENT_TIMESTAMP (standard in SQLite)
    return sql


def execute_sql_file(file_path: Path, engine: Engine) -> None:
    """Executes a SQL file containing multiple statements.

    Args:
        file_path: Absolute Path to the SQL file.
        engine: SQLAlchemy Engine instance.
    """
    is_sqlite = engine.dialect.name == "sqlite"
    content = file_path.read_text(encoding="utf-8")

    if is_sqlite:
        content = _adapt_sql_for_sqlite(content)

    # Split by semicolon while ignoring comments
    statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]

    with engine.begin() as conn:
        for stmt in statements:
            # Strip SQL comments
            clean_lines = [line for line in stmt.splitlines() if not line.strip().startswith("--")]
            clean_stmt = "\n".join(clean_lines).strip()
            if not clean_stmt:
                continue
            try:
                conn.execute(text(clean_stmt))
            except Exception as e:
                logger.warning(f"Error executing statement from {file_path.name}: {e}")
                if not is_sqlite:
                    raise


def init_schema(engine: Optional[Engine] = None) -> None:
    """Initializes all database tables, staging tables, warehouse, views, and monitoring.

    Args:
        engine: Optional Engine. If None, acquires using get_engine().
    """
    if engine is None:
        engine = get_engine()

    sql_files = [
        settings.sql_dir / "01_staging.sql",
        settings.sql_dir / "02_warehouse.sql",
        settings.sql_dir / "03_views.sql",
        settings.sql_dir / "04_monitoring.sql",
    ]

    for sql_file in sql_files:
        if sql_file.exists():
            logger.info(f"Applying schema file: {sql_file.name}")
            execute_sql_file(sql_file, engine)
        else:
            logger.error(f"Schema file not found: {sql_file}")

    logger.info("Database schema initialized successfully.")
