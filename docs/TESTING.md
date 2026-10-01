# Dentiva Pro — Test Strategy (v1.0, Phase 1)

Normative for REQ-QA-01..04, REQ-GOV-07 and every phase's acceptance criteria.
The project's honesty rule: **no test is reported as passed unless its run is
executed and its output archived**; hardware-dependent checks are labeled
`hardware-unavailable` explicitly, never "passed by proxy".

## 1. Test tiers & layout

```
tests/
├─ unit/           # pure logic: domain rules, money, dates, layout math (mm-space), validators, permission engine, state machines, backup manifest, activation derivation
├─ integration/    # real SQLite (temp dir), repositories/UoW, services end-to-end w/ DirectExecutor, migrations, FTS, audit chain, attachments store
├─ gui/            # pytest-qt, QT_QPA_PLATFORM=offscreen: shell, forms, tables, dialogs, lock screen, wizard, chart editor, preview widget; screenshot baselines
├─ security/       # negative authz matrix, bypass campaign scripts, log/secret scans, activation lockout loops, audit tamper tests, backup tamper matrix
├─ printing/       # DocumentModel goldens, op-stream JSON snapshots, PDF generation+parse assertions, raster perceptual diffs, signature-zone clearance property tests
├─ perf/           # budgets (REQ-PERF-*): reduced-scale in CI, full-scale at Phase 17; psutil memory guards
└─ fixtures/       # factories (factory-boy style local builders), golden corpora, stress generator (scripts/gen_stress_db.py)
```

Pytest + `pytest-qt` + `hypothesis` + `psutil` (+ `pypdf` test-only for PDF
assertions). Coverage: `pytest-cov`; gate = ≥85% lines on
`domain|services|security|backup|printing`, 100% branch on money and authz
modules (fail-closed numbers, CI-enforced from Phase 5 once services exist).

## 2. Determinism contract (every test obeys)

- **Clock:** all time via injected `Clock`; tests use `FakeClock` (no
  wall-clock reads in tests; sleep simulated).
- **Seeded RNG only** (fixtures set seeds); byte-for-byte repeatable datasets.
- **No sleeps for sync** — jobs driven to completion via `DirectExecutor` or
  explicit `job.wait()` with timeouts that *fail* loudly.
- **Temp dirs:** per-test data dir under `tmp_path`; no shared state; cleanup by
  teardown (leak detector asserts no stray locks).
- **Network:** `socket.socket` monkey-blocked in all test sessions (proves the
  offline rule while tests run — REQ-PLAT-03 corollary).
- **Fuzz boundaries:** any property test caps at < 2 s locally; CI parallel shards.

## 3. Fault injection & chaos (REQ-TXN-*, REQ-BKP-04, REQ-SETUP-04, REQ-ERR-*)

`tests/support/faults.py`: context managers that raise at chosen lifecycle
points (repository write #n, pre-commit hook, fsync, rename, zip member, hash
loop) + process-kill harness (`SIGKILL` on spawned child at randomized step,
100× loop in nightly job, 20× in PR job). Invariants asserted after each
injection: no partial rows / atomic file / journal state machine correctness.
The kill-harness doubles as the abnormal-shutdown startup test (REQ-TXN-03).

## 4. GUI testing method (headless)

`pytest-qt` offscreen on Linux (works identically on Windows CI); helpers:
`open_app(perm_role=…)` (composes a container with fakes + real DB),
`screenshot(widget)` baseline compare (perceptual hash vs committed goldens),
`assert_state_matrix(component)` (loading/empty/error/disabled/focus/selection
variants per REQ-UX-04), DPI sweeps via `QT_SCALE_FACTOR` 1.0/1.25/1.5/1.75/2.0
with invariant checks (bounding rects, min touch targets, no elided-must-not-be
labels), long-text torture fixtures (Bengali 200-char names etc. — REQ-UX-05).
Real-monitor DPI checks remain a Phase 4/14/18 human matrix item (recorded,
not simulated).

## 5. Security test program (Phases 5/12/15)

1. **Authz matrix generation:** AST-enumerate every public service method ×
   every seeded role × representative fixtures (patient with invoice w/ partial
   payment, inventory item at min stock, finalized rx…). Expected
   allow/deny table is a *committed CSV* (docs/tests/authz-matrix.csv); CI
   fails on drift in either direction (missing test OR behavior change).
2. **Bypass campaign (15):** drive denied paths via UI state edits
   (monkey-patched view flags), hotkey table, router deep links, direct
   service calls with hostile principals, DB tampering (audit UPDATE attempt),
   backup-package spoofing, attachment path traversal fixtures. Every attempt
   must fail with typed error + audit.
3. **Secret/PII scans (every release CI):** grep source + artifact tree +
   log fixtures for activation literals, `password`, `BEGIN RSA`, debug creds;
   log-corpus redaction tests.
4. **Password/activation soak:** hash param matrix (calibration), rehash on
   policy change, 30× restart activation loop, lockout pacing timing tests
   (fake clock).

## 6. Requirement-linked naming (REQ-GOV-04)

Each test module declares coverage in its docstring: `# covers: REQ-PAT-05,
REQ-PERF-02`. `scripts/check_traceability.py` (Phase 2+) parses the register +
matrix and fails CI if (a) any REQ lacks a matrix row, (b) any matrix row cites
a nonexistent test id, (c) a `Verified` row's evidence link is stale. Pending
AC tests referenced by REQUIREMENTS get stub rows in the matrix (`planned`) —
*reserved names, not executed* — until their phase ships them.

## 7. Stress datasets & budgets (REQ-QA-02, REQ-PERF-*)

`scripts/gen_stress_db.py` — seeded, flags:
`--patients 50000 --visits-per 4 --invoices 100000 --payments 150000
--rx 40000 --attachments 5000 --movements 300000 --audit 1000000`.
Perf suite asserts budgets at two scales (CI: 1/10 scale, ~8 s suite; Phase 17:
full) including: search p95 ≤ 300 ms, list page ≤ 150 ms, profile open ≤ 400 ms,
dashboard refresh ≤ 600 ms (all aggregates), invoice finalize ≤ 250 ms,
preview first page ≤ 500 ms, backup 500 MB ≤ 60 s, RSS guard (100 navigations
→ growth ≤ 20 MB), 8-hour soak loop (nav + save + lock cycles) with growth and
no error-log increase. `EXPLAIN QUERY PLAN` assertions for the 10 hottest
queries are committed artifacts (must use indexes; full scans on patients =
fail).

## 8. Print/PDF validation

Op-stream JSON goldens (layout math, signature clearance property-tested with
hypothesis: no DrawOp rect intersects reserved zone across fuzzed content
sizes), PDF structural asserts (embedded font names present, no /Type3,
page count, mediabox = profile), raster perceptual equivalence triad
(preview vs pdf-raster vs windows-print-pdf) per fixture × paper, Bengali
golden set (§PRINTING §7), thermal 1-bit logo variant golden. Windows-only
step (Print-to-PDF) gated in `release.yml`.

## 9. Clean-machine & release-suite protocol (Phase 18/20, REQ-QA-03)

Manual checklist (VM image: Windows 10 22H2 + Windows 11 latest, no VC
redist assumptions — the bundle carries what it needs, tested): install →
activate (code) → wizard → admin login → 30-op clinic day simulation (patient
→ visit → chart → rx → print PDF → invoice → partial payment → payment →
report) → lock/unlock cycle → backup → uninstall (keep data) → reinstall →
data intact → restore from backup on *fresh* second VM → day-2 flows →
negative checks (denied role, invalid attachment, corrupted .dvpkg). Each row:
`pass/fail/blocked(reason)` + evidence file (screenshot/log).
`release.yml` re-runs the *full test suite against the installed tree*
(pytest with `DENTIVA_ARTIFACT_ROOT`) — the artifact, not the dev tree, is the
tested object (REQ-QA/Phase 20 mandate).

## 10. Tooling & CI mapping

`quality.yml` runs tiers 1,2,4(partial),5(1..3 scans),7(CI scale),8(no PDF-raster on windows-only bits) —
all Linux/offscreen. `release.yml` re-runs everything on Windows +
windows-only suites (9,8-Windows). Phase gates additionally require the phase's
*manual* protocol rows recorded in the phase report (owner-run items clearly
separated, D1 honesty). Nightly schedule runs full-scale stress + kill soak
(so a Friday merge can't smuggle a 3 a.m. perf cliff).

## 11. What "passed" means (report wording, REQ-GOV-07)

Phase reports cite: runner URL + commit, test counts by tier, failures
(original + re-run status), skipped-with-reason list (every skip justified),
coverage numbers, perf table rows, and hardware/owner items with their labels.
The words "zero bugs" never appear; "no known unresolved release-blocking
issues" is the strongest claim allowed, and only at Phase 19/20 with evidence.
