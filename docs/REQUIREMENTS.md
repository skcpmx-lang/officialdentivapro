# Dentiva Pro — Requirements Register (Phase 1)

Status: **v1.0 — normalized from the master product prompt (2026-10-01).**
This document is the single source of truth for *what* Dentiva Pro must do. Every
requirement has an ID (`REQ-<AREA>-<nn>`), acceptance criteria (AC), and
dependencies (DEP). `docs/TRACEABILITY.md` maps each ID to implementation
modules and tests; `docs/CONFLICTS-DECISIONS.md` records conflict resolutions
(referenced below as `CONFLICT-Cn`).

Coverage rule: **every requirement statement in the master prompt is mapped to
at least one REQ ID below** (coverage manifest at the end of this file). A
statement that is a *process* rule rather than a product feature is mapped to
`REQ-GOV-*`. Gaps identified during normalization are marked **[GAP→addition]**
and are mandatory additions, not optional polish.

Conventions used throughout:

- **MoSCoW**: M = must (release-blocking), S = should, C = could (only if free), A = won't (1.0).
- AC phrasing "test `XxxTest::name`" reserves test names that must exist and pass by the phase that implements the requirement (they may be pending until then — see `docs/TESTING.md` §6).
- Statuses used across this project (TRACEABILITY, phase reports): `Planned(Pn)` → `Building` → `Implemented-Unverified` → `Verified` → `Verified-Release-Ready`. A requirement may only show `Verified` with a named executed test run as evidence; `Verified-Release-Ready` additionally requires audit-phase confirmation (Phase 14–19).
- Money = integer *poisha* (1 BDT = 100 poisha) — see `REQ-DATA-09`.

---

## 1. Product identity & positioning

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-PROD-01 | M | Product identity is **Dentiva Pro**: a commercial, offline-first Windows dental clinic management product for real clinics in Bangladesh — not a demo, prototype, mockup, tutorial, or visual-only frontend. | Phase 20 gate: app installed from production artifact passes the clean-machine checklist (`docs/TESTING.md` §9). | — |
| REQ-PROD-02 | M | Primary interface language is professional English; user-entered content (patients, prescriptions, invoices, notes, addresses, names, instructions) must support Bengali Unicode throughout input, storage, display, and print. | All text columns store UTF-8; Bengali fixtures render in UI and PDF tests (`TestBengaliEndToEnd`). | REQ-LOC-01 |
| REQ-PROD-03 | M | Currency is Bangladesh Taka displayed as `BDT` and/or `৳`; no hard-coded `$` anywhere. | Currency formatter is the only money-to-text path; `TestMoneyFormat` covers both symbols and locale digits. | REQ-DATA-09 |
| REQ-PROD-04 | M | The product is a management and clinical-record workflow tool. It must not claim medical diagnosis, regulatory/clinical compliance, or statutory accounting compliance anywhere in UI, docs, or prints. | String audit in Phase 19 finds no compliance/diagnosis claims; disclaimer present in About. | — |
| REQ-PROD-05 | M | The application is architected as a coherent system: domain model, schema, business rules, permissions, navigation, state, printing, backup, settings, audit, and error-handling are defined **before** UI screens; every screen binds to real logic and persistent data. | Architecture doc precedes implementation (this phase); Phase 13 integration gate proves end-to-end chains. | REQ-GOV-02 |
| REQ-PROD-06 | M | **Zero simulated functionality**: no fake buttons, placeholder workflows, TODO functionality, dummy success messages, hard-coded fake records, dead navigation items, or decorative no-op controls in any shipped build. | Phase 16/19 automated sweep: every enabled control has a handler bound to a service call; repo-wide `TODO/FIXME/placeholder` scan over `src/` is clean; every nav route resolves. | REQ-NAV-01 |
| REQ-PROD-07 | M | **[GAP→addition]** Multi-entity by design: the model must never assume a single dentist, user, printer, visit, payment, medicine, treatment, monitor size, paper size, or clinic configuration. | Schema has no singleton tables; flows support N of each; negative test asserts two dentists can work concurrently in day view; print supports ≥2 profiles. | — |
| REQ-PROD-08 | M | **[GAP→addition]** Every module's data must persist across application restart at the exact moment the user receives success feedback (no in-memory-only state). | Restart-persistence tests per module (Phase 16 suite `TestRestartPersistence` covering all modules). | REQ-DATA-04 |
| REQ-PROD-09 | M | The product must feel coherent from first launch to uninstall (activation → setup → login → daily ops → lock → restart → backup → uninstall). | Phase 18 end-to-end checklist on production artifact. | REQ-INSTALL-* |

## 2. Platform, environment & distribution constraints

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-PLAT-01 | M | Target: Windows 10 and 11, 64-bit (x64). UI is DPI-aware and per-monitor scalable. Windows ARM64 is out of 1.0 scope (documented). | CI builds x64; DPI matrix run in Phase 4/14 (100/125/150/175/200%). | — |
| REQ-PLAT-02 | M | Installation must work on a clean machine with no Python, no IDE, no dev tools, no source repo; all runtime dependencies packaged. | Phase 18 clean-VM checklist + CI artifact smoke (`TestArtifactSelfContained`). | REQ-BUILD-01 |
| REQ-PLAT-03 | M | Fully offline during normal operation: no paid APIs, SaaS, cloud subscriptions, online AI, remote DBs, or mandatory internet for core functionality. Network code paths do not exist in the runtime except OS print spooler and local filesystem. | Static scan for network imports in `src/dentiva` (allowlist: none) in CI (`TestNoNetworkImports`). | — |
| REQ-PLAT-04 | M | Every third-party dependency must be legally compatible with closed-source commercial redistribution; licenses audited and shipped before release. | `THIRD-PARTY-NOTICES.json` generated + policy-checked in CI; license texts bundled in installer. | REQ-BUILD-04 |
| REQ-PLAT-05 | M | Long-term local data storage reliability: durability across power loss/crash; documented storage layout under the clinic data directory. | WAL+journal+backup tests (Phase 3/12/17), `docs/ARCHITECTURE.md` §10. | REQ-DB-01 |
| REQ-PLAT-06 | M | Support multiple printer types and paper sizes through Windows printer drivers (wired, wireless, Bluetooth, thermal). No proprietary printer SDK required. | Printer API abstraction + PDF equivalence tests; hardware validation logged as available/unavailable (Phase 11/18). | REQ-PRINT-* |
| REQ-PLAT-07 | S | **[GAP→addition]** Windows SmartScreen/AV behavior for unsigned builds is documented for clinics; code-signing is an optional owner decision (CONFLICT-O3). | `docs/BUILD-RELEASE.md` §5 includes guidance and owner decision status. | REQ-BUILD-03 |

## 3. Activation & licensing

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-ACT-01 | M | One-time activation at install/first activation with required code `1516591935015165`; activation is mandatory before first-run setup and cannot be deferred. | E2E: fresh install → activation screen blocks everything until correct code entered. | REQ-SETUP-04 |
| REQ-ACT-02 | M | The code must not be stored as obvious plaintext in source. The binary carries only a derived verification constant (salted SHA-256 digest); comparison is over digests, constant-time. | Source/binary scan in Phase 15: literal `1516591935015165` absent from `src/` and from built exe strings; unit vectors test derivation. | — |
| REQ-ACT-03 | M | The security limitation must be documented honestly: a fixed offline code cannot be made unrecoverable from a determined reverse engineer; the goal is to prevent casual exposure, not to claim cryptographic unbreakability. | `docs/SECURITY.md` §2 + About/help text contain the limitation statement; Phase 19 audit confirms wording matches reality. | — |
| REQ-ACT-04 | M | Activation must be deterministic, reliable, and fully testable (published test vectors), and must never lock out a legitimately activated installation after restart or ordinary use (activation state persists in DB + verified on startup; failures never re-lock activated installs). | `TestActivationLifecycle`: activate → restart ×30 loop → still unlocked; corrupt-marked tests; vectors pinned in docs. | REQ-DATA-03 |
| REQ-ACT-05 | M | Activation state is auditable (timestamp, install identifier) and survives restore/reinstall of app files while data dir intact; reinstall over preserved data does not silently require reactivation unless activation record missing. | Audit entries asserted; `TestActivationSurvivesReinstall`. | REQ-AUDIT-01 |

## 4. First-run setup (onboarding)

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-SETUP-01 | M | Secure first-run wizard after installation collecting: clinic/business name, clinic logo (image), address, phone, and one or more dentists. | Wizard walkthrough test; empty install → wizard shown; cannot be closed to main shell. | REQ-ACT-01 |
| REQ-SETUP-02 | M | Each dentist record: name, multiple designations, multiple certifications/qualifications; independent per dentist; dentists become the authoritative reference for clinical activity attribution. | Seed wizard supports ≥3 dentists; profile print uses only the responsible dentist's designations/certs. | REQ-SET-02 |
| REQ-SETUP-03 | M | Wizard establishes the initial administrator account (username + password) with validation, duplicate rejection, malformed-credential prevention, and strength feedback. | Negative tests: dup username, whitespace/case traps, short password policy (CONFLICT-C5). | REQ-AUTH-01 |
| REQ-SETUP-04 | M | Setup is atomic: all wizard data commits in one transaction; if interrupted (crash, kill, power loss) the app restarts into a clean "setup not completed" state with no partial records, and can be completed safely. | Fuzzed interruption test at each wizard step (`TestSetupAtomicity`); DB left at pre-setup state. | REQ-TXN-01 |
| REQ-SETUP-05 | M | Logo intake validates type (PNG/JPG), size limits, and stores the normalized copy in managed storage (not the user's original path). | Invalid file rejected with message; logo stored content-addressed; `TestSetupLogoIntake`. | REQ-ATT-01 |

## 5. Authentication & session security

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-AUTH-01 | M | Passwords are hashed with Argon2id (per-password random salt, OWASP-aligned work factor; tunable down for weak hardware), PHC encoded storage, constant-time verification. **Never** plaintext anywhere (DB, logs, crashes). | `TestPasswordHashing`: policy params, rehash-on-login when params change, no plaintext in DB dump/log scan. | REQ-LOG-02 |
| REQ-AUTH-02 | M | Login validates username+password with lockout pacing (progressive delay on failures), lockout events audited; no user enumeration differences. | Negative timing/message tests; audit entries. | REQ-AUDIT-01 |
| REQ-AUTH-03 | M | Auto-lock on inactivity with selectable durations **5, 10, 15, or 30 minutes** (plus "off" only for admin-owned installs if configured); lock preserves application state (current module, unsaved draft where safe) and requires re-authentication. | Idle-timer unit tests with fake clock; lock-screen E2E restores prior view. | REQ-SET-06 |
| REQ-AUTH-04 | M | Sensitive actions require re-authentication (step-up) or explicit elevated permission: restore, reset, permission changes, user deletion, unmasking restricted data en-masse. | `TestStepUpAuth` per sensitive operation. | REQ-RBAC-03 |
| REQ-AUTH-05 | M | Session has explicit lifecycle: login, active session in memory only, logout, lock/unlock, idle tracking from real input events (mouse/keyboard). | Session service unit tests; no tokens persisted to disk. | — |
| REQ-AUTH-06 | M | Multiple users can exist; each user is associated with a staff record where applicable; audit entries always attribute to a real user id (never a name string alone). | Schema FK integrity test; multi-user E2E. | REQ-STAFF-01 |

## 6. Authorization model (RBAC)

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-RBAC-01 | M | Granular permission catalog covering: patient management, clinical records, prescriptions, appointments, queue, treatments, invoices, payments, inventory, accounting, staff, users, backups, settings, reports, audit logs, destructive operations, and an **independent financial-visibility** permission. | Catalog table with stable string codes; every module declares required codes (startup assertion test). | REQ-DB-01 |
| REQ-RBAC-02 | M | Admin/owner can create users and assign roles with per-permission grants/revocations (role templates + user-level overrides). | Role CRUD E2E; template seeding (Owner, Dentist, Front-desk, Billing, Inventory staff) documented. | REQ-STAFF-02 |
| REQ-RBAC-03 | M | Authorization is enforced **in the business-logic (service) layer**, not merely UI: every service operation checks permission before touching data; UI hiding/disabling is cosmetic only. | Negative authz suite (Phase 5+, extended in 15) calls services directly with under-privileged principals; all denied (`TestServiceLayerAuthz`). | REQ-ARCH-01 |
| REQ-RBAC-04 | M | A staff member may be allowed to create invoices and enter payment information while being denied complete financial reports and aggregate financial views. | Fixture role "billing-clerk": invoice create ✔, payment record ✔, reports ✖, receivables ✖ — asserted. | REQ-RBAC-01 |
| REQ-RBAC-05 | M | Permission checks cannot be bypassed through alternate paths: routes, keyboard shortcuts, dialogs opened directly, local "API" calls, or query tools. Startup self-check asserts every UI command maps to a permission-decorated service call. | Phase 15 bypass attempts matrix (UI state manipulation, hotkeys, direct service invocation) → all blocked + audited. | REQ-NAV-02 |
| REQ-RBAC-06 | M | Permission changes are audited (who, to whom, before/after) and take effect for affected sessions immediately or on next action (documented choice: next operation). | Audit content test; live-effect test. | REQ-AUDIT-01 |
| REQ-RBAC-07 | S | Users may be deactivated (cannot log in) without deleting; audit history is retained. | Disable → login refused; history browsable. | REQ-DEL-01 |

## 7. Design system & visual language

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-UX-01 | M | A complete design-token system is defined **before** implementation: semantic colors (primary, secondary, accent, background, surface, border, text, muted text, success, warning, danger, info, disabled, hover, pressed, focused, selected, active, validation error/ok), typography scale, spacing scale, radius scale, elevation, density metrics, component dimensions, dialog size classes, icon grid, motion curves/durations. | `docs/DESIGN-SYSTEM` section in ARCHITECTURE §9 + token JSON shipped; no raw hex/px literals in UI code (lint rule `no-direct-colors`, Phase 2+). | — |
| REQ-UX-02 | M | Premium clinical visual identity: precision, trust, cleanliness, modern technology; must not resemble a generic CRUD app, school project, or admin template. | Phase 14 visual audit checklist pass; design review sign-off recorded in phase report. | REQ-UX-01 |
| REQ-UX-03 | M | Consistency across the whole product: typography hierarchy, cards, forms, tables, dialogs, buttons, tabs, icons, dropdowns, notifications, charts, tooltips, nav, spinners, empty/error states, confirmations, print previews, settings. | Component gallery app in Phase 4; Phase 14 audit compares every screen to tokens; drift findings fixed. | REQ-UX-01 |
| REQ-UX-04 | M | Complete interactive states for every component: loading, empty, error, disabled, hover, focused, selected, validation, success, warning, destructive. Tables with zero records use a designed empty state, not a broken frame. | State matrix tests per component (Phase 4 suite `TestComponentStates`); screenshot baselines. | REQ-UX-01 |
| REQ-UX-05 | M | Scrolling/layout integrity: no content outside viewport, no dialog beyond usable screen without interaction path, forms usable at min window size and all DPI levels, long strings (names, addresses, medicine names, notes, Bengali) never overlap icons or leave containers. | Resize/DPI torture tests + long-text fixtures in Phase 14; layout unit tests with `QT_QPA_PLATFORM=offscreen`. | REQ-DPI-01 |
| REQ-UX-06 | M | Deliberate alignment: grid card counts balance (e.g. 6 cards → 3×2, never 3-over-2 orphan rows); icon/text baselines aligned; tabular numerals in money columns; consistent hit areas (min 40×40 px logical for primary controls). | Layout unit tests assert grid math; Phase 14 pixel audit. | REQ-UX-01 |
| REQ-UX-07 | M | Animations are smooth, restrained, purposeful (≤200 ms micro, ≤300 ms panel), opacity/transform only where feasible, never block input, and degrade gracefully (reduced-motion preference honored; no animation on low-power flag). | Motion spec in tokens; `TestNoBlockingAnimations` (input latency during transitions); reduced-motion toggle E2E. | REQ-UX-01 |
| REQ-UX-08 | M | Custom Dentiva Pro application icon: refined dental symbol + clinical geometry + premium software identity; not a tooth emoji; clean geometry, optical centering, precise margins, transparent corners; validated at all Windows sizes (16/20/24/32/40/48/64/96/128/256) and contexts (exe, shortcuts, taskbar, installer, dialogs). | Icon QA checklist (crop/alignment/transparency/scale at each size) in Phase 4 report; `.ico` embedding verified in built exe (Phase 18 resource inspection). | REQ-BUILD-01 |
| REQ-UX-09 | S | Charts/sparklines on dashboard and reports share the token palette, are readable at 100% and 200% scaling, and include empty/error states. | Phase 14 audit. | REQ-DASH-01 |

## 7b. Architecture-level requirements (defined here; realized in ARCHITECTURE.md)

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-ARCH-01 | M | Layered architecture with strict one-way dependencies (ADR-006); business rules, persistence, and authorization live below the UI; UI binds view-models only. | Import-graph + pattern conformance tests pass in every CI run from Phase 3 onward. | REQ-GOV-02 |
| REQ-ARCH-02 | M | Versioned composition: schema revision, settings schema versions, and document-snapshot schema tags all stamped and validated at startup; migrations forward-only and deterministic. | Migration matrix CI job (ADR-004); startup version checks test. | REQ-DB-03 |
| REQ-ARCH-03 | M | Blocking work never runs on the UI thread; long operations run on the controlled worker pool with progress/cancellation (ADR-007). | `TestDirectExecutorContract` + UI-latency asserts during long queries. | REQ-PERF-04 |
| REQ-ARCH-04 | M | Cross-cutting services (audit, settings, clock, notifications, backup hooks) are container-managed singletons with fake-able interfaces used pervasively by tests. | Container tests; no module-level singletons outside bootstrap (lint). | REQ-ARCH-01 |
| REQ-NAV-01 | M | Navigation is a first-class module: named routes, route params (record ids), deep-link entry (`open patient #id`), history back/forward, and a startup-time route↔permission registration audit. | Router test suite; route inventory == nav map test (no orphan routes, no orphan nav items). | REQ-SHELL-03 |
| REQ-NAV-02 | M | Route access control: navigating to a route the user cannot read returns an access-denied view (and the *data fetch* was never attempted); nav items hidden are derived from the same permission service. | Negative route tests per group; fetch-not-attempted spy assertion. | REQ-RBAC-03 |

## 8. Application shell, navigation & global state

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-SHELL-01 | M | Header contains: Dentiva Pro identity, clinic business name, current date, notification center, user/session info, and contextual controls (global search, lock). | Shell E2E; values read from live clinic/session state. | REQ-SET-01 |
| REQ-SHELL-02 | M | Collapsible left navigation grouped: **Practice** (Dashboard, Patients, Appointments, Queue), **Clinical** (Treatments, Prescriptions), **Billing** (Invoice, Payments, Inventory, Accounting), **Administration** (Staff & Users, Backup & Restore, Settings, About) — plus necessary additions: Reports, Referrals (under Clinical), Audit Log, Clinical Library (under Admin). Collapsed state persists. | Nav map test asserts section→route wiring; collapsed state survives restart. | REQ-NAV-01 |
| REQ-SHELL-03 | M | Navigation model: single router with named routes, deep-link context (module+record id), back/forward, permission-filtered visibility computed from the service-layer authz result (not hardcoded lists). | Router unit tests; unauthorized route renders access-denied with audit trail. | REQ-RBAC-03 |
| REQ-SHELL-04 | M | Application state model: active session, clinic profile snapshot, pending background jobs, per-record edit locks; state transitions are explicit and testable (no global mutable singletons outside the container). | `AppState` reducer unit tests; container enforces dependency injection (architecture test, Phase 3). | REQ-ARCH-01 |
| REQ-SHELL-05 | M | Global error boundary: unexpected exceptions caught at every dispatch point, shown as friendly dialogs with error id, logged with full diagnostics; one failure never terminates the app abnormally. | Injected-fault tests per module; crash-report files written; process stays alive. | REQ-ERR-01 |
| REQ-SHELL-06 | S | Status bar / busy indicator: long operations show determinate or indeterminate progress; never a frozen window. | Worker-pool contract test (Phase 4/13). | REQ-ARCH-03 |

## 9. Dashboard

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-DASH-01 | M | Operational command center with widgets: today's patients, today's appointments, completed visits today, waiting queue summary, unpaid invoices count, outstanding receivables, today's payments collected, treatment activity, low-stock alerts, upcoming appointments, missed appointments, recent patient activity. | Each widget backed by a single SQL aggregate (EXPLAIN-checked); widget fixture tests compare DB-truth vs displayed numbers. | REQ-APPT-*, REQ-BILL-*, REQ-INV-04 |
| REQ-DASH-02 | M | Widgets respect permissions: financial widgets (receivables, payments, unpaid invoices) are entirely absent for users without `finance.view`; enforced by the query/service path, not by hiding. | Fixture user without finance perms: service raises `PermissionDenied`; dashboard renders no financial widgets. | REQ-RBAC-03 |
| REQ-DASH-03 | M | Every widget has loading, empty, error, and no-data states; refresh is live (on events) and on-demand without blocking UI. | State matrix test per widget class. | REQ-UX-04 |
| REQ-DASH-04 | S | **[GAP→addition]** Dashboard actions: key widgets are clickable and navigate to the underlying filtered lists (e.g. "missed today" → appointments filtered to no-show). | Navigation E2E for each clickable widget. | REQ-SHELL-03 |

## 10. Patients

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-PAT-01 | M | Effectively unlimited patient records (bounded only by storage/DB practicality); no arbitrary count caps in UI or logic. | 50,000-patient stress dataset passes list/search/profile benchmarks in budget (`docs/TESTING.md` §7). | REQ-DB-02 |
| REQ-PAT-02 | M | Every patient has a unique, permanent patient code (format configurable, e.g. `DVP-000001`, never reused, shown everywhere) and a persistent profile. | Sequence generator test (no gaps reused after delete); code uniqueness constraint at DB level. | REQ-DB-01 |
| REQ-PAT-03 | M | Registration supports: name, DOB **or** age (kept consistent, auto-derive), gender, blood group, address, phone, emergency phone, current complaint, past history, notes, referral source, plus photo; validation is helpful, not restrictive of legitimate real-world data. | Field-level validation tests incl. Bangladeshi phone formats (01…, +8801…, 09606…, with/without dashes — CONFLICT-C6), blank optional fields. | REQ-VAL-01 |
| REQ-PAT-04 | M | Patient list with date filters: today, 7 days, 30 days, 90 days, 1 year, custom range; default view prioritizes recent/new patients. | Filter SQL parity tests vs fixtures; default sort = created desc. | REQ-DATE-01 |
| REQ-PAT-05 | M | Advanced multi-attribute search (name, code, phone, notes, complaint…) with combinable filters; indexed query path; server-side pagination — never loads the whole table into memory. | `EXPLAIN QUERY PLAN` asserts index usage at 50k rows; p95 ≤ 300 ms (budget). | REQ-DB-02 |
| REQ-PAT-06 | M | Selecting a patient opens the comprehensive profile page (REQ-PAT-07…10). | E2E navigation test from list, search, and global search. | REQ-SHELL-03 |
| REQ-PAT-07 | M | Profile shows demographics + clinical info, visit history, treatment history, prescription history, appointment history, billing history, payment history, outstanding balance, balance settlement history, referrals/transfers, attachments, dental chart, notes, and timeline. | Profile tab inventory test (all sections present and populated from live data). | REQ-VISIT-*, REQ-CHART-01 |
| REQ-PAT-08 | M | Profile quick actions create real records for this patient: new visit, new appointment, new invoice, new prescription, record payment, add attachment, refer, add note. | Each action → record exists in DB with patient FK + audit; cancel creates nothing. | REQ-TXN-01 |
| REQ-PAT-09 | M | Repeat visits are separate historical events linked to the patient; nothing about prior visits is overwritten; "what happened recently" is visible at a glance. | Multi-visit fixture asserts chronological integrity after edits to latest visit only. | REQ-TIMELINE-01 |
| REQ-PAT-10 | M | Profile outstanding balance and settlement history are computed from invoice/payment ledger (no stored-cached drift); historical invoices display their snapshot values. | Balance parity test after partial payments; invoice snapshot immutability test. | REQ-BILL-05, REQ-DATA-05 |
| REQ-PAT-11 | M | Editing patient demographics updates the **current** record and does not rewrite printed historical documents (invoice/visit/prescription snapshots stay). | Snapshot immutability test (change phone → old invoice PDF data unchanged). | REQ-DATA-05 |
| REQ-PAT-12 | M | Archive/restore for patients: archived patients excluded from default lists/search but retained for history; deleting a patient record is only available via the destructive safeguard flow (REQ-DEL-01). | Archive E2E; hard-delete path requires backup+re-auth+typed confirm. | REQ-DEL-01 |

## 11. Appointments

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-APPT-01 | M | Calendar + list workflows to create/edit appointments: patient, dentist, date/time, duration, purpose, status, notes. | CRUD E2E from both calendar and list views; double-book warning policy test. | REQ-PAT-02 |
| REQ-APPT-02 | M | Statuses: scheduled, confirmed, arrived, in-progress, completed, cancelled, rescheduled, no-show — with legal transition rules enforced in services (no silent jumps like completed→scheduled). | Transition matrix unit test matches implementation; invalid transition rejected + auditable. | REQ-RBAC-01 |
| REQ-APPT-03 | M | Reschedule creates an audit-traceable change with old→new time kept (history preserved via events, not overwrite). | History table rows asserted after reschedule. | REQ-AUDIT-01 |
| REQ-APPT-04 | M | Attended vs missed visibility: users can see scheduled-and-attended and missed (no-show) appointments; day/period filters. | Filter parity tests on fixtures incl. boundary times. | REQ-DATE-02 |
| REQ-APPT-05 | M | Appointment history remains linked to the patient profile/timeline; creating a visit can link back to an appointment. | Linkage E2E: appointment → visit shows on both sides. | REQ-PAT-09 |
| REQ-APPT-06 | S | **[GAP→addition]** Appointment reminders feed the notification center (upcoming within configurable horizon) and dashboard "upcoming" widget. | Notification rules test. | REQ-NOTIF-01 |

## 12. Queue management

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-QUEUE-01 | M | Real-time waiting list: queue order, dentist assignment, per-entry status (waiting, in-room, called, seen, left), computed waiting time. | Queue service unit tests incl. reordering; waiting time computed from timestamps not display math. | REQ-APPT-02 |
| REQ-QUEUE-02 | M | Current/next patient controls (recall, next, mark left, move up/down, clear) with immediate persistence. | Action E2E each; DB state after each action asserted. | REQ-TXN-01 |
| REQ-QUEUE-03 | M | Queue state must not be lost on screen refresh, navigation, or restart — it is DB-backed, not view-model-backed. | Navigate away/back + app restart mid-day → queue identical. | REQ-PROD-08 |
| REQ-QUEUE-04 | S | Arrival from appointment ("check in") pushes to queue atomically with status transitions. | Atomicity test: both appointment=arrived and queue entry exist or neither. | REQ-TXN-01 |

## 13. Visits & clinical documentation

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-VISIT-01 | M | New-visit workflow records: reason for today's visit, clinical findings, treatments performed, prescriptions issued, notes, attending dentist, selected teeth, and charges; created directly from patient profile or module. | Visit creation E2E writes visit + chart findings + tx lines + prescription link in one transaction; charge lines proposed from catalog with editable amounts. | REQ-CHART-01, REQ-TREAT-01, REQ-RX-01 |
| REQ-VISIT-02 | M | C/C (clinical complaints) and O/E (examination findings) are selectable from the clinical library (with free text allowed alongside); R/E (recommended treatment) and advice support structured selection and free text. | Picker tests: multi-select library entries round-trip; free text preserved verbatim; history of a patient's complaints visible. | REQ-CLINLIB-01 |
| REQ-VISIT-03 | M | Visits are historical documents: once finalized, edits require an authorized amendment flow that records before/after (audit), never silent rewrite. | Amendment E2E: old values queryable in audit; finalized state enforced. | REQ-FINALIZE-01 |
| REQ-VISIT-04 | M | Visits link to: patient, dentist (responsible), appointment (optional), invoice (optional), prescription(s) (optional), chart findings, attachments; deleting a draft visit is allowed, finalized visit deletion is only via destructive safeguard. | Linkage integrity tests; FK cascade policies match `docs/DATABASE.md`. | REQ-DEL-01 |

## 14. Dental chart

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-CHART-01 | M | Professional numbering: **FDI two-digit** for adult (11–18, 21–28, 31–38, 41–48) and **primary teeth** (51–55, 61–65, 71–75, 81–85); a visit selects the dentition set (adult/pediatric) per patient age context, defaulting intelligently but overridable. | Chart data model + rendering tests for both sets; default selection by DOB (≥6 threshold documented) with manual override. | REQ-PAT-03 |
| REQ-CHART-02 | M | Tooth-level and surface-level condition marking (surfaces: occlusal, mesial, distal, buccal, lingual/palatal; tooth-level codes), multiple conditions per tooth, multiple teeth per encounter. | Editor E2E: mark 3 teeth × 2 surfaces across quadrants; persistence exact. | REQ-CHART-01 |
| REQ-CHART-03 | M | Findings are **episodic history**: each mark is tied to a visit and preserved forever; "current status" is derived (latest visit per tooth/surface), never overwrites earlier findings. | Derivation query test on multi-visit fixtures; deleting a draft removes only its findings. | REQ-TIMELINE-01 |
| REQ-CHART-04 | M | Chart is functional storage first, visual second: colors/icons are legend-configurable and readable in print; the same finding codes are usable in the treatment plan and invoice flow. | Data-first API: chart usable headless without rendering; legend tokens in design system; chart print snapshot (Phase 11) optional but no decorative-only state. | REQ-UX-01 |
| REQ-CHART-05 | S | **[GAP→addition]** Missing/extracted tooth state and simple treatment status per tooth (planned/in-progress/completed) to support real workflows. | States in enum catalog; timeline rendering asserts. | REQ-CLINLIB-02 |

## 14b. Timeline & finalization policies (referenced by clinical/billing areas)

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-TIMELINE-01 | M | Clinical Timeline is a chronological, understandable history of patient activity: visits, treatments, prescriptions, appointments, invoices, payments, referrals, attachments, notes, chart findings — each with date, responsible user/dentist, and detail; events are generated transactionally with their source records (a projection, never a manually-edited list). | Timeline parity test: for each event type, creating the source record appends the event in one transaction; ordering stable (timestamp + seq tiebreak); navigation from event opens source. | REQ-VISIT-*, REQ-BILL-05 |
| REQ-FINALIZE-01 | M | Finalization semantics for prescriptions, invoices, visits, and accounting entries: draft → finalized is explicit and irreversible except through authorized correction flows (amendment with before/after audit, or void+replace). Bulk print/lock guards: finalized docs can be reprinted with "REPRINT" marker; silent overwrite is impossible at the service layer. | State machine unit tests per document type; reprint marker test; amendment trail query returns prior content. | REQ-DATA-06 |

## 15. Clinical option library (C/C, O/E, findings, advice, statuses)

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-CLINLIB-01 | M | Configurable library with categories: complaints (e.g. pain, swelling, gum bleeding, bad breath, sensitivity), examination findings (G. caries, caries, BDR/BDC, gingivitis, periodontal pocket, periodontitis, pulpitis, impacted teeth, dry socket, attrition, erosion, + others), advice/recommendation entries. The requested terminology above is **seeded by default**. | Seed data test asserts every listed term exists post-setup; category browse/search in pickers. | REQ-SET-03 |
| REQ-CLINLIB-02 | M | Library entries carry: label, optional description, category, active/inactive, sort order; used by pickers in visit, prescription, and chart contexts. | CRUD E2E by authorized user; inactive entries hidden from new selections but retained in history. | REQ-RBAC-01 |
| REQ-CLINLIB-03 | M | Authorized users manage the library; unauthorized users consume it read-only. | Negative service tests (create/update denied without `clinical.library.manage`). | REQ-RBAC-03 |
| REQ-CLINLIB-04 | M | Library deletion never breaks history: in-use entries are archive-protected (cannot hard-delete; soft inactivate instead). | Constraint test: delete of in-use entry refused with guidance; historical labels preserved. | REQ-DATA-06 |

## 16. Treatment catalog

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-TREAT-01 | M | Structured catalog: name, category, description, default price (Decimal BDT), active/inactive, configurable by authorized users. | Catalog CRUD E2E; price validation (≥0, 2dp). | REQ-VAL-02 |
| REQ-TREAT-02 | M | Treatment usage is recorded against visits (performed/planned) and invoices (charged) with quantity and tooth references where applicable. | Linkage tests: invoice line → treatment + teeth; visit treatment → chart finding cross-ref. | REQ-CHART-02 |
| REQ-TREAT-03 | M | Historical invoices keep the actually-charged amount frozen; later default-price changes must not alter them. | Change-price E2E → old invoice value unchanged (snapshot column asserted). | REQ-DATA-05 |
| REQ-TREAT-04 | M | Inactivate ≠ delete: retired treatments disappear from new selection but remain in history. | Same pattern as REQ-CLINLIB-04. | REQ-DATA-06 |

## 17. Prescriptions

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-RX-01 | M | Prescriptions can be created from the patient profile and from the Prescriptions module (patient selection there); each prescription records responsible dentist, date, items, and clinical context (C/C, O/E, R/E/advice carried from or linked to a visit). | Both entry points E2E produce identical DB records. | REQ-VISIT-02 |
| REQ-RX-02 | M | Multiple medicines per prescription; each item: medicine name, strength/dose ("power"/mg), form (tablet/capsule/syrup/cream/injection/drops/ointment/… configurable), frequency (morning/noon/night + doses-per-day representation), food relation (before/after), duration (days or course), additional instructions, conditional instructions (e.g. "if pain"). | Item field round-trip tests incl. Bengali instruction text; "as needed" conditional flag rendered correctly in print. | REQ-FORMOPT-01 |
| REQ-RX-03 | M | Efficient drafting: add/edit/reorder/remove items before finalization; keyboard-friendly entry; no DB row churn on drafts (draft is one transaction at save). | Draft editor UI test incl. reorder; cancel creates nothing. | REQ-TXN-01 |
| REQ-RX-04 | M | Finalization state machine: draft → finalized (signed) → amendment only via authorized flow; finalized prescriptions render/print only when finalized (or explicit "DRAFT" watermark if previewed). | State tests; print of draft shows watermark (policy documented). | REQ-FINALIZE-01 |
| REQ-RX-05 | M | Prescription print design: header with clinic name+logo, address, phone; responsible dentist with **all their** designations and certifications; patient name/gender/age/date; C/C, O/E, R/E+advice sections; medicines table (name, dose, form, freq, food, duration, instructions); footer clinic message + availability; lower-right signature area with guaranteed blank space and nothing printed inside it. | Golden-layout PDF tests per paper size (Phase 11) incl. signature-zone clearance assertion (rect intersection = ∅). | REQ-PRINT-* |
| REQ-RX-06 | M | Prescriptions are historical: later edits to dentist designations, clinic info, or medicine catalogs do not rewrite finalized prescription content (full print snapshot). | Snapshot immutability test as REQ-PAT-11 but for rx. | REQ-DATA-05 |
| REQ-FORMOPT-01 | S | **[GAP→addition]** Medicine form/frequency/food-relation option lists are themselves configurable in Settings (seeded with the terms above). | Admin edits option; new pickers show it; existing records unchanged. | REQ-SET-03 |

## 18. Invoices & payments (Billing)

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-BILL-01 | M | Invoice creation from visit or standalone; items from treatment catalog, quantities, unit prices; supports adding custom/one-off lines; discount/adjustment (amount or percent) where applicable. | Builder E2E incl. mixed lines; arithmetic parity checks on totals. | REQ-TREAT-01 |
| REQ-BILL-02 | M | Invoice header carries clinic identity (name, logo, address, phone) with a hierarchy distinct from prescriptions; **no** prescription-style signature/footer block. | Layout tests: invoice template asserts absence of signature zone; identity fields from snapshot. | REQ-DATA-05 |
| REQ-BILL-03 | M | Totals: subtotal, discount/adjustment, total, paid, balance due, payment status (unpaid/partial/paid) — computed in poisha; status derived from ledger, not user-set. | Property-based tests (hypothesis) for arithmetic; status derivation table test. | REQ-DATA-09 |
| REQ-BILL-04 | M | Invoices are finalized documents; later payments attach to them without rewriting the invoice row; amendment/void only via authorized correction flows with audit trail (void keeps financial effect visible). | Void E2E: original + void doc net to zero; ledger consistent. | REQ-FINALIZE-01 |
| REQ-BILL-05 | M | Payments are independently stored records: patient, invoice reference, date/time, amount, method, receiving user, notes; multiple payments per invoice; partial payments reduce balance correctly; settlement history shows when/how each payment settled what. | Multi-payment E2E sequence; balance math property tests; timeline shows each payment event. | REQ-TXN-01 |
| REQ-BILL-06 | M | Payment methods: cash, bank, card, mobile wallet with configurable wallet list including **bKash, Nagad, Rocket, Upay, Others** (seeded); new methods configurable by admin. | Method CRUD + record-payment E2E; seeded list assertion post-setup. | REQ-SET-03 |
| REQ-BILL-07 | M | Payments module: full transaction history with date filters (today default, 7d, 30d, 90d, 1y, custom), method/user breakdowns. | Filter parity tests; default view = today. | REQ-DATE-02 |
| REQ-BILL-08 | M | Outstanding balance calculation across partial payments and later settlement is exact (no float drift), and the patient profile presents a coherent financial history (charges, payments, adjustments chronologically). | 1,000 random transaction sequences: ledger balance == invoice-level sum; zero drift after restart. | REQ-DATA-09 |
| REQ-BILL-09 | M | Invoice print: professional layout for A4, A5, thermal/receipt (80/58 mm), invoice printers; adapts without clipping; large item counts paginate; long names/addresses wrap; totals in BDT with ৳/BDT setting. | Golden tests (Phase 11) for each paper profile incl. stress fixtures (100 items, 200-char Bengali names). | REQ-PRINT-* |
| REQ-BILL-10 | M | Financial data for users without `finance.view` is unavailable at the service layer (queries raise), including aggregates, reports, and dashboard; users with `billing.operate` but not `finance.view` may create/collect within record scope but cannot read clinic-wide financials. | Negative authz matrix per service method (Phase 15 suite); UI widgets absent, not blanked. | REQ-RBAC-03, REQ-RBAC-04 |

## 19. Inventory

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-INV-01 | M | Stock items: name, category, supplier/source, purchase date, unit purchase cost, quantity purchased, current stock, unit (pcs/box/ml/…), batch info, expiry date, minimum stock level; dental consumables/accessories/supplies. | Item CRUD E2E; validation tests; Bengali names supported. | REQ-VAL-02 |
| REQ-INV-02 | M | Every stock change is a traceable movement record: purchase-in, usage/consumption, adjustment (with reason), wastage, transfer/correction; current stock is a derived+cached aggregate validated against movements. | Ledger recompute parity test; adjustments never edit history (append new). | REQ-TXN-01 |
| REQ-INV-03 | M | Low-stock alerts (at/below minimum) and expiry/near-expiry visibility (configurable horizon, e.g. 30/60/90 days) surface in notifications and dashboard. | Rule tests with fixtures; navigation to item from notification. | REQ-NOTIF-01 |
| REQ-INV-04 | M | Non-destructive updates: deleting an item with history is blocked; archive available. Stock quantity is never set by overwriting a number alone (all changes via movements). | Constraint tests; audit trail of movement chain. | REQ-DATA-06 |
| REQ-INV-05 | S | **[GAP→addition]** Consumption can be recorded per-day/department; purchase entries optionally post to Accounting expense. | Integration E2E (Phase 13): purchase with "record expense" tick creates linked expense entry once, atomic. | REQ-ACC-01 |

## 20. Accounting

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-ACC-01 | M | Clinic income & expense ledger with configurable categories seeded for: rent, electricity, internet, equipment/accessory purchase, staff salary, maintenance, miscellaneous, other income (and clinic revenue can be reported alongside but **not** double-entered: patient receipts are reported from the payments ledger, never re-typed). | Category CRUD; income-vs-expense report reconciles with payments+expenses exactly (no duplicate revenue). | REQ-BILL-05 |
| REQ-ACC-02 | M | Expense entries: date, category, amount, description, payee/supplier, optional attachment (receipt scan), recorded-by user. | CRUD E2E + attachment integration. | REQ-ATT-01 |
| REQ-ACC-03 | M | Salary records per staff: amount, period, paid-on, method, note — visible only under financial permission; linked to staff, not to patient data. | Permission tests; staff payslip view. | REQ-STAFF-03 |
| REQ-ACC-04 | M | Reports: daily/monthly/annual, category-wise, payment-method-wise, income vs expense, receivables summary — with the standard date filters; all respect `finance.view`. | Report parity SQL tests; RBAC negative tests. | REQ-REPORT-01 |
| REQ-ACC-05 | M | Positioning: internal clinic accounting — no statutory/compliance claims (REQ-PROD-04); entries support void/correct via reversing entries rather than silent edits. | Reversal E2E; original stays intact. | REQ-FINALIZE-01 |

## 21. Staff & users

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-STAFF-01 | M | Staff records: name, role/department, DOB/age, address, blood group (optional), ID document number (validated loosely), photo, salary (access-controlled), contact, employment status (active/inactive/resigned), notes. | CRUD E2E; photo content-addressed; salary field gated by `finance.view`. | REQ-ATT-02 |
| REQ-STAFF-02 | M | Users are conceptually separate from staff but linkable (1:0..1); user = username, password hash, role, permissions, session/lock settings inherited or overridden, status. | Separate tables with FK; user without staff allowed; staff without user allowed. | REQ-AUTH-06 |
| REQ-STAFF-03 | M | Salary amounts are financial data: hidden without `finance.view` (list, profile, exports). | Field-level masking test at service layer (value not returned, not just not painted). | REQ-RBAC-03 |
| REQ-STAFF-04 | S | Staff resignation/termination archives rather than deletes; historical attribution (audits, visits) intact. | Archive E2E. | REQ-DEL-01 |

## 22. Settings (centralized configuration)

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-SET-01 | M | Settings hub organized into logical groups (not one overwhelming page): Clinic & Identity, Dentists, Preferences (clinic hours, appointment slot behavior), Clinical Library, Treatment Catalog, Billing & Invoice, Prescription, Printers & Paper Profiles, Backup, Notifications, Users & Security (auto-lock), Reports, Data (storage location), About access. | Settings inventory test: every group reachable; cross-references between docs. | REQ-SHELL-03 |
| REQ-SET-02 | M | Clinic identity (name, logo, address, phone) and dentist registry (per-dentist name, designations list, certifications list) editable here; edits apply to **new** documents; finalized documents keep snapshots. | Snapshot behavior test shared with REQ-PAT-11/REQ-RX-06. | REQ-DATA-05 |
| REQ-SET-03 | M | Option catalogs (clinical library, forms/frequencies/food relations, payment methods, invoice settings like prefix/numbering, clinic footer messages, currency presentation ৳ vs BDT, receipt/invoice prefixes) configurable by authorized users. | Config round-trip tests; numbering prefix change affects only future documents (sequence continuity asserted). | REQ-DB-01 |
| REQ-SET-04 | M | Printer profiles: per document type (prescription, invoice, reports) select default printer, paper size (incl. custom width for thermal), orientation, margins, scaling; profiles previewed. | Profile CRUD + default resolution tests; profile applies in print path (mock printer + PDF equivalence). | REQ-PRINT-01 |
| REQ-SET-05 | M | Backup settings: destination folder (validated), interval 7/15/30 days (+off), retention count; notification settings (which alerts on, horizons); language/input preference (UI stays English; data entry input hints), currency presentation, date format preference. | Settings apply immediately where documented; validation rejects missing/invalid paths. | REQ-BKP-01, REQ-NOTIF-01 |
| REQ-SET-06 | M | Security settings: auto-lock interval (5/10/15/30 min), step-up requirement toggles where allowed, password policy display; changes audited and step-up-protected (self-lockout guard: cannot remove own admin rights). | Guard tests; audit asserted; auto-lock effect E2E. | REQ-AUTH-03, REQ-AUTH-04 |
| REQ-SET-07 | M | All settings persist in DB with defaults + validation on write; no settings file duplication drift (single source: settings table; config dir only for bootstrap locations). | Settings service test; file scan asserts no parallel config store. | REQ-DATA-03 |

## 23. Destructive actions & data protection

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-DEL-01 | M | Destructive operations (delete patient/visit/user/record, "delete all data", reset application) require: `ops.destructive` permission (+ admin for global reset), re-authentication, typed confirmation for mass destruction, **mandatory immediate safety backup** before execution (for data-destroying ops), and results audited. | E2E flows for each destructive action assert all gates; skipping any gate aborts with zero DB change. | REQ-BKP-02, REQ-AUTH-04 |
| REQ-DEL-02 | M | Soft-delete/archive is the default wherever history matters (patients, staff, treatments, library entries, items); hard deletes only where history is not clinical (e.g. draft documents) and never one-click. | Inventory of delete-capable entities lists policy per entity (`docs/DATABASE.md` §8); test enforces policy map. | REQ-DATA-06 |
| REQ-DEL-03 | M | No dangerous one-click destructive operations anywhere; bulk selections show count and affected-record preview before confirmation. | UI audit test: no bulk action fires without confirm dialog with counts. | REQ-UX-04 |
| REQ-DEL-04 | M | "Reset application" is a full factory path: wipes data dir contents (after backup export prompt), requires owner re-auth + typed app name, returns app to activation state — implemented and guarded, not hidden. | Reset E2E on test install; guarded paths asserted. | REQ-ACT-04 |

## 24. About & product information

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-ABOUT-01 | M | About identifies Dentiva Pro and credits **Shohan Khan, helloiamshohan@gmail.com** professionally (not visually excessive); shows version/build metadata, activation state summary, data location, third-party licenses entry. | About content test incl. license bundle presence (from installed tree). | REQ-BUILD-04 |

## 25. Global search

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-SEARCH-01 | M | Advanced global search across patients, appointments, visits, prescriptions, invoices, payments, inventory, staff, referrals (and other configured record types), filtered by the searcher's permissions per record type. | Each area contributes results iff user has `.read`; negative authz test excludes financial tables for non-finance users (rows not even fetched). | REQ-RBAC-03 |
| REQ-SEARCH-02 | M | Results are grouped by record type with type labels, matched-field snippets, and direct navigation to the record (route + context). | Navigation E2E per type opens correct screen/record. | REQ-SHELL-03 |
| REQ-SEARCH-03 | M | Search is fast on large data (indexed, capped result windows, no full-table loads); Ctrl+K style shortcut opens it; Esc closes; typing debounced; empty and no-results states designed. | Perf budget: global search p95 ≤ 500 ms on 50k-patient dataset; UI test for shortcut/esc. | REQ-DB-02 |

## 26. Notifications

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-NOTIF-01 | M | Notification center with actionable, meaningful notifications: upcoming appointments, missed/no-show, low stock, expiring stock, outstanding balances (permission-gated), backup-due/backup-failed, restore warnings, system warnings. | Rule engine unit tests per type; no generic noise — every rule has trigger conditions and de-dup keys. | REQ-RULES-01 |
| REQ-NOTIF-02 | M | Read/unread state, severity levels (info/success/warning/danger), per-user, with navigation to the relevant record; "mark all read"; unread count badge in header. | E2E incl. multi-user isolation (user B does not see user A's read state). | REQ-DATA-03 |
| REQ-NOTIF-03 | M | Notifications never reveal restricted data to unauthorized users (generated with permission checks at generation and display; financial alerts simply do not exist for non-finance users). | Generation-context test as root user vs clerk user → different persisted rows. | REQ-RBAC-03 |
| REQ-NOTIF-04 | S | Onboarding/in-app help: guided tour for first run, contextual help icons, keyboard shortcut reference — content that aids operation; no marketing fluff. | Tour skip/complete states; shortcut sheet matches real bindings. | REQ-KBD-01 |

## 27. Audit log

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-AUDIT-01 | M | Audit records capture: timestamp, user, action, entity type/id, contextual detail (JSON snapshot of what changed, redacted of sensitive fields), and severity; covering authentication (login/logout/lock/failures), permission/user changes, destructive ops, backup/restore, sensitive financial actions, patient record changes, prescription finalization, invoice/payment operations. | Event catalog table in ARCHITECTURE §8; per-event tests assert emission and content. | REQ-ARCH-04 |
| REQ-AUDIT-02 | M | Audit log is append-only from the application's perspective: no update/delete API; tamper-evidence via hash-chained records (prev_hash → entry hash); chain verified on startup and on view. | Chain verification test incl. detection of a manually tampered row (dev-mode fault injection). | REQ-DB-01 |
| REQ-AUDIT-03 | M | Audit viewer: filters (user, action category, entity, date range), detail view, export (CSV/PDF) with permission `audit.read`; export audited. | Viewer E2E; export content assertions; negative test for viewers without perms. | REQ-REPORT-01 |
| REQ-AUDIT-04 | S | Audit retention policy configurable (default retain all; optional archive after N years writes signed file then prunes only with re-auth). | Policy unit test; pruned archive verifiable. | REQ-DEL-01 |

## 28. Attachments

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-ATT-01 | M | Authorized users attach files (previous prescriptions, reports, images, documents, scans) to a patient; store in managed data dir content-addressed by SHA-256 (never the user's original absolute path); safe internal names; metadata: original filename, MIME, size, hash, uploader, timestamp. | Files live under `<data>/attachments/aa/bb/<sha256>`; DB path relative; moving data dir keeps everything working (portability E2E). | REQ-BKP-05 |
| REQ-ATT-02 | M | Upload validation: extension whitelist ∩ sniffed magic bytes (PNG/JPEG/GIF/BMP/WebP/PDF/DOCX/XLSX/TXT), max size configurable (default 25 MB), zero-byte and corrupted-file rejection with clear messages, duplicate detection (same hash → instant dedupe reference). | Malformed fixtures (fake .pdf bytes, .exe renamed .jpg, truncated images) rejected; dedupe test; size boundary tests. | REQ-VAL-03 |
| REQ-ATT-03 | M | Direct open/view via Windows shell association (safe temp materialization with original extension), reveal-in-folder, in-app preview for images/PDF where practical; never executes content. | Open tests use sandboxed temp; execution impossible (no double-click handler beyond `os.startfile` on validated copy). | REQ-SEC-02 |
| REQ-ATT-04 | M | Attachment lists paginate and remain usable at hundreds of files; per-attachment audit (added/removed by whom); removal is soft (file retained until backup-verified prune utility — documented). | 300-file list stress; removal → DB row marked removed, file still present pre-prune. | REQ-BKP-04 |

## 29. Backup & restore

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-BKP-01 | M | Admin selects backup destination folder; deterministic naming `DentivaPro-Backup-YYYYMMDD-HHMMSS(Z)-<manual|auto|pre-restore>.dvpkg`; container = ZIP with manifest, DB snapshot, attachment index+files, configuration, version stamps — format documented in `docs/BACKUP.md`. | Naming format property test; container layout test; docs match implementation (automated conformance check). | REQ-DATA-03 |
| REQ-BKP-02 | M | Manual backup on demand with progress; automatic scheduled backups at configurable intervals (7/15/30 days) with missed-window catch-up on app start; retention policy. | Fake-clock scheduler tests incl. catch-up; real-time smoke in Phase 12. | REQ-DATE-02 |
| REQ-BKP-03 | M | Restore from one or multiple selected backup files (multiple = sequential policy, last-wins, explicit warning; documented); integrity validation **before** replacement; clear destructive warnings; re-auth required. | Restore flow tests incl. multi-select ordering policy; tampered package rejected pre-swap. | REQ-BKP-05 |
| REQ-BKP-04 | M | Pre-restore automatic safety backup of current state; restore verified (PRAGMA quick_check + counts + manifest hashes) after swap; on failure, automatic rollback to safety package. | Fault injection at each swap step → never a corrupt live DB; rollback asserted; audit trail complete. | REQ-TXN-03 |
| REQ-BKP-05 | M | Backup includes everything required to restore application state: database + managed attachments + configuration (per format doc); interrupted backup leaves no corrupt artifact (temp+rename, verified before renaming in). | Interrupted-write tests; output dir contains only valid packages; `TestBackupAtomicity`. | REQ-FILE-01 |
| REQ-BKP-06 | M | Tested scenarios: create, invalid backup detection (not a package), corrupted detection (hash mismatch), partial backup, restore into empty install, restore over existing data, duplicate restore attempt, interrupted restore, post-restore integrity verification. | Dedicated suite `tests/security/test_backup_matrix.py` (Phase 12) with all named cases green on CI. | REQ-BKP-01..05 |
| REQ-BKP-07 | S | Backup status surfaced: last success time in Settings/Backup page and notification center; failures notify with actionable message; optional volume-check at destination. | Notification rule test; destination-free-space pre-flight test. | REQ-NOTIF-01 |

## 30. Data, domain model & integrity

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-DB-01 | M | Normalized relational model (documented fully in `docs/DATABASE.md`) covering: patients, visits, dentists, designations/certs, appointments, treatments, chart findings, prescriptions(+items), invoices(+items), payments, referrals, attachments, inventory items/movements/suppliers, expenses/income, staff, users, roles, permissions, settings, backups, notifications, audit, sequences, documents snapshots — with explicit PKs, FKs, unique constraints, indexes, nullability, CHECK constraints, enum/status domains. | Schema conformance test compares live SQLite schema to documented spec (names, keys, indexes); every enum column has CHECK/domain table. | — |
| REQ-DB-02 | M | SQLite engine configured for durability and scale: WAL journal, foreign_keys ON, busy_timeout, synchronous=FULL for installs (documented trade-off), page cache tuning, integrity pragmas; search/list queries use indexes and LIMIT/OFFSET or keyset pagination. | `PRAGMA` assert test; pagination keyset behavior tests at 50k rows; `EXPLAIN` index assertions. | REQ-DB-01 |
| REQ-DB-03 | M | Versioned schema migrations (Alembic) with deterministic offline upgrade path, `user_version` stamping, forward-only policy for shipped versions, tested on every historical version chain. | Migration CI job: build at each tagged schema rev → upgrade to head → conformance. | REQ-ARCH-02 |
| REQ-DB-04 | M | No comma-separated multi-values where relations apply (e.g. designations, certifications, teeth, surfaces, permissions are rows); documented and enforced by schema review test. | Schema spec review test + grep rule for `_csv`/`_ids` anti-pattern columns. | REQ-DB-01 |
| REQ-DATA-03 | M | Settings/config persisted in DB (typed store with schema-checked values); single source of truth; bootstrap file only records data-directory location. | REQ-SET-07 tests; drift impossible by construction (no second store). | REQ-SET-01 |
| REQ-DATA-04 | M | All critical business operations are transactional with rollback: setup completion, visit finalization, prescription finalization, invoice creation+payment, inventory adjustment, restore, queue check-in — half-completed states are impossible on error injection. | Per-operation fault-injection transaction tests (Phase 3 seeds; extended per module). | REQ-TXN-01 |
| REQ-DATA-05 | M | Defined snapshotting rules for finalized/printed documents: invoices, prescriptions, visit summaries, receipts freeze the patient identity block, dentist block, clinic block, and charged amounts used at print time; later master-data edits never alter them; "legal/operational need to preserve original printed state" is an explicit design rule. | Snapshot table/JSON column tests: master data mutation leaves rendered-document source unchanged for all doc types. | REQ-DB-01 |
| REQ-DATA-06 | M | Explicit lifecycle semantics for every entity: draft → finalized → amended(voided) and active → archived; status domains enumerated in DB; illegal transitions rejected in service layer. | Transition policy matrix test mirrors docs. | REQ-FINALIZE-01 |
| REQ-DATA-07 | M | Referential integrity enforced by FKs with deliberate cascade/restrict policies (e.g. deleting a patient cascades only to non-financial drafts; financial and clinical history are RESTRICT → archive path). | FK behavior tests per relation as documented in DATABASE.md §7. | REQ-DB-01 |
| REQ-DATA-08 | M | **[GAP→addition]** Referrals/transfers: record to whom/where, reason, date, notes, follow-up date/status; visible in patient timeline and a Referrals module list. | CRUD E2E + timeline event; follow-up notification rule. | REQ-TIMELINE-01 |
| REQ-DATA-09 | M | Money: integer poisha in DB; `Decimal` in logic; explicit quantize+ROUND_HALF_UP at input boundaries; never binary float for money end-to-end; amounts ≥ 0 for bills, negatives only via typed adjustments/reversals. | Property tests (fuzzed line sets) for totals/balance identities; lint rule bans `float(` in money paths (custom check). | REQ-VAL-02 |
| REQ-DATA-10 | M | **[GAP→addition]** Clinical notes and free-text history (past problems) are versioned append-style where edited after finalization; current view + history both available. | Note revision chain test. | REQ-VISIT-03 |

## 31. Transactions, recovery & resilience

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-TXN-01 | M | A Unit-of-Work/repository layer wraps every write use-case in a transaction; nested operations share one UoW; commit only at use-case boundary. | Architecture test: services obtain UoW via container (no direct engine commits); concurrency demo test. | REQ-ARCH-01 |
| REQ-TXN-02 | M | Database writes roll back fully on any exception mid-operation; user sees the error; no partial rows. | Injected exceptions at each write stage per critical flow → DB byte-state unchanged (checksum compare). | REQ-TXN-01 |
| REQ-TXN-03 | M | Startup detects abnormal shutdown (unclean flag file + WAL replay check); runs integrity check; offers safe recovery path (auto-repair attempt via backup/verify → restore prompt) and informs the user honestly. | Kill-mid-session matrix: process killed at random ops ×50 → clean startup, integrity pass or guided recovery. | REQ-BKP-04 |
| REQ-TXN-04 | M | Unexpected termination must never corrupt the DB for normal transactions (SQLite WAL + synchronous FULL + single-writer discipline); multi-process access is refused via lock file with friendly message. | Lock-file contention test (second instance refuses with dialog, no DB damage). | REQ-DB-02 |
| REQ-FILE-01 | M | All file writes (attachments, backups, exports, config bootstrap) use temp-file + fsync + atomic rename pattern; interrupted file operations leave no half-written authoritative files. | Fault-injection file ops suite. | — |
| REQ-ERR-01 | M | Structured error model: typed exceptions (DomainError hierarchy: Validation, PermissionDenied, NotFound, Conflict, Integrity, BackupIntegrity…) mapped to user-facing messages + stable error codes; raw stack traces never shown to users; full trace in logs keyed by shown error id. | Error-code catalog test; UI never renders traceback text (fixture test with forced crash). | REQ-LOG-01 |

## 32. Logging & diagnostics

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-LOG-01 | M | Structured application logs (rotating file handler, size+age caps, bounded total retention; e.g. 7×10 MB), levels configurable in settings (default INFO), with error ids correlating UI dialogs to log entries. | Rotation unit test; correlation test dialog→grep log by error id. | REQ-ERR-01 |
| REQ-LOG-02 | M | No sensitive data in ordinary logs: never passwords, password hashes, activation codes/constants, full patient clinical text; redaction filters applied to exception context; logs stored inside data dir (not world-writable temp). | Redaction unit tests + scan of log fixtures for forbidden patterns; PII-boundary review documented in SECURITY.md. | REQ-SEC-02 |
| REQ-LOG-03 | S | **[GAP→addition]** Crash reporter: on unhandled exception, write a redacted diagnostic bundle (error id, version, stack, no clinical data) and offer "copy error id" to the user; no telemetry/network. | Bundle content test; zero network calls asserted. | REQ-PLAT-03 |

## 33. Input validation

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-VAL-01 | M | Validation covers: phone numbers accepting legitimate Bangladeshi formats (01X…, +8801X…, 096XX…, optional dashes/spaces; warn-not-block unusual), required fields, dates (no future DOB, sane ranges), money (2 dp, ≥0), quantities (>0), usernames (charset, length, case-insensitive uniqueness), passwords (policy per CONFLICT-C5), file names, appointment times (within working hours warning, not block), duplicate patient identifiers (same name+phone+dob → possible-duplicate warning with side-by-side review, never silent merge). | Rule-based unit tests per validator incl. the boundary/malicious cases; duplicate-review E2E. | — |
| REQ-VAL-02 | M | Monetary/quantity parsing is centralized (single money parser); user input like `1,500.75`, `৳500`, spacing variants handled; invalid rejects with helpful message. | Fuzz + table tests on parser. | REQ-DATA-09 |
| REQ-VAL-03 | M | Inline, non-blocking validation UX: errors on blur/submit, field-level messages, form-level summary scroll-to-error; save disabled while invalid. | Form interaction tests; accessibility check for error announcement (screen-reader labels at least via accessible name). | REQ-KBD-01 |
| REQ-VAL-04 | S | Validation never rejects legitimate clinical data on length: text fields capped generously (e.g. 4k chars notes) with clear counters, not hidden truncation. | Boundary length tests at max; DB TEXT used. | REQ-DB-01 |

## 34. Money & reporting precision

Covered by REQ-DATA-09, REQ-BILL-03, REQ-BILL-08. Additional:

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-MONEY-01 | M | Rounding rules are explicit and documented: line = qty×unit rounded to poisha HALF_UP at entry; totals = sum of rounded lines; discounts applied then rounded once; percents stored as integer basis points (1/10000). | Documented in ARCHITECTURE §11; property test of identity total == Σ lines + adjustment. | REQ-DATA-09 |
| REQ-MONEY-02 | M | Reports and UI format amounts with thousands separators and 2 decimals (en grouping with Bangla digits option for print only if configured — default Latin digits). | Formatter tests; print golden includes large totals (10,00,000.00-style grouping configurable — default 1,00,00,000.00 South-Asian grouping for BDT; documented decision). | REQ-LOC-02 |

## 35. Date, time & timezone

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-DATE-01 | M | One internal representation: all timestamps stored UTC (ISO-8601 TEXT with `Z`), all clinic-facing dates/times displayed/interpreted as Asia/Dhaka via `zoneinfo` + pinned `tzdata`; "today" boundaries computed in Dhaka time. | Boundary unit tests (midnight-crossing fixtures); no naive-datetime lint rule. | REQ-ARCH-02 |
| REQ-DATE-02 | M | Deterministic comparisons for appointments, payments, reports, audits, backups: range filters are [start, end) half-open on Dhaka day boundaries; day/week/month aggregations use Dhaka calendar. | Parity tests of Python vs SQL aggregation; DST-free assumption documented. | REQ-DATE-01 |
| REQ-DATE-03 | S | **[GAP→addition]** Clinic working hours/slots configuration drives appointment defaults and after-hours warnings. | Config test; picker limits. | REQ-SET-01 |

## 36. Unicode, Bengali & localization

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-LOC-01 | M | Bengali Unicode end-to-end: input (IME-friendly plain fields), storage (UTF-8), display (Qt + bundled Noto Sans Bengali fallback), printing/PDF (font embedding verified), and reports. Mixed BN/EN runs, Bengali numerals ০-৯, punctuation, ZWJ/NFC-vs-NFD edge cases must not produce tofu, boxes, or misalignment. | `TestBengaliEndToEnd`: same string round-trips UI→DB→PDF; PDF glyph-run assertions (no `.notdef`); shaping verification harness (docs/PRINTING §7). | REQ-FONT-01 |
| REQ-LOC-02 | M | Presentation configs: currency symbol (৳/BDT), digit style (Latin default; Bengali digits optional for printed docs), date format (dd-MMM-yyyy default, configurable), name order; stored per clinic. | Each toggle drives a golden fixture (UI + PDF). | REQ-SET-03 |
| REQ-LOC-03 | M | Text normalization: all user text NFC-normalized at intake (documented), stored verbatim; no case-mapping of Bengali; Latin searches case/accent-insensitive where sensible (name search). | Normalization unit tests; search fold test. | REQ-DB-01 |
| REQ-LOC-04 | S | UI strings externalized (single `i18n` catalog) even though 1.0 ships English only — prevents hardcoded-string drift and enables future Bengali UI without rework. | Catalog extraction check in CI (no literal UI strings outside catalog) — enforced from Phase 4. | REQ-ARCH-01 |

## 37. Fonts & text rendering

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-FONT-01 | M | Ship OFL-licensed fonts embedded in the app: UI Latin font (Inter or equivalent OFL — final pick in Phase 4 audit), Noto Sans Bengali (+ Bold/BoldItalic variants for print), bundled at fixed versions with license texts; never depend on user-installed fonts for correctness (system fonts may be offered as an option). | Font manifest (name, version, sha256, license) asserted at startup; PDF embed test: font present in PDF resources for Bengali output. | REQ-PLAT-04 |
| REQ-FONT-02 | M | Glyph coverage verified programmatically (QRawFont coverage checks) rather than assumed; missing-glyph fallback chain: bundled Bengali → Noto → system; tofu detection in print tests. | Coverage test enumerates required codepoints (Bengali block, latin, ৳, digits, punctuation) per bundled face; print harness flags `.notdef`. | REQ-LOC-01 |
| REQ-FONT-03 | S | Text shaping relies on Qt's HarfBuzz engine (complex-script correctness); Bengali conjuncts rendered correctly in UI and print — validated against reference golden images. | Golden-image comparison (perceptual threshold) for sample conjunct strings in offscreen render. | REQ-FONT-01 |

## 38. High-DPI, responsiveness & layout

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-DPI-01 | M | High-DPI correctness: Qt6 per-monitor DPI aware v2; logical-pixel design tokens; icons supplied/derived at all needed sizes; no blurry or clipped UI at 100/125/150/175/200%; print preview scales correctly. | DPI matrix automated where possible (QT_SCALE_FACTOR sweeps in CI + Windows-run visual check in Phase 4/14); manual matrix on real displays logged in report. | REQ-BUILD-01 |
| REQ-DPI-02 | M | Minimum window size defined (1024×680 logical) and enforced; layouts degrade in documented priority order (sidebars collapse, tables drop columns into expandable rows, dialogs scroll) — no control ever inaccessible. | Min-size test; collapse policy tests at 1024×680. | REQ-SHELL-01 |
| REQ-DPI-03 | M | Practical window resizing on different monitors: fluid resize, no reflow thrash, scroll areas sized to viewport; print preview fits window with zoom controls. | Resize torture test (fuzzed sizes) with invariant checks (all visible widgets inside bounds). | REQ-UX-05 |
| REQ-DPI-04 | S | Screens needing larger minimums (e.g. dental chart editor, print preview) declare and enforce their own minimum with graceful auto-expand. | Per-screen policy test. | REQ-CHART-01 |

## 39. Keyboard accessibility & productivity

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-KBD-01 | M | Predictable Tab order per screen (explicit, not accidental), Enter=accept/default action, Esc=cancel/back per dialog rules, visible focus rings from tokens, mnemonics on dialogs. | Focus-order tests (Qt accessible interface) per screen inventory; focus-visible screenshot assertions. | REQ-UX-04 |
| REQ-KBD-02 | M | Shortcuts: global search (Ctrl+K), new record context (Ctrl+Ins/Ctrl+N), save (Ctrl+S), close tab (Ctrl+W), lock (Ctrl+L), print (Ctrl+P where applicable), nav sections (Alt+1..9); documented in-app shortcut reference. | Shortcut registry test: every declared shortcut has a handler and appears in help; no duplicates. | REQ-SHELL-03 |
| REQ-KBD-03 | M | Shortcuts never bypass authorization or destructive safeguards: handlers route through the same service paths and confirm dialogs. | Bypass test: Ctrl+delete style destructive attempts still gated (same as REQ-RBAC-05). | REQ-RBAC-05 |
| REQ-KBD-04 | S | Accessible naming for screen readers on interactive controls; contrast ratios from token palette meet WCAG AA (4.5:1 text). | AX-name inventory test; contrast unit tests over token pairs. | REQ-UX-01 |

## 40. Printing subsystem (engine-level)

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-PRINT-01 | M | Print profile system: profiles capture printer selection, paper size (A4, A5, 80 mm, 58 mm, custom W×H), orientation, margins, scaling, document type; profile resolution order: explicit choice → doc-type default → system default; profiles editable in Settings. | Profile service tests incl. custom sizes; resolution order matrix. | REQ-SET-04 |
| REQ-PRINT-02 | M | **Single renderer guarantee:** preview, PDF export, and physical printing all render from the same layout pipeline at the chosen paper's metrics — the preview is the actual document model, not an approximation. | Equivalence test: rasterize preview-pixmap vs printed-PDF vs QPrinter-output per fixture → perceptually equal (thresholded). | REQ-ARCH-01 |
| REQ-PRINT-03 | M | Layout engine adapts to paper dimensions: content never overlaps or clips; font sizes scale within documented min/max bands for receipt widths; header/body/footer restructure per width class (full A-series layout vs receipt layout). | Golden layout suite across 5 paper profiles × doc types incl. pathological content. | REQ-UX-05 |
| REQ-PRINT-04 | M | Multi-page behavior: item tables paginate with header repetition, "page x of y", no orphaned single rows; long Bengali notes flow correctly across pages. | Pagination tests at boundary item counts (0,1,exact-fit,fit+1,200 items). | REQ-PRINT-03 |
| REQ-PRINT-05 | M | PDF output embedded as a first-class path (QPdfWriter, bundled fonts subset-embedded) plus Windows "Microsoft Print to PDF" compatibility; PDF selected in tests as canonical fidelity oracle. | PDF opens in stock reader-independent parse; embedded-font assertion; Print-to-PDF smoke on Windows CI. | REQ-FONT-01 |
| REQ-PRINT-06 | M | Printer selection via native Windows dialog enumerating wired/wireless/Bluetooth drivers exposed by the OS; the app does not assume a specific printer model or presence. | Uses `QPrinter`/`QPrintDialog`; graceful "no printers installed" state on CI (documented hardware-unavailable validation in Phase 11/18). | REQ-PLAT-06 |
| REQ-PRINT-07 | M | Prescription signature area: reserved rectangle, minimum 28 mm height reserved, zero non-whitespace ink inside (except optional thin baseline), positioned lower-right; enforced by the layout engine (assertion, not by manual spacing). | Geometry assertion in every rx golden test; "nothing drawn in signature zone" pixel test (alpha channel). | REQ-RX-05 |
| REQ-PRINT-08 | M | Print preview UI: page-accurate preview at selected profile, zoom, page nav, printer button, PDF button, copies, and duplex where driver allows; preview honors permission gating (restricted users get no financial print options). | E2E per doc type; restricted-user variant test. | REQ-UX-05 |
| REQ-PRINT-09 | S | Reports (list exports) print through the same engine with a generic tabular document template. | Generic template golden + CSV/PDF export tests. | REQ-REPORT-01 |
| REQ-PRINT-10 | S | Thermal behavior notes documented: continuous-feed assumption, max-width layout, dot-density fallback (no images > 1-bit friendly); logo on receipt optional toggle (auto-thresholded). | Docs + golden receipt with logo thresholded variant. | REQ-PRINT-03 |

## 41. Reports

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-REPORT-01 | M | Reports sufficient for clinic management: patient activity, appointment activity (attended/missed by dentist/day), treatment activity (counts/revenue per treatment), prescription activity, invoices (issued/paid status), payments (by method/user), outstanding balances (per patient + aging), income, expenses, inventory valuation/usage, low stock, expiry; standard date filters; CSV/PDF export; print via engine. | Each report has: SQL parity test vs fixtures, RBAC test, export test, empty-state test. | REQ-DATA-09 |
| REQ-REPORT-02 | M | Reports respect RBAC at the service layer (financial reports require `finance.view` + `report.view`); a user may have list access but not export, where configured. | Negative tests per report×permission combination table. | REQ-RBAC-03 |
| REQ-REPORT-03 | S | Report results windowed (e.g. 10k rows) with "export full" streaming path that never loads unbounded result sets into memory. | Streaming export test with row-count + memory guard (<150 MB on 1M-row synthetic). | REQ-ARCH-03 |

## 42. Repository, standards & process

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-GOV-01 | M | Clean repository organization documented and followed: `src/dentiva/{app,bootstrap,core,domain,data,services,security,printing,backup,notifications,search,ui,resources}`, `tests/{unit,integration,gui,security,perf,fixtures}`, `scripts/`, `installer/`, `docs/`, `.github/workflows/`. | Structure conformance test (imports + path rules); ARCHITECTURE §2 matches tree. | REQ-ARCH-01 |
| REQ-GOV-02 | M | Architecture-first: domain model, schema, business rules, permission model, navigation, state, printing, backup, settings, audit, error strategy defined in docs before UI build (Phases 1–3 precede 4+). | This document set; Phase gate reports record adherence. | — |
| REQ-GOV-03 | M | Coding standards & static enforcement: ruff (lint+format), mypy on core (domain/services/data/security/printing/backup), import-boundary architecture tests, no dead code (`vulture`/ruff F401 zero), no `TODO/FIXME` in shipped source. | CI quality job fails on any violation from Phase 2 onward; sweep scripts included. | REQ-ARCH-01 |
| REQ-GOV-04 | M | Living traceability document: every REQ ID maps to implementation location(s) + test IDs + status (implemented-tested / implemented-pending / open), updated at each phase gate with evidence links. | `docs/TRACEABILITY.md` rules + CI check that every REQ-ID in register has a matrix row; every row updated each phase. | — |
| REQ-GOV-05 | M | Living architecture documentation updated per phase (this `docs/` spine), sufficient for future maintenance of a final, non-upgrade product. | Docs-diff required in each phase PR (CI check: phase report references doc updates). | REQ-GOV-04 |
| REQ-GOV-06 | M | Phase gates: each phase ends with a structured completion report (template in `docs/PHASE-REPORTS.md`); continuation only on explicit owner "Continue"; interrupted work resumes from the exact unfinished point after state inspection. | `docs/reports/` contains one report per completed phase; resume-protocol section followed. | — |
| REQ-GOV-07 | M | Honest verification policy: no "test passed" claims without executed evidence; no hardware claims without hardware; environment-validated vs hardware-validated clearly distinguished; no "zero bugs" claims — only documented found-and-fixed + unresolved-issue lists. | Phase reports contain raw test output summaries (counts + failures); audit in Phase 19. | REQ-QA-01 |

## 43. Build, CI/CD & release

| ID | Req | MoS | Requirement | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-BUILD-01 | M | Deterministic production build: pinned toolchain (CPython 3.12.x, PySide6 pin, PyInstaller pin), `onedir` layout, app icon embedded, version metadata in exe, build info JSON (commit, CI run id) embedded; builds on GitHub Actions `windows-latest` only for release artifacts. | Same input commit → identical file list + identical exe/PYZ hashes modulo timestamped resources (documented exceptions); artifact metadata test. | REQ-ARCH-02 |
| REQ-BUILD-02 | M | Production package excludes: dev dependencies, test files, debug code, dev credentials, sample secrets, temporary artifacts, source maps/unneeded data; a manifest audit script enforces exclusions. | `scripts/audit_artifact.py` runs on built tree in CI and fails on forbidden patterns (tests/, `.env`, plaintext activation, `DEBUG=true`). | REQ-ACT-02 |
| REQ-BUILD-03 | M | Installer: Inno Setup 6 (6.4.x pinned for commercial-use licensing, see ADR-015) producing single `DentivaPro-Setup-<version>.exe`, per-machine install to Program Files, app-id GUID, shortcuts, optional launch, uninstall with explicit **data-preserving** policy (app files only; data dir untouched unless user opts in). | CI builds installer; uninstall test on runner: data dir survives; opt-in removal path separate; version upgrade in-place test. | REQ-BUILD-01 |
| REQ-BUILD-04 | M | License audit & bundling: every dependency's license text + attribution shipped in installer (`THIRD-PARTY-LICENSES/`), machine-readable inventory generated from the lockfile, CI policy gate (allowlist: MIT/BSD/Apache-2.0/OFL/PSF/CC0/zlib/LGPL-with-compat-plan; deny GPL/AGPL runtime deps; LGPL components dynamic-import only + relink documentation). | Inventory generation + policy check in CI (both jobs); About screen links to bundled file. | REQ-PLAT-04 |
| REQ-BUILD-05 | M | GitHub Actions CI/CD mandatory: `quality.yml` (lint, type, unit/integration/gui on ubuntu-latest offscreen, migration chain, artifact audit dry-runs) and `release.yml` (windows-latest: build → run **full test suite against the built artifact** → installer → validate outputs → fail loudly otherwise). Workflows must fail rather than silently succeed. | Both workflows green on Phase-2 skeleton and every later phase; deliberate-fault branch test proves failure propagation (one-time, recorded). | REQ-GOV-03 |
| REQ-BUILD-06 | M | Release publication via GitHub Releases when possible; if genuinely unavailable (permissions/connector), artifacts + checksums placed in `dist/` with documented fallback state; never left ambiguous. | Release job attempts `gh release create`; fallback job commits `dist/` artifacts; README in `dist/` updated with actual outcome each release. | REQ-BUILD-05 |
| REQ-BUILD-07 | M | Integrity info for release: `SHA256SUMS.txt` + manifest JSON (artifact, size, hash, version, commit, CI run URL); checksum verification step documented for clinics. | Sums validated in CI and in `dist/` fallback; doc instructions present. | REQ-BUILD-06 |
| REQ-BUILD-08 | M | PRs are never auto-merged; merges are the product owner's manual decision; branch/PR workflow respects the gate and stops at merge-gate with a handoff report. | Repo settings + workflow policy; phase reports state gate status. | REQ-GOV-06 |
| REQ-QA-01 | M | Automated tests for every major feature — positive **and** negative — executed (not claimed): unit, integration, GUI(offscreen), security, perf, chaos; coverage gate on services/domain (≥85% lines, branch on money/authz paths 100%). | Coverage report enforced in CI; test inventory mapped in TRACEABILITY. | REQ-GOV-04 |
| REQ-QA-02 | M | Stress/reliability: 50k patients / 200k visits / 100k invoices synthetic datasets (generator committed), search/list/profile/report budgets, long-session and repeated open/close cycles, rapid-interaction fuzzing, backup/restore at scale, abnormal-termination matrix; results in phase report with numbers. | `scripts/gen_stress_db.py` + perf suite thresholds; Phase 17 report tables. | REQ-PERF-* |
| REQ-QA-03 | M | Clean-machine validation (Phase 18) on a Windows VM without dev tools: install, activation, setup wizard, login, all module flows, printing (PDF + any available printer), backup/restore, uninstall(+reinstall keeping data). Results (including hardware-unavailable items) documented. | Phase 18 checklist file with pass/fail per row + evidence screenshots/logs. | REQ-BUILD-03 |
| REQ-QA-04 | M | Final release gate: no known unresolved release-blocking issue; Phase 19 re-check of master prompt line-by-line vs implementation with three-state statuses; anything "needs correction"/"not implemented" blocks release. | `docs/reports/phase-19-release-audit.md` with per-requirement statuses + evidence; gate checklists green. | REQ-GOV-04 |

## 44. Cross-cutting performance budgets (REQ-PERF)

| ID | Req | MoS | Requirement (budget) | Acceptance criteria | Depends on |
|---|---|---|---|---|---|
| REQ-PERF-01 | M | Cold start (exe → interactive shell, existing data) ≤ 4 s on reference machine class (i5/8GB/SSD); warm ≤ 1.5 s. | Timed launch CI metric + Phase 17 stress machine. | REQ-BUILD-01 |
| REQ-PERF-02 | M | Patient search p95 ≤ 300 ms at 50k patients; list page (50 rows) ≤ 150 ms. | Perf suite `test_search_perf`. | REQ-DB-02 |
| REQ-PERF-03 | M | Any list/table view switches ≤ 400 ms perceived (first paint); loading states bridge longer operations. | GUI perf tests offscreen. | REQ-ARCH-03 |
| REQ-PERF-04 | M | Save/finalize flow commit p95 ≤ 250 ms (typical record graph); UI never blocks > 100 ms synchronously (long ops off-thread). | Worker pool + timing asserts. | REQ-ARCH-03 |
| REQ-PERF-05 | M | Invoice/receipt print preview first page ≤ 500 ms incl. pagination scan; PDF export ≤ 2 s. | Print harness timers in CI. | REQ-PRINT-02 |
| REQ-PERF-06 | M | Backup of 500 MB data set ≤ 60 s on SSD with progress; UI responsive throughout. | Measured in Phase 17 suite. | REQ-BKP-04 |
| REQ-PERF-07 | M | Steady-state RSS ≤ 450 MB during normal browsing; leak guard: ≤ +20 MB growth after 100 navigations. | psutil-based CI guard. | REQ-ARCH-03 |

The budget table in `docs/TESTING.md` §7 and the numbers in `docs/ARCHITECTURE.md` §12 are restatements of this normative table; they may be tightened during audits but never loosened silently — any change to a budget requires the AC hash in `docs/TRACEABILITY.md` to change and the owning phase gate to re-pass.

---

## Coverage manifest — master prompt → requirement mapping (every statement reviewed)

Reading order follows the master prompt paragraphs. This manifest demonstrates that **no requirement statement was skipped**; each maps to at least one REQ ID above or to a conflict/decision record.

| Master prompt theme | Mapped to |
|---|---|
| Commercial Windows product framing; not demo/mockup | REQ-PROD-01, REQ-PROD-06, REQ-QA-01..04 |
| English UI, Bengali data, BDT | REQ-PROD-02, REQ-PLAT-01, REQ-LOC-*, REQ-DATA-09, REQ-MONEY-02 |
| Offline-first, no paid services | REQ-PLAT-03, REQ-PLAT-04 |
| Stack selection with documented rationale before code | REQ-GOV-02 + all ADRs |
| Coherent architecture; screens wired to logic; no fake UI | REQ-PROD-05, REQ-PROD-06, REQ-SHELL-*, REQ-QA-01 |
| Premium identity; design system tokens; states; DPI | REQ-UX-*, REQ-DPI-* |
| Animations | REQ-UX-07 |
| Application icon generation & validation | REQ-UX-08 (generation executed Phase 4, verified at packaging Phase 18) |
| First-run setup wizard (clinic, dentists, admin account, atomicity) | REQ-SETUP-* |
| Activation code `1516591935015165`, no plaintext, honest limitation | REQ-ACT-* (CONFLICT-C1) |
| Shell header, collapsible grouped nav, named modules + additions | REQ-SHELL-*, REQ-NAV-01/02 |
| Dashboard widgets + permission-aware | REQ-DASH-* |
| Patients: unlimited, codes, fields, list filters, search, profile, actions, repeated visits | REQ-PAT-* |
| Dental chart adult/pediatric, surfaces, historical | REQ-CHART-* |
| Clinical timeline, auditability, no silent rewrite | REQ-TIMELINE-01 (within REQ-PAT-09/REQ-VISIT-03), REQ-AUDIT-01 |
| Treatment catalog + price history immutability | REQ-TREAT-* |
| Prescriptions (profile+module, items, reorder, PRN), C/C–O/E–R/E library, flagship print design, signature space, A4/A5/mini, printers, PDF, Bengali print | REQ-RX-*, REQ-CLINLIB-*, REQ-PRINT-* |
| Invoices identity/hierarchy, itemization, payments/partial/balance, printing all formats | REQ-BILL-* |
| Payments history, methods incl. wallets, date filters, Decimal money | REQ-BILL-05..08, REQ-DATA-09 |
| Financial enforcement at business layer | REQ-RBAC-03..05, REQ-BILL-10, REQ-DASH-02, REQ-ACC-04 |
| Inventory (fields, movements, expiry, low-stock, traceable) | REQ-INV-* |
| Accounting (categories, reports, honest positioning) | REQ-ACC-* |
| Staff & Users separation | REQ-STAFF-* |
| Granular RBAC incl. invoice-create-without-reports case | REQ-RBAC-* |
| Argon hashing, sessions, auto-lock 5/10/15/30, step-up | REQ-AUTH-* |
| Notification center semantics | REQ-NOTIF-* |
| Appointments statuses incl. no-show/reschedule, history | REQ-APPT-* |
| Queue real-operation, state persistence | REQ-QUEUE-* |
| Referrals | REQ-DATA-08 |
| Attachments managed storage, validation, open, metadata | REQ-ATT-* |
| Backup/restore full matrix incl. pre-restore backup, multi-file, integrity | REQ-BKP-* |
| Settings hub, printer profiles | REQ-SET-* |
| Destructive safeguards | REQ-DEL-* |
| About (Dentiva Pro, Shohan Khan, email) | REQ-ABOUT-01 |
| Advanced global search, permission-filtered | REQ-SEARCH-* |
| Audit log | REQ-AUDIT-* |
| Relational schema, no CSV multi-values, constraints/indexes | REQ-DB-*, REQ-DATA-* |
| Transactions/fail-safe ops | REQ-TXN-*, REQ-DATA-04 |
| Crash recovery | REQ-TXN-03/04, REQ-ERR-01 |
| Structured logging, no sensitive leak | REQ-LOG-* |
| Loading/empty/error/validation states everywhere | REQ-UX-04, REQ-SHELL-06 |
| Scrolling, alignment, overflow rules | REQ-UX-05/06 |
| Keyboard accessibility & shortcuts, no bypass | REQ-KBD-* |
| Print profiles, preview accuracy, Bengali print verification | REQ-PRINT-*, REQ-FONT-* |
| High-DPI matrix, resize/min sizes | REQ-DPI-* |
| Validation incl. BN phone leniency | REQ-VAL-* |
| Date/time determinism, Dhaka | REQ-DATE-* |
| Money decimal safety | REQ-DATA-09, REQ-MONEY-* |
| Reports minimum set | REQ-REPORT-* |
| Outstanding balance & settlement history | REQ-BILL-05/08, REQ-PAT-10 |
| Current-vs-historical snapshotting | REQ-DATA-05, REQ-PAT-11, REQ-RX-06, REQ-TREAT-03 |
| Finalization state transitions | REQ-FINALIZE-01 (see REQ-VISIT-03, REQ-RX-04, REQ-BILL-04, REQ-DATA-06) |
| Error boundaries, no stack traces to users | REQ-SHELL-05, REQ-ERR-01 |
| Packaging/installer/uninstaller behavior | REQ-BUILD-03, REQ-QA-03, REQ-PROD-09 |
| Deterministic build hygiene | REQ-BUILD-01/02 |
| Repo structure | REQ-GOV-01 |
| GitHub Actions mandatory, fail-loud | REQ-BUILD-05 |
| Releases or dist fallback | REQ-BUILD-06/07 |
| No auto-merge | REQ-BUILD-08 |
| Phased development, phase reports, resume protocol | REQ-GOV-06, `docs/ROADMAP.md`, `docs/PHASE-REPORTS.md` |
| Phase 1 scope statement | This document set (all files listed in README) |
| Traceability living doc | REQ-GOV-04 |
| Architecture/dev docs living | REQ-GOV-05 |
| Multi-everything assumptions forbidden | REQ-PROD-07 |
| No arbitrary record limits, performance via indexes/pagination | REQ-PAT-01/05, REQ-DB-02, REQ-PERF-* |
| Real-world claims limitation (no medical/statutory claims) | REQ-PROD-04 |
| No silently dropped requirements; conflicts documented | REQ-GOV-02, `docs/CONFLICTS-DECISIONS.md` |
| No paid APIs/cloud; GitHub only for dev/release pipeline | REQ-PLAT-03 (scope note in CONFLICTS-D2) |
| Honest test/hardware claims | REQ-GOV-07 |
| Don't stop at "it launches"; exercise everything | REQ-QA-01..04, phase gates |
| Correctness over speed | REQ-GOV-02..06, roadmap gates |
| Final recheck & absolute gate | REQ-QA-04 |
| Coherent product feel first launch → uninstall | REQ-PROD-09 |

## Gap analysis summary (missing requirements added by this phase)

The master prompt is unusually complete; normalization nonetheless identified the following **mandatory production requirements not explicitly stated** — all assigned IDs above and marked **[GAP→addition]** where tied to a REQ: working-hours/slot policy (REQ-DATE-03), duplicate-patient detection UX (REQ-VAL-01), archive-vs-delete policy per entity (REQ-DEL-02), note versioning (REQ-DATA-10), restart-persistence guarantee (REQ-PROD-08), single-writer lock (REQ-TXN-04), text normalization policy (REQ-LOC-03), i18n groundwork (REQ-LOC-04), crash bundle (REQ-LOG-03), streaming exports (REQ-REPORT-03), performance budgets (REQ-PERF-*), install/upgrade coexistence and data-location bootstrap (REQ-BUILD-03, REQ-DATA-03), print-to-PDF driver path (REQ-PRINT-05), backup destination health (REQ-BKP-07), dashboard deep links (REQ-DASH-04), per-user notification state (REQ-NOTIF-02), unsigned-build guidance (REQ-PLAT-07), and a global route/permission self-check (REQ-RBAC-05).

**Phase 1 coverage statement:** every requirement in the master prompt was read, normalized into an ID with acceptance criteria, dependency-mapped, conflict-checked, and entered into the traceability matrix. Nothing was silently removed or substituted.
