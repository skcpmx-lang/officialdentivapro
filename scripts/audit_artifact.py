#!/usr/bin/env python3
"""Fail-closed manifest scan for build-tree contents (no product build in Phase 2)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SECURITY_DOC = ROOT / "docs" / "SECURITY.md"
_FORBIDDEN_PARTS = {
    ".env",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "coverage",
    "docs",
    ".git",
    "scripts",
    "tests",
}
_FORBIDDEN_DEBUG = re.compile(rb"\bDEBUG\s*=\s*true\b", re.IGNORECASE)


def documented_activation_code() -> str:
    """Read the owner-approved input from the private planning doc, not this tool."""
    text = _SECURITY_DOC.read_text(encoding="utf-8")
    match = re.search(r"one-time code `([0-9]{16})`", text)
    if match is None:
        raise RuntimeError("Could not locate the activation reference in docs/SECURITY.md")
    return match.group(1)


def _files(target: Path, *, source_tree: bool = False) -> list[Path]:
    if target.is_file():
        return [target]
    paths = (path for path in target.rglob("*") if path.is_file() and not path.is_symlink())
    if source_tree:
        paths = (
            path
            for path in paths
            if "__pycache__" not in path.relative_to(target).parts and path.suffix != ".pyc"
        )
    return sorted(paths)


def audit_tree(
    target: Path, *, activation_code: str | None = None, source_tree: bool = False
) -> list[str]:
    """Return violations for the given tree; an empty list means it passed."""
    if not target.exists():
        return [f"target does not exist: {target}"]
    forbidden = (activation_code or documented_activation_code()).encode("ascii")
    problems: list[str] = []
    for path in _files(target, source_tree=source_tree):
        relative = path.relative_to(target) if target.is_dir() else Path(path.name)
        parts = {part.casefold() for part in relative.parts}
        if parts & _FORBIDDEN_PARTS or path.name.casefold().startswith(".env."):
            problems.append(f"forbidden path: {relative.as_posix()}")
        if path.name.casefold() in {".env", "credentials.json", "secrets.json"}:
            problems.append(f"sensitive file included: {relative.as_posix()}")
        if path.suffix.casefold() == ".py" and not source_tree:
            problems.append(f"loose Python source included: {relative.as_posix()}")
        try:
            with path.open("rb") as stream:
                overlap = b""
                while chunk := stream.read(1024 * 1024):
                    sample = overlap + chunk
                    if forbidden in sample:
                        problems.append(f"activation input found: {relative.as_posix()}")
                        break
                    if _FORBIDDEN_DEBUG.search(sample):
                        problems.append(f"debug build flag found: {relative.as_posix()}")
                        break
                    overlap = sample[-max(len(forbidden), 32) :]
        except OSError as exc:
            problems.append(f"unreadable artifact entry {relative.as_posix()}: {exc}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="directory or file to audit")
    parser.add_argument(
        "--source-tree",
        action="store_true",
        help="dry-run mode: ignore interpreter-generated __pycache__ entries",
    )
    args = parser.parse_args()
    problems = audit_tree(args.target, source_tree=args.source_tree)
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        return 1
    print(
        f"PASS: artifact audit ({len(_files(args.target, source_tree=args.source_tree))} files) — {args.target}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
