import re
from pathlib import Path

import pytest

from dentiva.security import activation


@pytest.mark.security
def test_activation_derivation_vectors_are_stable() -> None:
    vectors = {
        "Dentiva-vector-1": "43440802d7f333d3fef5fa78e443cd45fd86a4307ed35e14ad1ec77ae8ec6225",
        "Dentiva-vector-2": "dc5c7fa500cb5b11e5b09d9aabca4673ce3083750987be3b28b6ec3c948fa117",
        "": "c9cd7acfba14c7384ad8ab0734eb9aeaf60a12844526d8183432c63d8778dff2",
    }
    assert {text: activation.derive_activation_digest(text).hex() for text in vectors} == vectors


def test_candidate_format_and_constant_time_match(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = "1234567890123456"
    monkeypatch.setattr(
        activation, "VERIFICATION_DIGEST", activation.derive_activation_digest(candidate)
    )
    assert activation.verify_activation_code("1234-5678 9012-3456")
    assert not activation.verify_activation_code("1234x567890123456")
    assert not activation.verify_activation_code("12345")


@pytest.mark.security
def test_activation_source_does_not_contain_the_documented_plaintext() -> None:
    root = Path(__file__).resolve().parents[2]
    security_text = (root / "docs" / "SECURITY.md").read_text(encoding="utf-8")
    match = re.search(r"one-time code `([0-9]{16})`", security_text)
    assert match is not None
    assert activation.derive_activation_digest(match.group(1)) == activation.VERIFICATION_DIGEST
    forbidden = match.group(1).encode("ascii")
    for path in (root / "src" / "dentiva").rglob("*"):
        if path.is_file() and path.suffix in {".py", ".json", ".ui", ".qss"}:
            assert forbidden not in path.read_bytes(), f"activation literal found in {path}"
