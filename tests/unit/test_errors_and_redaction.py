from dentiva.core.errors import (
    BackupIntegrityError,
    ConflictError,
    DentivaError,
    IntegrityError,
    NotFoundError,
    PermissionDeniedError,
    StorageError,
    ValidationError,
)
from dentiva.core.redact import redact_text, redact_value


def test_error_hierarchy_has_stable_codes_and_correlation_ids() -> None:
    errors: list[DentivaError] = [
        ValidationError(),
        PermissionDeniedError(),
        NotFoundError(),
        ConflictError(),
        IntegrityError(),
        BackupIntegrityError(),
        StorageError(),
    ]
    assert len({error.code for error in errors}) == len(errors)
    assert len({error.error_id for error in errors}) == len(errors)
    assert all(error.public_message and error.code.startswith("DVT-") for error in errors)


def test_labelled_sensitive_values_are_redacted_recursively() -> None:
    message = "password=hunter2 patient_name=Example activation_code=0000000000000000"
    redacted = redact_text(message)
    assert "hunter2" not in redacted
    assert "Example" not in redacted
    assert "0000000000000000" not in redacted
    assert "[REDACTED]" in redacted
    assert redact_value({"password_hash": "hash-data", "safe_count": 2}) == {
        "password_hash": "[REDACTED]",
        "safe_count": 2,
    }
