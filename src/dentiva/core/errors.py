"""Stable, user-safe application error types."""

from __future__ import annotations

from uuid import uuid4


class DentivaError(Exception):
    """Base for errors that may cross an application boundary."""

    code = "DVT-0000"
    default_public_message = "The operation could not be completed."

    def __init__(self, public_message: str | None = None, *, error_id: str | None = None) -> None:
        self.public_message = public_message or self.default_public_message
        self.error_id = error_id or str(uuid4())
        super().__init__(self.public_message)


class ValidationError(DentivaError):
    code = "DVT-1001"
    default_public_message = "Some information is invalid. Check the highlighted fields."


class PermissionDeniedError(DentivaError):
    code = "DVT-1002"
    default_public_message = "You do not have permission to perform this operation."


class NotFoundError(DentivaError):
    code = "DVT-1003"
    default_public_message = "The requested record could not be found."


class ConflictError(DentivaError):
    code = "DVT-1004"
    default_public_message = "The operation conflicts with the current record state."


class IntegrityError(DentivaError):
    code = "DVT-1005"
    default_public_message = "The data integrity check failed."


class BackupIntegrityError(IntegrityError):
    code = "DVT-1006"
    default_public_message = "The backup could not be verified."


class StorageError(DentivaError):
    code = "DVT-1007"
    default_public_message = "The local data store could not be accessed."


class InstanceAlreadyRunningError(DentivaError):
    code = "DVT-1008"
    default_public_message = "Dentiva Pro is already running for this data directory."
