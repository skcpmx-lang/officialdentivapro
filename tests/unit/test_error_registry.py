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


def test_error_codes_are_stable_and_unique() -> None:
    error_types: tuple[type[DentivaError], ...] = (
        ValidationError,
        PermissionDeniedError,
        NotFoundError,
        ConflictError,
        IntegrityError,
        BackupIntegrityError,
        StorageError,
    )
    codes = [error_type.code for error_type in error_types]
    assert len(codes) == len(set(codes))
    assert all(code.startswith("DVT-") and len(code) == 8 for code in codes)


def test_public_error_message_and_correlation_id_are_available() -> None:
    error = ValidationError()
    assert error.public_message
    assert len(error.error_id) == 36
