import logging
from pathlib import Path

from dentiva.bootstrap import logging_setup


def _close_logger() -> None:
    logger = logging.getLogger("dentiva")
    for handler in tuple(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def test_structured_rotating_logs_redact_sensitive_fields(tmp_path: Path) -> None:
    logger = logging_setup.configure_logging(tmp_path, console=False)
    logger.info(
        "password=%s patient_name=%s clinical_note=%s",
        "raw-password",
        "Example Patient",
        "private note text",
        extra={"error_id": "DVT-1234"},
    )
    logger.error("operation rejected", extra={"error_id": "DVT-4321"})
    try:
        raise RuntimeError("unlabelled clinical narrative must not enter ordinary logs")
    except RuntimeError:
        logger.exception("caught application error", extra={"error_id": "DVT-5555"})
    _close_logger()

    app_log = (tmp_path / "logs" / "app.log").read_text(encoding="utf-8")
    error_log = (tmp_path / "logs" / "errors.log").read_text(encoding="utf-8")
    assert "DVT-1234" in app_log
    assert "DVT-4321" in error_log
    assert "raw-password" not in app_log
    assert "Example Patient" not in app_log
    assert "private note text" not in app_log
    assert "unlabelled clinical narrative" not in app_log
    assert "message suppressed" in app_log
    assert app_log.count("[REDACTED]") == 3


def test_rotation_is_bounded_to_seven_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(logging_setup, "MAX_LOG_BYTES", 180)
    logger = logging_setup.configure_logging(tmp_path, console=False)
    for index in range(40):
        logger.info("entry %02d %s", index, "x" * 50)
    _close_logger()
    files = list((tmp_path / "logs").glob("app.log*"))
    assert 1 <= len(files) <= logging_setup.LOG_BACKUP_COUNT + 1
