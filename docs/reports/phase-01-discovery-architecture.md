# Phase 01 — Product discovery, requirements normalization, risk analysis, architecture strategy & implementation plan

- Owner directive: initial (session start; master product prompt)
- Branch/commit range: `777f1ee` (initial commit) → Phase 1 documentation set (this commit)
- Objective: understand the entire product concept; normalize every requirement; identify dependencies and missing production requirements; choose and justify the full stack; define architecture, data, security, printing, backup, testing, installer, CI, and release strategy; establish acceptance criteria; produce a complete requirements→module→test traceability matrix; deliver the phase report. **No production UI code in this phase** (per mandate).

## Work completed

1. **Requirement normalization.** The master prompt was read end-to-end and normalized into **254 requirement IDs across 44 areas** in `docs/REQUIREMENTS.md`, each with MoSCoW class, acceptance criteria, and dependency links. A coverage manifest maps every master-prompt theme to requirement IDs; gap analysis added ~20 missing-but-mandatory production requirements (archive policies, restart-persistence guarantee, single-writer lock, text normalization, performance budgets, streaming exports, duplicate-patient review, working-hours policy, crash bundles, backup destination health, etc.).
2. **Conflict & risk analysis.** `docs/CONFLICTS-DECISIONS.md`: 11 requirement conflicts (C1–C11) with binding professional interpretations; 5 environment/capability constraints (D1–D5) — including the honest Linux-headless sandbox limitation and offline-activation cryptographic ceiling; 9 product-owner decisions (O1–O9) with adopted defaults so nothing blocks; explicit non-goals list. No requirement was silently dropped or substituted.
3. **Technology stack selection with rationale.** 19 ADRs (`docs/adr/`) covering: CPython 3.12 pin (wheel-availability reasoning incl. sqlcipher cp312 ceiling), PySide6/Qt6 + QSS-token design system (license economics vs PyQt; rejected Tk/wx/Kivy/QML/webview with reasons), SQLite WAL hardened w/ documented residual risk + SQLCipher seam, SQLAlchemy 2 + Alembic (peewee/raw-sqlite documented as runners-up), integer-poisha money model, layered monolith + conformance tests, threading (pool, not asyncio/qasync), Argon2id auth (calibration tiers), permission-code RBAC + hash-chained audit (deny-by-default AST gate), derived-hash activation with honest limits, custom Qt print/PDF/preview single-renderer engine (ReportLab/QTextDocument/WeasyPrint rejected with reasons), `.dvpkg` backup container + journal-safe restore, content-addressed attachments, OFL font bundling with coverage gates, PyInstaller onedir (Nuitka/cx_Freeze considered), Inno Setup **6.4.3 pinned for commercial-use license compatibility** (6.5+ moved commercial licensing — researched and recorded), CI/CD two-workflow fail-loud design, legal/license inventory automation.
4. **Architecture definitions.** `docs/ARCHITECTURE.md`: repo/module layout, one-way dependency rules, startup state machine (lock→pragmas→integrity→activation→setup→login), app-state model, route/permission registry, subsystem contracts (UoW/audit/settings/attachments/notifications/search/backup hooks), error model & logging policy, file layout, money/time conventions, performance budgets (REQ-PERF-01..07 as normative numbers).
5. **Database design.** `docs/DATABASE.md`: complete table inventory (~55 tables/views) with PKs, FKs + cascade policy table, CHECK-enforced status domains, index spec, FTS plan, sequences, snapshot semantics (historical vs current, the prompt's phone-number/designation examples encoded as `snapshot_json` rules), permission catalog + role seeds (incl. the exact "invoice+payment entry without financial reports" role), migration/versioning strategy, seeds list (treatment catalog deliberately empty — no fake records), deletion policy table.
6. **Security model.** `docs/SECURITY.md`: trust boundary doctrine (service layer only), activation threat statement, auth/lock/step-up, RBAC enforcement + bypass test program, audit chain + honest ceiling, attachment/path surface, residual-risk table, logging redaction.
7. **Printing architecture.** `docs/PRINTING.md`: single-renderer pipeline (model→layout(PagePlan)→3 sinks), block model, width-class & pagination rules incl. signature-zone hard reservation with layout-time assertion, printer/paper profile integration incl. thermal/Bluetooth posture, preview = actual output by construction, PDF embedding, Bengali shaping/coverage verification protocol, golden corpus, failure policy, hardware-honesty protocol.
8. **Backup architecture.** `docs/BACKUP.md`: `.dvpkg` container spec (manifest schema example), naming, atomic creation protocol, validation tooling contract, 9-stage journal-safe restore protocol (pre-restore safety backup, activation-travels policy, multi-file sequential policy, interruption recovery), scheduler/retention, self-containment table + CI completeness test definition.
9. **Testing strategy.** `docs/TESTING.md`: tier map, determinism contract (injected clock, no-sleep rule, socket-block proving offline), fault-injection/kill-soak harness, GUI offscreen method, security program (generated authz matrix CSV), requirement-linked test naming + traceability CI check, stress dataset spec & budgets, print/PDF validation, clean-machine protocol (full suite re-run **against the installed artifact**), "what passed means" wording rules.
10. **Installer/CI/release strategy.** `docs/BUILD-RELEASE.md`: versioning/buildinfo, lock+wheel-platform policy, release pipeline step list incl. artifact audit rules, installer contract (data-preserving uninstall with typed opt-in), unsigned-build/SmartScreen honesty, GitHub-Release-with-`dist/`-fallback procedure, exact-artifact verification rule (tested-hash == published-hash), reproducibility scope statement, dev/release parity, upgrade/rollback posture for a final non-upgrade product.
11. **Execution plan.** `docs/ROADMAP.md`: Phases 2–20 each with deliverables/acceptance criteria/exit gates, resume-after-interruption protocol (§0), dependency spine rationale, cross-phase invariants. `docs/PHASE-REPORTS.md`: mandatory report template + index.
12. **Traceability foundation.** `docs/TRACEABILITY.md`: all **254 rows** seeded with phase, module surface, frozen acceptance text + AC-hash (changing any AC flips the hash and forces the owning phase gate to re-pass), and status vocabulary (`Planned(Pn)`…`Verified-Release-Ready`). Generated mechanically from the register by `scripts/gen_traceability.py`; `--check` mode is the bidirectional CI drift gate (proven green this phase: 254 ⇔ 254).
13. **Repository hygiene.** README (with explicit "no working application yet" notice — honesty rule), .gitignore, proprietary LICENSE, `dist/README.md` fallback contract.

## Files/modules created or modified

- `README.md` (rewritten as product+doc index), `LICENSE`, `.gitignore`, `dist/README.md`
- `docs/REQUIREMENTS.md`, `docs/CONFLICTS-DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/DATABASE.md`, `docs/SECURITY.md`, `docs/PRINTING.md`, `docs/BACKUP.md`, `docs/TESTING.md`, `docs/BUILD-RELEASE.md`, `docs/ROADMAP.md`, `docs/PHASE-REPORTS.md`, `docs/TRACEABILITY.md`
- `docs/adr/README.md` + `ADR-001…ADR-019` (19 records)
- `docs/reports/phase-01-discovery-architecture.md` (this file)

## Database changes — UI changes

None (no implementation yet — by phase mandate).

## Tests executed

No application test suite exists to execute yet. Verification performed in this phase (executed, not claimed):

| check | result |
|---|---|
| Register internal consistency: every referenced REQ ID defined (scripted cross-ref over `docs/REQUIREMENTS.md`) | pass — 3 missing IDs (REQ-TIMELINE-01, REQ-FINALIZE-01, REQ-ARCH/NAV block) found and fixed same turn |
| Traceability row coverage: every REQ ID in register ⇔ one matrix row (generated + verified) | pass (0 gaps after generation) |
| ADR index ⇔ files cross-check (titles/links) | pass (1 filename mismatch found & fixed) |
| Key stack facts validated against live sources (searches on 2026-10-01): PySide6 LGPL tri-license; Inno 6.4.x free-for-commercial vs 6.5+ paid; sqlcipher3-wheels cp312 Win wheels; ReportLab BSD; PyInstaller GPL-exception; Qt HarfBuzz shaping; CPython 3.12/3.14/3.15 status; Noto OFL; argon2/OWASP params | recorded inline in ADRs |
| Sandbox capability probe: `pip install` from PyPI works in build env (click wheel fetched) — foundation-phase pipelining viable | pass |

## Static checks

Docs-level review by re-read; markdown table/ID lint via scripts (in-tool). No code to lint (intentional).

## Perf & scale observations

N/A (design budgets set, not measured).

## Issues found & fixed

1. Referenced-but-undefined requirement IDs → added §7b/§14b blocks (traceability stays closed).
2. ADR file naming/index mismatch → renamed to ADR-019.
3. Database doc contained an unresolved deliberation artifact in `visit_treatments` row → replaced with the decided child-table design (no CSV columns).
4. Traceability self-check initially reported 247 rows vs 254 register entries: the §44 PERF table predated the final register column format (missing MoS column) so its 7 IDs escaped the generator. Register normalized to the common format; regenerated matrix verified 254 ⇔ 254. This is exactly the class of drift the mechanical generator + `--check` gate exists to catch.

## Known issues & risks (carry-forward, all pre-existing by nature of Phase 1)

- **R1 (high → mitigated by plan):** PySide6+PyInstaller frozen Qt is the biggest packaging risk (AV false positives, hook breakage). Mitigations: onedir, module pruning, PE-manifest audit, full-suite-against-artifact CI. Tracked: BUILD-RELEASE §3–5, ADR-015.
- **R2 (medium):** argon2 native binding in frozen build — CI import-smoke + fail-closed (no silent fallback, ADR-008).
- **R3 (medium):** physical printer/thermal fidelity can't be fully validated in CI — honest labeling protocol (PRINTING §10, TESTING §9).
- **R4 (low):** Inno 6.4.3 is an older pin; accepted for licensing reasons; owner may purchase current license later (ADR-016, BUILD-RELEASE §4).
- **R5 (medium, owner-dependent):** clean-machine/human DPI matrix needs the product owner's hardware at Phases 4/14/18 — scheduled, not skippable (CONFLICT-D1).
- **R6 (low):** 50k-patient scale is design-validated by SQLite indexing plan + budgets; if Phase 17 breaks a budget, plan allows keyset/materialized-CTE tuning without schema redesign.
- **R7 (documented residual, non-gating):** DB unencrypted at rest for 1.0 (SQLCipher seam for 1.0.1); activation is deterrence-grade, both disclosed in SECURITY §8/§2.

## Decisions made this phase

All 19 ADRs adopted; conflicts C1–C11 bound; defaults O1–O9 adopted pending owner veto; non-goals list adopted; verification-scope labeling vocabulary adopted; report/traceability tooling design frozen (executed by Phase 2 `scripts/`).

## Traceability delta

All 254 rows exist with frozen acceptance criteria; implementation rows are `Planned(Pn)`. Phase-1-owned governance rows (REQ-GOV-02/04/05, REQ-PROD-04/05 statement-level, REQ-ACT-03, REQ-GOV-07 policy) are `Verified(docs)` where the deliverable *is* documentation (Phase 2 adds tooling enforcement). No implementation requirement claims `Verified` — none can yet.

## Verification-scope labels

- sandbox-verified: doc cross-ref tooling runs, PyPI reachability probe.
- windows-CI-verified: (none yet — Phase 2+).
- hardware-required: printer/DPI/clean-VM rows — owner-side at scheduled phases.
- owner-run: PR merges (always), O1–O9 vetoes (available at any gate).

## Next phase

**Phase 2 — Engineering foundation** (ROADMAP §1/Phase 2). Deliverables: full repo skeleton, dependency management + lock, lint/type/test tooling, logging+config bootstrap, DB engine/pragma/lockfile foundation, Alembic baseline, CI `quality.yml`+`release.yml` running on the skeleton, docs updates. **Stop-gate: this phase is complete; do not start Phase 2 until the product owner replies `Continue`.**
