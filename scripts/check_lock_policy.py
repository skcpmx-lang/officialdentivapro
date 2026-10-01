#!/usr/bin/env python3
"""Verify exact pins and CPython 3.12 Windows x64 wheels from uv.lock."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlparse

from packaging.utils import parse_wheel_filename

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "uv.lock"
PROJECT = ROOT / "pyproject.toml"


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).casefold()


def _selected(dependency: dict[str, object], environment: dict[str, str]) -> bool:
    marker = dependency.get("marker")
    if marker is None:
        return True
    from packaging.markers import Marker

    return Marker(str(marker)).evaluate(environment)


def _windows_environment() -> dict[str, str]:
    from packaging.markers import default_environment

    environment = default_environment()
    environment.update(
        {
            "implementation_name": "cpython",
            "platform_machine": "AMD64",
            "platform_python_implementation": "CPython",
            "platform_release": "10",
            "platform_system": "Windows",
            "platform_version": "10.0.0",
            "python_full_version": "3.12.10",
            "python_version": "3.12",
            "sys_platform": "win32",
        }
    )
    return environment


def _closure(
    package_map: dict[str, dict[str, object]], roots: list[dict[str, object]], env: dict[str, str]
) -> set[str]:
    visited: set[str] = set()
    pending = [str(dep["name"]) for dep in roots if _selected(dep, env)]
    while pending:
        name = _normalize(pending.pop())
        if name in visited:
            continue
        package = package_map.get(name)
        if package is None:
            raise RuntimeError(f"uv.lock dependency is missing package record: {name}")
        visited.add(name)
        dependencies = package.get("dependencies", [])
        pending.extend(
            str(dep["name"])
            for dep in dependencies
            if isinstance(dep, dict) and _selected(dep, env)
        )
    return visited


def _supports_cp312_windows(filename: str) -> bool:
    try:
        _, _, _, tags = parse_wheel_filename(Path(urlparse(filename).path).name)
    except ValueError:
        return False
    for tag in tags:
        if tag.platform == "any" and tag.interpreter in {"py3", "py2.py3", "py2"}:
            return True
        if tag.platform == "win_amd64":
            if tag.interpreter in {"py3", "py2.py3", "py2"} and tag.abi == "none":
                return True
            if tag.interpreter == "cp312" and tag.abi in {"cp312", "abi3"}:
                return True
            if tag.interpreter.startswith("cp") and tag.abi == "abi3":
                try:
                    version = int(tag.interpreter[2:])
                except ValueError:
                    continue
                if 39 <= version <= 312:
                    return True
    return False


def check_lock() -> list[str]:
    project = tomllib.loads(PROJECT.read_text(encoding="utf-8"))
    lock = tomllib.loads(LOCK.read_text(encoding="utf-8"))
    project_config = project["project"]
    failures: list[str] = []
    if project_config.get("requires-python") != ">=3.12,<3.13":
        failures.append(
            "project.requires-python must pin the supported interpreter line to CPython 3.12"
        )
    if lock.get("requires-python") != ">=3.12, <3.13":
        failures.append("uv.lock does not declare the same CPython 3.12 support range")
    requirements = list(project_config.get("dependencies", []))
    for group in project.get("dependency-groups", {}).values():
        requirements.extend(group)
    for requirement in requirements:
        if "==" not in requirement:
            failures.append(f"dependency is not exactly pinned: {requirement}")
    package_map = {_normalize(package["name"]): package for package in lock.get("package", [])}
    root = package_map.get(_normalize(project_config["name"]))
    if root is None:
        return failures + ["uv.lock has no root project record"]
    environment = _windows_environment()
    roots: list[dict[str, object]] = list(root.get("dependencies", []))
    groups = root.get("dev-dependencies", {})
    if isinstance(groups, dict):
        roots.extend(groups.get("dev", []))
    packages = _closure(package_map, roots, environment)
    for name in sorted(packages):
        package = package_map[name]
        wheels = package.get("wheels", [])
        compatible = [
            wheel["url"]
            for wheel in wheels
            if isinstance(wheel, dict) and _supports_cp312_windows(str(wheel.get("url", "")))
        ]
        if not compatible:
            failures.append(
                f"no CPython 3.12 Windows x64 wheel locked for {package['name']}=={package['version']}"
            )
    if not failures:
        print(
            f"PASS: {len(packages)} locked runtime/dev packages have CPython 3.12 Windows x64 wheels"
        )
    return failures


def main() -> int:
    failures = check_lock()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
