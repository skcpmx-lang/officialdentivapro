#!/usr/bin/env python3
"""Generate docs/TRACEABILITY.md from docs/REQUIREMENTS.md (single source of truth).

Phase 1 form: one row per requirement with planned phase, module surface,
frozen acceptance text, and a status token. Later phases extend statuses with
evidence links; this script's --check mode is the CI drift gate (TESTING §6).
"""
import hashlib, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / "docs" / "REQUIREMENTS.md"
OUT = ROOT / "docs" / "TRACEABILITY.md"

AREA_PHASE = {
    "PROD": (1,), "PLAT": (2,), "ACT": (5,), "SETUP": (5,), "AUTH": (5,),
    "RBAC": (3, 5), "UX": (4,), "DPI": (4,), "FONT": (4,), "LOG": (2,),
    "ARCH": (3,), "NAV": (4,), "SHELL": (4,), "DASH": (7, 9),
    "PAT": (6,), "APPT": (7,), "QUEUE": (7,), "VISIT": (8,), "CHART": (8,),
    "TIMELINE": (8,), "FINALIZE": (8,), "CLINLIB": (8,), "TREAT": (8,),
    "RX": (8,), "FORMOPT": (8,), "BILL": (9,), "INV": (10,), "ACC": (10,),
    "STAFF": (5,), "SET": (5,), "DEL": (5,), "ABOUT": (5,), "SEARCH": (13,),
    "NOTIF": (12,), "AUDIT": (3,), "ATT": (6,), "BKP": (12,), "DB": (3,),
    "DATA": (3,), "TXN": (3,), "FILE": (3,), "ERR": (4,), "VAL": (3,),
    "MONEY": (3,), "DATE": (3,), "LOC": (2,), "KBD": (4,), "PRINT": (11,),
    "REPORT": (9, 10), "GOV": (2,), "BUILD": (2,), "QA": (16,), "PERF": (17,),
}
AREA_MODULE = {
    "PROD": "src/dentiva/* (cross-cutting)", "PLAT": "src/dentiva/app.py, bootstrap, resources, installer/",
    "ACT": "src/dentiva/security/activation.py, services/activation, ui/screens/activation",
    "SETUP": "services/setup, ui/screens/wizard", "AUTH": "security/*, services/staff_users, ui/screens/lock",
    "RBAC": "security/permissions.py, services (decorator), ui/state", "UX": "ui/theme, ui/components, resources/icons",
    "DPI": "ui/theme, app.py manifest", "FONT": "resources/fonts, ui/theme, printing/render",
    "LOG": "bootstrap/logging_setup, core/redact", "ARCH": "bootstrap/container.py, core",
    "NAV": "appstate/router, appstate/routes.py", "SHELL": "ui/shell, appstate",
    "DASH": "services/reports (aggregates), ui/screens/dashboard",
    "PAT": "services/patients, domain/patients, data (patients*), ui/screens/patients",
    "APPT": "services/appointments, domain/appointments, ui/screens/appointments",
    "QUEUE": "services/queue, ui/screens/queue", "VISIT": "services/visits, ui/screens/visits",
    "CHART": "domain/chart, services/chart, ui/widgets/chart",
    "TIMELINE": "services/patients (timeline), domain/timeline",
    "FINALIZE": "domain/statuses.py, services/* finalize ops",
    "CLINLIB": "services/clinical_library, data seeds, ui/screens/settings/library",
    "TREAT": "services/treatments, ui/screens/treatments",
    "RX": "services/prescriptions, domain/prescriptions, ui/screens/prescriptions",
    "FORMOPT": "services/prescriptions/options, ui/screens/settings",
    "BILL": "services/billing, services/payments, domain/billing, ui/screens/billing",
    "INV": "services/inventory, domain/inventory, ui/screens/inventory",
    "ACC": "services/accounting, domain/accounting, ui/screens/accounting",
    "STAFF": "services/staff_users, domain/staff, ui/screens/staff, ui/screens/users",
    "SET": "services/settings, ui/screens/settings/*",
    "DEL": "services/policies.py, ui/dialogs/confirm.py, services (destructive ops)",
    "ABOUT": "ui/screens/about", "SEARCH": "services/search, data (FTS), ui/screens/search",
    "NOTIF": "services/notifications (rules), ui/notifications", "AUDIT": "security/audit.py, services/audit, ui/screens/audit",
    "ATT": "attachments/*, services (attachment ops), ui/widgets/files",
    "BKP": "backup/*, services/backup, ui/screens/backup",
    "DB": "data/models.py, data/migrations", "DATA": "core/money.py, data, domain",
    "TXN": "data/uow.py, core/errors.py, app.py (startup recovery)",
    "FILE": "core/files.py (atomic IO)", "ERR": "core/errors.py, ui/error_boundary",
    "VAL": "core/validation.py", "MONEY": "core/money.py", "DATE": "core/datetime_policy.py",
    "LOC": "core/i18n, resources/fonts, ui/theme (fallback)",
    "KBD": "appstate/shortcuts.py, ui (focus policy)",
    "PRINT": "printing/*, ui/screens/preview, services/printing",
    "REPORT": "services/reports, ui/screens/reports",
    "GOV": "docs/, scripts/, .github/, pyproject.toml",
    "BUILD": "scripts/build.py, scripts/audit_artifact.py, installer/, .github/workflows",
    "QA": "tests/**", "PERF": "tests/perf, scripts/gen_stress_db.py",
}
DOC_VERIFIED = {  # deliverable-of-this-phase governance rows (evidence = doc set itself)
    "REQ-GOV-02", "REQ-GOV-04", "REQ-GOV-05", "REQ-GOV-07",
    "REQ-ACT-03", "REQ-PROD-04", "REQ-PROD-05",
}

row_re = re.compile(r"^\|\s*(REQ-[A-Z]+-\d+)\s*\|\s*([MSCA])\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$", re.M)

def parse():
    text = REQ.read_text(encoding="utf-8")
    out = []
    for m in row_re.finditer(text):
        rid, moscow, req, ac, dep = m.groups()
        out.append((rid, moscow, req, ac, dep))
    return out

def main():
    reqs = parse()
    ids = [r[0] for r in reqs]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        print(f"FATAL: duplicate REQ ids: {sorted(dup)}", file=sys.stderr); sys.exit(1)
    if "--check" in sys.argv:
        if not OUT.exists():
            print("FATAL: TRACEABILITY.md missing", file=sys.stderr); sys.exit(1)
        ttext = OUT.read_text(encoding="utf-8")
        missing = [i for i in ids if f"| {i} " not in ttext]
        extra_ids = set(re.findall(r"REQ-[A-Z]+-\d+", ttext)) - set(ids)
        # extra ids in TRACE may exist only as prose references; flag matrix rows only
        bad_extra = [e for e in extra_ids if re.search(rf"\|\s*{e}\s*\|", ttext)]
        if missing or bad_extra:
            print(f"FATAL: missing rows={missing} orphan rows={bad_extra}", file=sys.stderr); sys.exit(1)
        print(f"OK: {len(ids)} requirements ⇔ {len(ids)} traceability rows")
        return

    lines = [
        "# Dentiva Pro — Requirements Traceability Matrix (living)",
        "",
        "Generated from `docs/REQUIREMENTS.md` (regenerate: `python3 scripts/gen_traceability.py`;",
        "CI gate: `--check`). **One row per requirement — completeness is mechanical, not editorial.**",
        "",
        "Status vocabulary (REQUIREMENTS.md header): `Planned(Pn)` → `Building` → `Implemented-Unverified`",
        "→ `Verified(+evidence: run URL/test output)` → `Verified-Release-Ready` (audit-confirmed).",
        "`Verified(docs)` = the requirement's deliverable in this phase is documentation/policy itself;",
        "tooling enforcement lands with the Phase 2 CI script (same-name check + evidence links).",
        "",
        "AC hash = first 10 hex of SHA-256 over the acceptance-criteria text; a change in any AC",
        "flips the hash → row must re-pass its phase gate. Evidence links appended after the hash on",
        "verification never alter it.",
        "",
        "| REQ | Summary | Phase | Implementation surface | AC (frozen) | ACH | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for rid, moscow, req, ac, dep in reqs:
        area = rid.split("-")[1]
        phase = AREA_PHASE.get(area, (20,))[0]
        module = AREA_MODULE.get(area, "TBD")
        ach = hashlib.sha256(ac.encode()).hexdigest()[:10]
        status = "Verified(docs) [Phase 1]" if rid in DOC_VERIFIED else f"Planned(P{phase})"
        summary = re.sub(r"\*\*|\[GAP→addition\]", "", req).strip()
        if len(summary) > 110:
            summary = summary[:107].rsplit(" ", 1)[0] + "…"
        ac_c = ac.replace("**", "").strip()
        if len(ac_c) > 200:
            ac_c = ac_c[:197].rsplit(" ", 1)[0] + "…"
        lines.append(f"| {rid} | {summary} | P{phase} | {module} | {ac_c} | `{ach}` | {status} |")
    lines += [
        "",
        "## Matrix maintenance rules",
        "",
        "1. Never hand-edit a row's REQ/Summary/Phase columns — edit the register and regenerate.",
        "   `Status` and `Evidence` (suffix after ACH in Status cell, separated by ` — `) are the only",
        "   human-updated fields, updated at each phase gate from executed runs.",
        "2. A row reaches `Verified` only with: test name(s) executed, runner id/CI run URL, and date.",
        "3. Phase completion (ROADMAP acceptance) requires every row scheduled for that phase at",
        "   least `Implemented-Unverified`→`Verified` as applicable; audits move rows to",
        "   `Verified-Release-Ready`.",
        "4. Phase 19 re-reads the master prompt and this matrix line-by-line; any non-green row other",
        "   than an explicitly owner-accepted documented limitation blocks release.",
        "",
        f"Totals: {len(reqs)} requirements. Documentation-verified in Phase 1: {sum(1 for r in reqs if r[0] in DOC_VERIFIED)}.",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(reqs)} rows")

if __name__ == "__main__":
    main()
