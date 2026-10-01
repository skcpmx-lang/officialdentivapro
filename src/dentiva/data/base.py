"""Declarative metadata for Alembic; domain models arrive in Phase 3."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base metadata for the application's SQLAlchemy mappings."""
