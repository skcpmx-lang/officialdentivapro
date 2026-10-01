from pathlib import Path

from scripts.extract_i18n import extract_catalog


def test_checked_in_catalog_matches_current_sources() -> None:
    root = Path(__file__).resolve().parents[2]
    target = root / "src" / "dentiva" / "resources" / "i18n" / "messages.pot"
    assert target.read_text(encoding="utf-8") == extract_catalog(root / "src" / "dentiva")
