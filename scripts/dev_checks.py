#!/usr/bin/env python3
"""Run the repository's fail-closed development quality gates."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(label: str, command: list[str], *, env: dict[str, str] | None = None) -> int:
    print(f"\n== {label} ==", flush=True)
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, check=False)
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    if result.returncode:
        detail = f"FAIL: {label} exited with status {result.returncode}"
        print(detail, file=sys.stderr)
        if os.environ.get("GITHUB_ACTIONS") == "true":
            lines = (result.stdout + "\n" + result.stderr).splitlines()
            for line in lines[-12:]:
                message = line.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
                print(f"::error title={label}::{message}")
            summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
            if summary_path:
                with Path(summary_path).open("a", encoding="utf-8") as stream:
                    stream.write(f"\n### Failed gate: {label}\n\n```text\n")
                    stream.write("\n".join(lines[-40:]))
                    stream.write("\n```\n")
    else:
        print(f"PASS: {label}")
        if label == "pytest suite":
            _publish_test_evidence(ROOT / "test-results.xml", ROOT / "coverage.xml")
    return result.returncode


def _test_counts(path: Path) -> tuple[int, int, int, int]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    tests = sum(int(suite.attrib.get("tests", 0)) for suite in suites)
    failures = sum(int(suite.attrib.get("failures", 0)) for suite in suites)
    errors = sum(int(suite.attrib.get("errors", 0)) for suite in suites)
    skipped = sum(int(suite.attrib.get("skipped", 0)) for suite in suites)
    return tests, tests - failures - errors - skipped, failures + errors, skipped


def _coverage_counts(path: Path) -> tuple[int, int, int, int]:
    root = ET.parse(path).getroot()
    lines_valid = int(root.attrib.get("lines-valid", 0))
    lines_covered = int(root.attrib.get("lines-covered", 0))
    branches_valid = int(root.attrib.get("branches-valid", 0))
    branches_covered = int(root.attrib.get("branches-covered", 0))
    return lines_covered, lines_valid, branches_covered, branches_valid


def _publish_test_evidence(junit_path: Path, coverage_path: Path) -> None:
    details: list[str] = []
    markdown = ["### Phase 2 automated test evidence", ""]
    if junit_path.exists():
        tests, passed, failed, skipped = _test_counts(junit_path)
        details.append(f"pytest: {passed}/{tests} passed, {failed} failed, {skipped} skipped")
        markdown.append(
            f"- Pytest: **{passed}/{tests} passed**, {failed} failed, {skipped} skipped."
        )
    if coverage_path.exists():
        lines_covered, lines_valid, branches_covered, branches_valid = _coverage_counts(
            coverage_path
        )
        line_percent = 100 * lines_covered / lines_valid if lines_valid else 0.0
        branch_percent = 100 * branches_covered / branches_valid if branches_valid else 0.0
        details.append(
            f"coverage: lines {line_percent:.1f}% ({lines_covered}/{lines_valid}), "
            f"branches {branch_percent:.1f}% ({branches_covered}/{branches_valid})"
        )
        markdown.append(
            f"- Coverage: lines **{line_percent:.1f}%** ({lines_covered}/{lines_valid}); "
            f"branches **{branch_percent:.1f}%** ({branches_covered}/{branches_valid})."
        )
    if not details:
        return
    message = "; ".join(details)
    print(f"TEST_EVIDENCE: {message}")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        annotation = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::notice title=Phase 2 test evidence::{annotation}")
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            with Path(summary_path).open("a", encoding="utf-8") as stream:
                stream.write("\n".join(markdown) + "\n")


def prove_lint_gate_fails_on_a_deliberate_red_fixture() -> int:
    """Show that the exact Ruff checker used in CI rejects a broken fixture."""
    with tempfile.TemporaryDirectory(prefix="dentiva-red-branch-") as directory:
        fixture = Path(directory) / "broken_gate_fixture.py"
        fixture.write_text("import os\n\nprint('gate probe')\n", encoding="utf-8")
        command = [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--isolated",
            "--select",
            "F401",
            str(fixture),
        ]
        result = subprocess.run(command, cwd=directory, capture_output=True, text=True, check=False)
        if result.returncode == 0 or "F401" not in result.stdout:
            print("FAIL: deliberate red-branch fixture was not rejected by Ruff", file=sys.stderr)
            if result.stdout:
                print(result.stdout, file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1
        print("PASS: deliberate F401 red-branch fixture produced a non-zero lint result")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--failure-probe",
        action="store_true",
        help="run only the expected-red lint gate proof and exit",
    )
    args = parser.parse_args()
    if args.failure_probe:
        return prove_lint_gate_fails_on_a_deliberate_red_fixture()

    environment = os.environ.copy()
    environment.setdefault("QT_QPA_PLATFORM", "offscreen")
    environment.setdefault("PYTHONUTF8", "1")
    commands = [
        ("Ruff lint", [sys.executable, "-m", "ruff", "check", "src", "tests", "scripts"]),
        (
            "Ruff format",
            [sys.executable, "-m", "ruff", "format", "--check", "src", "tests", "scripts"],
        ),
        ("mypy", [sys.executable, "-m", "mypy"]),
        ("traceability drift", [sys.executable, "scripts/gen_traceability.py", "--check"]),
        ("i18n catalog drift", [sys.executable, "scripts/extract_i18n.py", "--check"]),
        ("CPython 3.12 Windows wheel policy", [sys.executable, "scripts/check_lock_policy.py"]),
        (
            "lock-derived license inventory",
            [sys.executable, "scripts/gen_license_inventory.py", "--check"],
        ),
        (
            "foundation artifact audit",
            [sys.executable, "scripts/audit_artifact.py", "--source-tree", "src/dentiva"],
        ),
        (
            "pytest suite",
            [
                sys.executable,
                "-m",
                "pytest",
                "--junitxml=test-results.xml",
                "--cov-report=xml:coverage.xml",
            ],
        ),
    ]
    for label, command in commands:
        if _run(label, command, env=environment):
            return 1
    print("\nAll configured development checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
