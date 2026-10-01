from pathlib import Path

from scripts.audit_artifact import audit_tree, documented_activation_code


def test_audit_accepts_a_clean_foundation_tree(tmp_path: Path) -> None:
    (tmp_path / "dentiva").mkdir()
    (tmp_path / "dentiva" / "app.bin").write_bytes(b"foundation test artifact")
    assert audit_tree(tmp_path) == []


def test_audit_finds_forbidden_paths_and_activation_input(tmp_path: Path) -> None:
    code = documented_activation_code()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "sample.txt").write_text("not for distribution", encoding="utf-8")
    (tmp_path / "unexpected.bin").write_bytes(code.encode("ascii"))
    problems = audit_tree(tmp_path)
    assert any("forbidden path" in problem for problem in problems)
    assert any("activation input" in problem for problem in problems)
