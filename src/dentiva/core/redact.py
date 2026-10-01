"""Redaction helpers for labelled sensitive data at logging boundaries."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

_REDACTED = "[REDACTED]"
_SENSITIVE_LABEL = re.compile(
    r"(?i)(?P<label>\b(?:password|passwd|pwd|secret|token|activation(?:[_ -]?code)?|"
    r"patient[_ -]?(?:name|id)|clinical[_ -]?(?:text|note)|diagnosis|"
    r"prescription[_ -]?text|hash(?:[_ -]?digest)?)\b\s*[:=]\s*)"
    r'(?P<value>"[^"]*"|\'[^\']*\'|[^\s,;]+)'
)


def redact_text(value: str) -> str:
    """Mask values attached to known sensitive labels in a log message."""
    masked = _SENSITIVE_LABEL.sub(lambda match: match.group("label") + _REDACTED, value)
    return masked.replace("\r", "\\r").replace("\n", "\\n")


def redact_value(value: Any) -> Any:
    """Recursively redact labelled fields in structured values."""
    if isinstance(value, Mapping):
        result: dict[Any, Any] = {}
        for key, item in value.items():
            normalized = str(key).casefold().replace("-", "_").replace(" ", "_")
            if any(
                marker in normalized
                for marker in (
                    "password",
                    "passwd",
                    "secret",
                    "token",
                    "activation",
                    "patient_name",
                    "patient_id",
                    "clinical",
                    "diagnosis",
                    "prescription_text",
                    "hash",
                )
            ):
                result[key] = _REDACTED
            else:
                result[key] = redact_value(item)
        return result
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [redact_value(item) for item in value]
    return value
