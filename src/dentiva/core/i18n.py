"""Small gettext seam; the shipped catalog is English until localization work."""

from __future__ import annotations

import gettext
from pathlib import Path


def translation_for(
    locale: str | None = None, *, localedir: Path | None = None
) -> gettext.NullTranslations:
    """Load an optional catalog and fall back to source English strings."""
    languages = [locale] if locale else None
    return gettext.translation(
        "dentiva",
        localedir=str(localedir) if localedir is not None else None,
        languages=languages,
        fallback=True,
    )


def translate(message: str, *, locale: str | None = None) -> str:
    """Translate one message, returning its English source when no catalog exists."""
    return translation_for(locale).gettext(message)


_ = translate
