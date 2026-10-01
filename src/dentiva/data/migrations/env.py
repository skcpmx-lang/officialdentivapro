"""Alembic environment wired through Dentiva's SQLite engine factory."""

from __future__ import annotations

from alembic import context
from sqlalchemy.engine import make_url

from dentiva.data.base import Base
from dentiva.data.engine import create_sqlite_engine

config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configured_url = config.get_main_option("sqlalchemy.url") or "sqlite:///dentiva.sqlite3"
    url = make_url(configured_url)
    if url.get_backend_name() != "sqlite":
        raise RuntimeError("The Phase 2 migration foundation supports local SQLite only")
    database = url.database or ":memory:"
    engine = create_sqlite_engine(database)
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata, compare_type=True
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
