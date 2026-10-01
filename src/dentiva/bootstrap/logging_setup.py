"""File logging bootstrap with bounded rotation and a handler-level redaction choke point."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from traceback import extract_tb
from types import TracebackType

from dentiva.core.redact import redact_text

MAX_LOG_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 6
_LOGGER_NAME = "dentiva"


class RedactionFilter(logging.Filter):
    """Render and redact a record before it reaches any persistent handler."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            message = "[unformattable log message]"
        record.msg = redact_text(message)
        record.args = ()
        error_id = getattr(record, "error_id", "-")
        record.error_id = redact_text(str(error_id))
        return True


class RedactingFormatter(logging.Formatter):
    """Retain stack frame locations but suppress exception values and locals."""

    def formatException(
        self,
        exc_info: tuple[type[BaseException], BaseException, TracebackType | None]
        | tuple[None, None, None],
    ) -> str:
        exception_type, _exception, traceback = exc_info
        if exception_type is None:
            return ""
        frames = extract_tb(traceback) if traceback is not None else []
        locations = "".join(
            f'  File "{Path(frame.filename).name}", line {frame.lineno}, in {frame.name}\n'
            for frame in frames
        )
        safe_trace = locations + f"{exception_type.__name__}: [message suppressed]"
        return redact_text(safe_trace)


class _ErrorsOnly(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.ERROR


def configure_logging(
    data_dir: Path,
    *,
    level: int | str = logging.INFO,
    console: bool = False,
) -> logging.Logger:
    """Configure Dentiva's bounded file logs under the selected local data dir."""
    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(_LOGGER_NAME)
    if isinstance(level, str):
        resolved_level = logging.getLevelName(level.upper())
        if not isinstance(resolved_level, int):
            raise ValueError(f"Unknown logging level: {level}")
    elif isinstance(level, int) and not isinstance(level, bool):
        resolved_level = level
    else:
        raise TypeError("level must be a logging level name or integer")
    logger.setLevel(resolved_level)
    logger.propagate = False

    for handler in tuple(logger.handlers):
        if getattr(handler, "_dentiva_handler", False):
            logger.removeHandler(handler)
            handler.close()

    formatter = RedactingFormatter(
        "%(asctime)s|%(levelname)s|%(name)s|%(error_id)s|%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        defaults={"error_id": "-"},
    )
    app_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=MAX_LOG_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
        delay=True,
    )
    app_handler.setFormatter(formatter)
    app_handler.addFilter(RedactionFilter())
    app_handler._dentiva_handler = True  # type: ignore[attr-defined]
    logger.addHandler(app_handler)

    error_handler = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=MAX_LOG_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
        delay=True,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.addFilter(_ErrorsOnly())
    error_handler.addFilter(RedactionFilter())
    error_handler.setFormatter(formatter)
    error_handler._dentiva_handler = True  # type: ignore[attr-defined]
    logger.addHandler(error_handler)

    if console:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(RedactionFilter())
        stream_handler._dentiva_handler = True  # type: ignore[attr-defined]
        logger.addHandler(stream_handler)
    return logger
