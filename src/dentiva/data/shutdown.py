"""Crash marker used to detect a process that did not complete clean shutdown."""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path


class ShutdownFlag:
    """Atomically maintain a small unclean-shutdown marker beside the database."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @property
    def was_unclean(self) -> bool:
        return self.path.exists()

    def begin_startup(self) -> bool:
        """Return whether the previous run was unclean, then persist this run's marker."""
        previous_run_was_unclean = self.was_unclean
        self.mark_startup()
        return previous_run_was_unclean

    def mark_startup(self) -> None:
        """Persist the dirty marker before opening mutable application state."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {"pid": os.getpid(), "started_utc": datetime.now(UTC).isoformat()},
            sort_keys=True,
        )
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(payload + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, self.path)
        except BaseException:
            with suppress(FileNotFoundError):
                os.unlink(temporary_name)
            raise

    def mark_clean_shutdown(self) -> None:
        """Remove the marker only after database close/checkpoint has succeeded."""
        self.path.unlink(missing_ok=True)
