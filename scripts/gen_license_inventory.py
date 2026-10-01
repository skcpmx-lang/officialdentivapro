#!/usr/bin/env python3
"""Generate a lock-derived license inventory and enforce runtime policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from importlib import metadata
from pathlib import Path

from packaging.markers import Marker, default_environment
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "uv.lock"
OUTPUT = ROOT / "THIRD-PARTY-NOTICES.json"
RUNTIME_ALLOWLIST = {
    "MIT",
    "MIT-0",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "PSF-2.0",
    "ISC",
    "Zlib",
    "CC0-1.0",
    "OFL-1.1",
}
KNOWN_LICENSES = RUNTIME_ALLOWLIST | {
    "LGPL-3.0-only",
    "GPL-2.0-only",
    "GPL-3.0-only",
    "MPL-2.0",
}
LGPL_COMPATIBLE = {"pyside6-essentials", "shiboken6"}

_CLASSIFIER_LICENSES = {
    "mit license": "MIT",
    "apache 2.0": "Apache-2.0",
    "apache license, version 2.0": "Apache-2.0",
    "mit-0": "MIT-0",
    "apache software license": "Apache-2.0",
    "bsd license": "BSD-3-Clause",
    "bsd 2-clause license": "BSD-2-Clause",
    "bsd 3-clause license": "BSD-3-Clause",
    "python software foundation license": "PSF-2.0",
    "isc license": "ISC",
    "mozilla public license 2.0 (mpl 2.0)": "MPL-2.0",
    "gnu general public license v3 (gplv3)": "GPL-3.0-only",
    "gnu general public license v2 (gplv2)": "GPL-2.0-only",
    "public domain": "CC0-1.0",
}


def _windows_environment() -> dict[str, str]:
    env = default_environment()
    env.update(
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
    return env


def _selected(dependency: dict[str, object], environment: dict[str, str]) -> bool:
    marker = dependency.get("marker")
    return marker is None or Marker(str(marker)).evaluate(environment)


def _dependency_closure(
    package_map: dict[str, dict[str, object]],
    roots: list[dict[str, object]],
    environment: dict[str, str],
) -> set[str]:
    result: set[str] = set()
    pending = [canonicalize_name(str(dep["name"])) for dep in roots if _selected(dep, environment)]
    while pending:
        name = canonicalize_name(pending.pop())
        if name in result:
            continue
        package = package_map.get(name)
        if package is None:
            raise RuntimeError(f"uv.lock dependency is missing package record: {name}")
        result.add(name)
        dependencies = package.get("dependencies", [])
        pending.extend(
            canonicalize_name(str(dependency["name"]))
            for dependency in dependencies
            if isinstance(dependency, dict) and _selected(dependency, environment)
        )
    return result


def _license_expression(dist: metadata.Distribution) -> str:
    meta = dist.metadata
    expression = meta.get("License-Expression", "").strip()
    if expression:
        return expression
    legacy = meta.get("License", "").strip()
    if legacy and len(legacy) < 100 and "\n" not in legacy:
        normalized = re.sub(r"\s+", " ", legacy).casefold()
        if normalized in _CLASSIFIER_LICENSES:
            return _CLASSIFIER_LICENSES[normalized]
        aliases = {
            "mit": "MIT",
            "apache-2.0": "Apache-2.0",
            "bsd-2-clause": "BSD-2-Clause",
            "bsd-3-clause": "BSD-3-Clause",
            "isc": "ISC",
            "zlib": "Zlib",
        }
        if normalized in aliases:
            return aliases[normalized]
        if re.fullmatch(r"[A-Za-z0-9.+() -]+", legacy):
            return legacy
    classifiers = meta.get_all("Classifier", [])
    for classifier in classifiers:
        prefix = "License :: OSI Approved :: "
        if classifier.startswith(prefix):
            license_name = classifier[len(prefix) :].casefold()
            if license_name in _CLASSIFIER_LICENSES:
                return _CLASSIFIER_LICENSES[license_name]
    return ""


def _expression_ids(expression: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9.-]+", expression)
    operators = {"AND", "OR", "WITH"}
    return {token for token in tokens if token.upper() not in operators}


def _allowed_runtime_license(name: str, expression: str) -> tuple[bool, str]:
    identifiers = _expression_ids(expression)
    if not identifiers or not identifiers <= KNOWN_LICENSES:
        return False, "unknown SPDX identifier"
    if (
        name in LGPL_COMPATIBLE
        and identifiers
        <= {
            "LGPL-3.0-only",
            "GPL-2.0-only",
            "GPL-3.0-only",
        }
        and "LGPL-3.0-only" in identifiers
    ):
        return True, "LGPL-3.0 dynamic-import compliance plan (ADR-019)"
    if identifiers <= RUNTIME_ALLOWLIST:
        return True, "allowlisted"
    return False, "unknown or disallowed runtime license"


def build_inventory() -> tuple[dict[str, object], list[str]]:
    lock_bytes = LOCK.read_bytes()
    lock = tomllib.loads(lock_bytes.decode("utf-8"))
    packages = {
        canonicalize_name(str(package["name"])): package for package in lock.get("package", [])
    }
    root = packages.get("dentiva-pro")
    if root is None:
        return {}, ["uv.lock has no root project package"]
    environment = _windows_environment()
    runtime_names = _dependency_closure(packages, list(root.get("dependencies", [])), environment)
    group_data = root.get("dev-dependencies", {})
    dev_roots = list(group_data.get("dev", [])) if isinstance(group_data, dict) else []
    dev_names = _dependency_closure(packages, dev_roots, environment) - runtime_names
    installed: dict[str, metadata.Distribution] = {}
    for distribution in metadata.distributions():
        name = distribution.metadata.get("Name")
        if name:
            installed[canonicalize_name(name)] = distribution

    problems: list[str] = []
    entries: list[dict[str, str]] = []
    for group, names in (("runtime", runtime_names), ("development-only", dev_names)):
        for name in sorted(names):
            locked = packages[name]
            dist = installed.get(name)
            if dist is None:
                problems.append(f"locked package is not installed for inventory generation: {name}")
                continue
            locked_version = str(locked["version"])
            installed_version = dist.version
            if installed_version != locked_version:
                problems.append(
                    f"installed version differs from uv.lock for {name}: "
                    f"{installed_version} != {locked_version}"
                )
                continue
            license_id = _license_expression(dist)
            if not license_id:
                problems.append(f"license metadata is missing for {name}=={locked_version}")
                continue
            if group == "runtime":
                allowed, policy = _allowed_runtime_license(name, license_id)
                if not allowed:
                    problems.append(
                        f"runtime policy rejected {name}=={locked_version}: {license_id}"
                    )
                    continue
            else:
                identifiers = _expression_ids(license_id)
                if not identifiers or not identifiers <= KNOWN_LICENSES:
                    problems.append(
                        f"development license is unknown for {name}=={locked_version}: {license_id}"
                    )
                    continue
                policy = "development-only; not bundled in product runtime"
            entries.append(
                {
                    "name": str(locked["name"]),
                    "version": locked_version,
                    "license": license_id,
                    "scope": group,
                    "policy": policy,
                }
            )

    inventory = {
        "schema_version": 1,
        "generated_from": "uv.lock",
        "lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "runtime_policy": "ADR-019 allowlist; PySide6 dynamic-import LGPL plan",
        "packages": entries,
    }
    return inventory, problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    inventory, problems = build_inventory()
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        return 1
    rendered = json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            print(
                "FAIL: license inventory is missing or stale; regenerate with scripts/gen_license_inventory.py",
                file=sys.stderr,
            )
            return 1
        print(f"PASS: license inventory ({len(inventory['packages'])} locked packages)")
        return 0
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote {args.output} ({len(inventory['packages'])} locked packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
