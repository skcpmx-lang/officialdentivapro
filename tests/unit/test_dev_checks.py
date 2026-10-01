from pathlib import Path

from scripts.dev_checks import _coverage_counts, _test_counts


def test_junit_summary_counts_passed_failed_and_skipped_tests(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    report.write_text(
        '<testsuites><testsuite tests="5" failures="1" errors="1" skipped="1" /></testsuites>',
        encoding="utf-8",
    )
    assert _test_counts(report) == (5, 2, 2, 1)


def test_coverage_summary_counts_lines_and_branches(tmp_path: Path) -> None:
    report = tmp_path / "coverage.xml"
    report.write_text(
        '<coverage lines-valid="100" lines-covered="80" '
        'branches-valid="20" branches-covered="15" />',
        encoding="utf-8",
    )
    assert _coverage_counts(report) == (80, 100, 15, 20)
