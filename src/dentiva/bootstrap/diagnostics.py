"""Write a local, redacted crash bundle without network access or traceback locals."""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from traceback import extract_tb
from typing import Any
from uuid import uuid4

from dentiva import __version__
from dentiva.core.errors import DentivaError


def write_diagnostic_bundle(
    exception: BaseException,
    destination: Path,
    *,
    version: str = __version__,
) -> Path:
    """Persist only stable error metadata and frame locations, never values/locals."""
    error_id = exception.error_id if isinstance(exception, DentivaError) else str(uuid4())
    code = exception.code if isinstance(exception, DentivaError) else "DVT-9999"
    payload: dict[str, Any] = {
        "schema_version": 1,
        "created_utc": datetime.now(UTC).isoformat(),
        "version": version,
        "error_id": error_id,
        "error_code": code,
        "exception_type": type(exception).__name__,
        "stack": [
            {
                "file": Path(frame.filename).name,
                "line": frame.lineno,
                "function": frame.name,
            }
            for frame in extract_tb(exception.__traceback__)
        ],
    }
    destination.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".diagnostic-", suffix=".tmp", dir=destination
    )
    bundle = destination / f"diagnostic-{error_id}.json"
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, bundle)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise
    return bundle
