# Dentiva Pro — System Architecture (v1.0, Phase 1)

Living document (REQ-GOV-05). Updated at each phase gate; this version fixes the
system shape that Phases 2–20 implement. Requirement IDs reference
`docs/REQUIREMENTS.md`; decisions reference `docs/adr/*`.

## 1. System in one paragraph

Dentiva Pro is a **single-process, offline, layered Python/Qt desktop
application**. One frozen executable per clinic PC; a SQLite database (WAL,
fully constrained) in the clinic data directory; content-addressed attachment
storage beside it; a deterministic print/PDF/preview layout engine; a
transaction-per-use-case service layer that is the sole enforcement point for
authorization and audit; and a `.dvpkg` backup container that is the product's
disaster-recovery and migration story. There is no network stack in the runtime.

## 2. Repository & module architecture (REQ-GOV-01, ADR-006)

```
officialdentivapro/
├─ src/dentiva/
│  ├─ __main__.py, app.py           # entry, CLI modes (--smoke, --offline-restore, --reset-diagnostic)
│  ├─ bootstrap/                     # composition root: container, config bootstrap file, paths, logging setup
│  ├─ core/                          # errors, result types, clock, money (Decimal/poisha), units, i18n catalog, events bus
│  ├─ domain/                        # entities, value objects, state machines, business rules (pure stdlib only)
│  ├─ data/                          # SQLAlchemy models, repositories, Unit-of-Work, migrations (alembic/), FTS sync, pragmas
│  ├─ services/                      # use-cases; @requires authz; transactions; audit emission; one sub-package per module:
│  │   ├─ patients/ visits/ chart/ clinical_library/ treatments/ prescriptions/
│  │   ├─ appointments/ queue/ billing/ payments/ inventory/ accounting/
│  │   ├─ staff_users/ settings/ notifications/ search/ reports/ audit/ backup/ activation/ setup/
│  ├─ security/                      # password hashers (argon2 policy+calibration), session manager, lock service, activation derivation, redaction filters, file-type sniffing
│  ├─ printing/                      # document model (blocks), snapshot builders, layout engine (mm-space), render sinks (pdf/printer/raster), profiles, print dialog flow
│  ├─ backup/                        # .dvpkg writer/validator/restorer, journal, scheduler
│  ├─ attachments/                   # content store, intake pipeline, thumbnails, open/materialize, verify
│  ├─ appstate/                      # shell state, router, route registry + permission map, notification store view-model, job coordinator
│  ├─ ui/                            # PySide6: theme (tokens), components (button, card, table, form, dialog, tabs…), screens (one package per module), lock screen, wizard, shell, chart widget, preview widget
│  └─ resources/                     # fonts/ (OFL), icons/ (SVG set + generated PNGs/ICO), seeds/ (clinical library, payment methods, roles), notices/
├─ tests/                            # see docs/TESTING.md §1 for tier map (unit, integration, gui, security, printing, perf, chaos)
├─ scripts/                          # build.py, audit_artifact.py, gen_license_inventory.py, gen_stress_db.py, activation_selftest.py, regen_print_goldens.py
├─ installer/                        # DentivaPro.iss, license.txt (EULA), assets (icon), version hook
├─ docs/                             # this spine
├─ .github/workflows/                # quality.yml, release.yml (ADR-017)
└─ dist/                             # fallback artifact staging (see dist/README.md)
```

**Dependency rule (enforced by conformance tests, ADR-006):**
`ui → appstate → services → (domain, data) → core`; `security`, `printing`,
`backup`, `attachments` are peer infrastructure services usable only through
`services`/`appstate` — never imported by `ui` beyond their UI-facing view
helpers. `domain` imports stdlib only. Alembic env lives under `data/migrations`.

## 3. Process, threads, and data flow (ADR-007)

- Single GUI thread; `JobRunner` with bounded pool (2 general workers + dedicated backup/restore worker). `DirectExecutor` in tests.
- Every user action: `UI signal → Command (appstate) → Service call (authz → validate → UoW commit → audit) → View-model update (Qt signals) → repaint`. No widget ever queries the DB.
- Reads for dense tables go through **paged query services** (keyset pagination, windowed aggregates) — REQ-PAT-05/REQ-REPORT-03. Cache: none beyond view-model snapshots; correctness beats memoization here.
- Writers serialize through `CommitGate` (single in-flight transaction). Readers use WAL snapshots. Lockfile in data dir rejects a second instance (REQ-TXN-04).

## 4. Startup sequence (state machine)

```
launch → paths/bootstrap → single-instance lock → logging → font registration+coverage gate
 → DB open (pragmas, user_version check) → integrity quick-check → abnormal-shutdown flag check
 → (if dirty) recovery flow (verify WAL replay → guided repair / restore entry)
 → migration check (head? older→migrate with preflight copy) → activation state
    ├─ NOT_ACTIVATED → Activation screen (one-time code) → write activation txn → continue
    └─ ACTIVATED → setup state
        ├─ SETUP_INCOMPLETE → first-run wizard (atomic txn, resumable) → login
        └─ SETUP_COMPLETE → Login → session start → shell (resume last route within permissions)
```
Every edge is testable by injecting container fakes; `--smoke` executes this
path headless in CI against a fixture data dir (ADR-017, REQ-QA-01).

## 5. Application state model (REQ-SHELL-04)

`AppState` (immutable snapshots, reducer-updated): `session {user, perms, ts}`,
`shell {route, navCollapsed, busyJobs}`, `context {focusPatientId?, filters…}`,
`clinicSnapshot {name, logo, dentistDirectory…}` (loaded once per session,
versioned), `notifications {unreadCount}`, `lockState`. Views subscribe; no
screen mutates state except via dispatched commands. Draft form state is
view-local by design (never global) — with lock-screen preservation (REQ-AUTH-03).

## 6. Navigation & routes (REQ-NAV-*, REQ-SHELL-*)

Route registry entries: `route_id`, view factory, required permission (read
gate), title, icon, section. Sections (REQ-SHELL-02): **Practice**
`dashboard, patients, patient_detail/:id, appointments, queue` · **Clinical**
`visits, visit_detail/:id, prescriptions, treatments_catalog, referrals, chart(:patient)` ·
**Billing** `invoices, invoice/:id, payments, inventory, accounting` ·
**Administration** `staff, users_roles, settings/*, clinical_library,
backup_restore, audit_log, reports, about`. Global: `search` (Ctrl+K overlay),
`lock` (modal). Deep navigation: any module can `open(entity,id)` through the
router; unauthorized targets → access-denied view + audit (REQ-NAV-02).

## 7. Core subsystem contracts

- **Transactions:** each service op = one UoW (`with uow(): …`); repositories flush; audit + timeline events registered on the session; commit fires `after_commit` UI invalidation (event bus). Nested calls share UoW (REQ-TXN-01/02).
- **Activation/Setup:** ADR-010 / REQ-SETUP-*; wizard steps map to one payload object; single transaction at finish.
- **Printing:** snapshot builder (DB → immutable document model incl. versioned `doc_json`) → layout → sinks; REQ-DATA-05 is *enforced by design*: printers never read live master rows (ADR-011, docs/PRINTING.md).
- **Backup/restore:** ADR-012 + docs/BACKUP.md; the backup worker quiesces CommitGate during snapshot/swap.
- **Notifications:** rule engine (§docs/DATABASE.md §10) generating deduped rows per rule key; navigation payloads.
- **Search:** FTS5 (patients, notes, complaint text) + indexed LIKE for codes/phones; union across modules gated per type (REQ-SEARCH-*); keyset results.
- **Audit:** ADR-009 hash chain; `audit_seq` monotonic (no gaps policy: gapless, since chain depends on order).

## 8. Error handling & logging (REQ-ERR-*, REQ-LOG-*)

`DentivaError` hierarchy with stable codes (`DVT-####` registry in
`core/errors.py`); services raise typed errors only; the dispatcher boundary
maps → toast/dialog (friendly text + error id) and logs full context under the
same id. Global `sys.excepthook` + Qt event filter for strays → crash bundle
(REQ-LOG-03). Structured logging: stdlib `logging` + `RotatingFileHandler`
(7×10 MB, `logs/app.log`, `logs/errors.log`), JSON-ish line format
`ts|level|component|error_id|msg` with **redaction filter** (passwords, hashes,
activation material, clinical payload in exception contexts) applied at the
handler (single choke point, REQ-LOG-02). Dev builds add console + higher level;
release default INFO, user-changeable to DEBUG *after* an explicit
"debug logs may contain clinical context near errors" notice (consent line) —
default OFF keeps the redaction promise.

## 9. Design system summary (REQ-UX-*; frozen visuals Phase 4)

Tokens-only styling (ADR-018): palette families (primary teal, ink navy,
neutral surfaces, semantic states incl. all interaction states), typography
scale on Inter/Noto Sans Bengali, 4-px spacing, radius tiers, 3-level
elevation, comfortable/compact densities, control metrics, dialog size classes
S/M/L/XL, motion tiers 80/120/180/240 ms with reduced-motion policy.
Components (Phase 4 gallery): Button (6 variants × states), Input stack
(text/date/time/money/combo/search/picker), Card, DataTable (keyset paged,
empty/loading/error states), Tabs, Segmented, Toast, Dialog, Stepper/Wizard,
Tree (nav), ChartDental, StatusChip, MoneyLabel, Avatar, FileTile,
EmptyState, ErrorBoundary panel, Progress (bar+spinner), Tooltip, Badge.
Screens conform by composition, not per-screen styling.

## 10. Data & file layout (REQ-DATA-03, REQ-PLAT-05, CONFLICT-O1)

```
%LOCALAPPDATA%/DentivaPro/
├─ data/
│  ├─ dentiva.sqlite3 (+-wal,-shm)     # the clinic database (WAL)
│  ├─ attachments/<xx>/<yy>/<sha256>   # content-addressed store (ADR-013)
│  ├─ logs/                            # rotated structured logs
│  ├─ temp/                            # open-materialization + print spool exports
│  ├─ quarantine/                      # restore swap safety area (ADR-012)
│  └─ .restore-journal / .shutdown-flag / instance.lock
└─ bootstrap.json                      # {data_dir, created, app_last_version} — the ONLY root file
```
Backups default destination `<data>/../backups` (relocatable). Data-dir
relocation is a Settings flow (copy + atomic bootstrap rewrite + verify).
`TEMP`/`TMP` is used only for Qt-internal rasters, never for authoritative data
(REQ-FILE-01).

## 11. Money & time conventions (REQ-DATA-09, REQ-MONEY-01, REQ-DATE-*)

- `Money = int poisha`; Decimal at boundaries; `ROUND_HALF_UP` on input; totals = Σ rounded lines + single rounding after discount basis points; South-Asian display grouping `1,00,00,000.00` default with plain `1,000,000.00` option (print setting); `৳/BDT` prefix setting.
- Time: **epoch-millisecond integers** for instants (sortable, index-friendly), ISO-8601 `Z` TEXT for human-readable timestamps in documents/audit; **Asia/Dhaka** is the display/filter timezone computed through the `Clock` service with pinned `tzdata`; day boundaries `[00:00, next 00:00)` Dhaka half-open (REQ-DATE-02). No naive datetimes (lint-enforced).

## 12. Performance budgets

Reproduced normatively in REQUIREMENTS §44 (REQ-PERF-01..07) — measured by
`tests/perf` in CI on reduced-scale datasets, full-scale at Phase 17; budgets
are release gates, not aspirations.

## 13. Security boundaries

Documented normatively in `docs/SECURITY.md`; architectural summary: UI is
untrusted input; the service layer is the sole trust boundary; the DB process
boundary is the data-at-rest boundary (documented residual risk); printing and
backup are capability-gated service clients; audit + activation are the
product's tamper-evidence layers.

## 14. Traceability & phase gates

`docs/TRACEABILITY.md` maps REQ→module→tests; every phase ends with
`docs/reports/phase-NN-*.md` per `docs/PHASE-REPORTS.md`; continuation on
explicit owner "Continue"; interruption protocol in ROADMAP §0.
