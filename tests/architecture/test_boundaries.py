import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "dentiva"
SCREEN_PACKAGES = {
    "dashboard",
    "patients",
    "patient_detail",
    "appointments",
    "queue",
    "visits",
    "visit_detail",
    "prescriptions",
    "treatments_catalog",
    "referrals",
    "chart",
    "invoices",
    "invoice_detail",
    "payments",
    "inventory",
    "accounting",
    "staff",
    "users_roles",
    "settings",
    "clinical_library",
    "backup_restore",
    "audit_log",
    "reports",
    "about",
    "search",
    "activation",
    "wizard",
}
SERVICE_PACKAGES = {
    "patients",
    "visits",
    "chart",
    "clinical_library",
    "treatments",
    "prescriptions",
    "appointments",
    "queue",
    "billing",
    "payments",
    "inventory",
    "accounting",
    "staff_users",
    "settings",
    "notifications",
    "search",
    "reports",
    "audit",
    "backup",
    "activation",
    "setup",
}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


class TestArchitectureConformance:
    def test_documented_module_and_workflow_tree_exists(self) -> None:
        expected_modules = {
            "bootstrap",
            "core",
            "domain",
            "data",
            "services",
            "security",
            "printing",
            "backup",
            "attachments",
            "appstate",
            "ui",
            "resources",
        }
        assert expected_modules <= {path.name for path in SRC.iterdir() if path.is_dir()}
        assert {
            path.name for path in (SRC / "services").iterdir() if path.is_dir()
        } >= SERVICE_PACKAGES
        assert {
            path.name for path in (SRC / "ui" / "screens").iterdir() if path.is_dir()
        } >= SCREEN_PACKAGES
        assert (SRC / "data" / "migrations" / "versions" / "0001_foundation_baseline.py").is_file()
        assert {"fonts", "icons", "seeds", "notices", "i18n"} <= {
            path.name for path in (SRC / "resources").iterdir() if path.is_dir()
        }
        assert {
            "unit",
            "integration",
            "gui",
            "security",
            "printing",
            "perf",
            "chaos",
            "fixtures",
        } <= {path.name for path in (ROOT / "tests").iterdir() if path.is_dir()}
        assert (ROOT / ".github" / "workflows" / "quality.yml").is_file()
        assert (ROOT / ".github" / "workflows" / "release.yml").is_file()
        assert (ROOT / "scripts" / "dev_checks.py").is_file()
        assert (ROOT / "installer" / "README.md").is_file()
        assert (ROOT / "pyproject.toml").is_file()
        assert (ROOT / "uv.lock").is_file()

    def test_domain_layer_imports_standard_library_only(self) -> None:
        for path in (SRC / "domain").rglob("*.py"):
            roots = imported_roots(path)
            assert roots <= sys.stdlib_module_names, (
                f"non-stdlib import in {path}: {roots - sys.stdlib_module_names}"
            )

    def test_ui_does_not_import_data_or_service_implementation(self) -> None:
        forbidden = {"sqlalchemy", "sqlite3"}
        for path in (SRC / "ui").rglob("*.py"):
            roots = imported_roots(path)
            assert not roots & forbidden, f"database import in UI module: {path}"
            source = path.read_text(encoding="utf-8")
            assert "dentiva.data" not in source, f"direct data-layer import in {path}"
            assert "dentiva.services" not in source, f"direct service import in {path}"

    def test_source_has_no_todo_or_placeholder_markers(self) -> None:
        banned = ("TODO", "FIXME", "placeholder")
        for path in SRC.rglob("*"):
            if path.is_file() and path.suffix == ".py":
                text = path.read_text(encoding="utf-8").casefold()
                for marker in banned:
                    assert marker.casefold() not in text, f"{marker} marker in {path}"
