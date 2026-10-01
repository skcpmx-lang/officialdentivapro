#!/usr/bin/env python3
"""Extract literal ``_()`` and ``translate()`` calls into a deterministic POT file."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "dentiva"
DEFAULT_OUTPUT = SOURCE / "resources" / "i18n" / "messages.pot"


def extract_catalog(source_root: Path) -> str:
    references: dict[str, set[str]] = defaultdict(set)
    for path in sorted(source_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            name = function.id if isinstance(function, ast.Name) else None
            if name not in {"_", "translate"} or not node.args:
                continue
            message = node.args[0]
            if isinstance(message, ast.Constant) and isinstance(message.value, str):
                try:
                    reference = path.resolve().relative_to(ROOT).as_posix()
                except ValueError:
                    reference = path.name
                references[message.value].add(f"{reference}:{node.lineno}")

    lines = [
        'msgid ""',
        'msgstr ""',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Content-Transfer-Encoding: 8bit\\n"',
        '"MIME-Version: 1.0\\n"',
        "",
    ]
    for message in sorted(references):
        refs = " ".join(sorted(references[message]))
        lines.extend(
            (f"#: {refs}", f"msgid {json.dumps(message, ensure_ascii=False)}", 'msgstr ""', "")
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = extract_catalog(args.source)
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            print(f"Catalog is stale: run {Path(__file__).name}", file=sys.stderr)
            return 1
        try:
            display_path = args.output.relative_to(ROOT)
        except ValueError:
            display_path = args.output
        print(f"Catalog is current: {display_path}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
