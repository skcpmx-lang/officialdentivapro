"""Empty foundation baseline; domain schema is introduced in Phase 3."""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "0001_foundation_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reserve the first schema revision without inventing product tables."""


def downgrade() -> None:
    """The baseline contains no domain schema to remove."""
