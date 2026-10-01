"""Single SQLite engine factory with the durability pragmas from ADR-003."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL, Engine

DEFAULT_BUSY_TIMEOUT_MS = 5_000
DEFAULT_CACHE_KIB = 20_000


def create_sqlite_engine(
    database: Path | str,
    *,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
    cache_kib: int = DEFAULT_CACHE_KIB,
    echo: bool = False,
) -> Engine:
    """Create a local SQLite engine and configure every DB-API connection.

    ``database`` is a filesystem path or the literal ``:memory:``. File-based
    databases use WAL; in-memory databases keep SQLite's memory journal mode.
    """
    if (
        isinstance(busy_timeout_ms, bool)
        or not isinstance(busy_timeout_ms, int)
        or busy_timeout_ms < 0
    ):
        raise ValueError("busy_timeout_ms must be a non-negative integer")
    if isinstance(cache_kib, bool) or not isinstance(cache_kib, int) or cache_kib <= 0:
        raise ValueError("cache_kib must be a positive integer")

    raw_database = str(database)
    in_memory = raw_database == ":memory:"
    if in_memory:
        url = URL.create("sqlite+pysqlite", database=raw_database)
    else:
        path = Path(raw_database).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        url = URL.create("sqlite+pysqlite", database=str(path))

    engine = create_engine(
        url,
        echo=echo,
        connect_args={"timeout": busy_timeout_ms / 1_000, "check_same_thread": False},
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def apply_pragmas(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute(f"PRAGMA busy_timeout = {busy_timeout_ms}")
            cursor.execute("PRAGMA synchronous = FULL")
            cursor.execute("PRAGMA temp_store = MEMORY")
            cursor.execute(f"PRAGMA cache_size = -{cache_kib}")
            if not in_memory:
                cursor.execute("PRAGMA journal_mode = WAL")
                cursor.fetchone()
        finally:
            cursor.close()

    return engine
