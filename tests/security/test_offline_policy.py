import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "dentiva"


class TestNoNetworkImports:
    def test_runtime_source_does_not_import_network_clients(self) -> None:
        blocked = {"requests", "httpx", "urllib", "http", "aiohttp", "websockets", "socket"}
        for path in SRC.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            assert not imported & blocked, f"network import in {path}: {imported & blocked}"

    def test_runtime_import_surface_is_local_or_standard_library(self) -> None:
        allowed_external = {"PySide6", "sqlalchemy", "alembic", "argon2"}
        stdlib = sys.stdlib_module_names
        for path in SRC.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            unexpected = imported - stdlib - allowed_external - {"dentiva"}
            assert not unexpected, f"unlocked runtime import in {path}: {unexpected}"
