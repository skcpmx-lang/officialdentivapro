import hashlib
from pathlib import Path

from scripts import gen_traceability


def _status_for(rendered: str, requirement_id: str) -> str:
    row = next(line for line in rendered.splitlines() if line.startswith(f"| {requirement_id} |"))
    return row.strip("|").split("|")[-1].strip()


def test_generator_preserves_status_when_acceptance_hash_is_unchanged(
    tmp_path: Path, monkeypatch
) -> None:
    requirement_id = "REQ-PROD-04"
    acceptance = "documentation acceptance remains the same"
    digest = hashlib.sha256(acceptance.encode()).hexdigest()[:10]
    matrix = tmp_path / "TRACEABILITY.md"
    matrix.write_text(
        f"| {requirement_id} | summary | P1 | surface | acceptance | `{digest}` | "
        "Verified(docs) [Phase 1] |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(gen_traceability, "OUT", matrix)

    rendered = gen_traceability.render([(requirement_id, "M", "summary", acceptance, "—")])

    assert _status_for(rendered, requirement_id) == "Verified(docs) [Phase 1]"


def test_generator_resets_status_when_acceptance_hash_changes(tmp_path: Path, monkeypatch) -> None:
    requirement_id = "REQ-PROD-04"
    matrix = tmp_path / "TRACEABILITY.md"
    matrix.write_text(
        f"| {requirement_id} | summary | P1 | surface | old AC | `{'0' * 10}` | "
        "Verified(docs) [Phase 1] |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(gen_traceability, "OUT", matrix)

    rendered = gen_traceability.render(
        [(requirement_id, "M", "summary", "changed acceptance", "—")]
    )

    assert _status_for(rendered, requirement_id) == "Planned(P1)"
