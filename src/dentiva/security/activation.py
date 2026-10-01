"""Offline activation derivation; the source contains no activation input."""

from __future__ import annotations

import hashlib
import hmac
import re

_LEGACY_SALT = b"dvp.legacy.2026:"
_LEGACY_SUFFIX = b":dvp"
_PURPOSE_SALT = b"dvp.act.v1:"
_PRODUCT_TAG = b"dentiva-pro:1.0"

# Generated from the documented derivation. This is a deterrence-grade verifier,
# not a secret; SECURITY.md records the reverse-engineering limitation.
VERIFICATION_DIGEST = bytes.fromhex(
    "08f785cce871e63eb9bb513ea8c55f789a5f315dca93737620a20cee9749e5bd"
)
_CODE_FORMAT = re.compile(r"[0-9]{16}\Z", re.ASCII)


def derive_activation_digest(value: str) -> bytes:
    """Derive the fixed-size verifier from a candidate using the ADR-010 recipe."""
    if not isinstance(value, str):
        raise TypeError("Activation candidate must be text")
    inner = hashlib.sha256(_LEGACY_SALT + value.encode("utf-8") + _LEGACY_SUFFIX).digest()
    return hashlib.sha256(_PURPOSE_SALT + inner + _PRODUCT_TAG).digest()


def normalize_activation_candidate(value: str) -> str:
    """Remove presentation whitespace and hyphens; leave all other text intact."""
    return "".join(character for character in value if not character.isspace() and character != "-")


def verify_activation_code(candidate: str) -> bool:
    """Constant-time verifier for a 16-digit candidate after presentation cleanup."""
    normalized = normalize_activation_candidate(candidate)
    if not _CODE_FORMAT.fullmatch(normalized):
        return False
    return hmac.compare_digest(derive_activation_digest(normalized), VERIFICATION_DIGEST)
