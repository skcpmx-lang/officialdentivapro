import json
import socket
from pathlib import Path

from dentiva.bootstrap.diagnostics import write_diagnostic_bundle
from dentiva.core.errors import ValidationError


def test_crash_bundle_contains_error_identity_but_not_exception_payload(
    tmp_path: Path, monkeypatch
) -> None:
    def forbidden_socket(*args, **kwargs):
        raise AssertionError("diagnostics must never open a network socket")

    monkeypatch.setattr(socket, "socket", forbidden_socket)
    try:
        raise ValidationError("clinical_note: confidential patient narrative")
    except ValidationError as error:
        bundle = write_diagnostic_bundle(error, tmp_path, version="test-version")

    payload = json.loads(bundle.read_text(encoding="utf-8"))
    assert payload["version"] == "test-version"
    assert payload["error_code"] == "DVT-1001"
    assert payload["error_id"]
    assert payload["exception_type"] == "ValidationError"
    assert payload["stack"]
    serialized = bundle.read_text(encoding="utf-8")
    assert "confidential patient narrative" not in serialized
    assert "clinical_note" not in serialized
