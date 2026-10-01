from pathlib import Path

from scripts.extract_i18n import extract_catalog

from dentiva.core.i18n import translate


def test_translation_falls_back_to_source_english() -> None:
    assert translate("Foundation shell") == "Foundation shell"


def test_catalog_extractor_is_deterministic_and_ignores_dynamic_strings(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "screen.py").write_text(
        "title = _(\"Patients\")\nlabel = translate('Patient profile')\nvalue = _(name)\n",
        encoding="utf-8",
    )
    first = extract_catalog(source)
    second = extract_catalog(source)
    assert first == second
    assert 'msgid "Patients"' in first
    assert 'msgid "Patient profile"' in first
    assert "name" not in first
