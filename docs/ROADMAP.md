# Dentiva Pro — Phase Roadmap & Gating (v1.0, Phase 1)

Strictly gated per master mandate. **A phase completes only when its acceptance
criteria pass** — code existing is never completion. Continuation to the next
phase happens only on the product owner's explicit `Continue`.

## 0. Resume & interruption protocol (applies to every phase)

On `Continue` after any interruption: (1) `git status/log` + current branch
state; (2) read latest report in `docs/reports/` and its "Next/Outstanding"
sections; (3) run quality gates (`scripts/dev_checks.py`) to establish ground
truth of code vs docs; (4) update `docs/TRACEABILITY.md` statuses from *observed*
test results, not memory; (5) resume the **unfinished phase** first — never skip
later-file existence as proof of earlier completion. Every phase ends with a
report from `docs/PHASE-REPORTS.md` template committed in the same change set.
PR/branch workflow: work lands on the session branch; PRs may be opened;
**merges are the owner's manual gate** (REQ-BUILD-08) — at merge-ready state we
stop and hand off, never merge.

## 1. Phase plan (2–20)

### Phase 2 — Engineering foundation
- **Deliver:** repo tree per ARCHITECTURE §2; `pyproject.toml` + committed `uv.lock`; pinned ruff/mypy/pytest/pytest-qt configs; `scripts/dev_checks.py`; bounded rotating logs + labelled-field redaction + local crash-bundle writer; SQLite engine factory with ADR-003 pragmas, OS lockfile, and atomic abnormal-shutdown flag; Alembic environment + empty `0001_foundation_baseline`; `core/` errors, Money, Dhaka Clock, decimal units, gettext catalog extractor; deterministic activation derivation + published non-secret vectors; `quality.yml` and Windows `release.yml` foundation validation (including expected-red lint probe); `installer/README.md` contract stub + `scripts/audit_artifact.py` dry-run wired to CI; lock/license inventory generators; docs updates.
- **Accept:** both GitHub workflows green on CPython 3.12; locked CPython 3.12 Windows x64 wheel policy passes; architecture and no-network-import tests pass; `python -m dentiva --smoke` creates/closes the foundation shell with the Qt offscreen platform and exits 0; activation vectors pass. The Windows workflow is validation only: no installer, product artifact, or publication is produced in this phase.
- **Gate to P3:** both workflows green; zero TODO/FIXME/placeholder markers in `src/`; lock-derived runtime license inventory is generated and policy-checked. The shell is not a clinic workflow and no domain schema is claimed beyond the empty baseline.

### Phase 3 — Data domain & core services
- **Deliver:** full SQLAlchemy models per DATABASE.md + `0001_initial` + seeds machinery; repositories + UoW + CommitGate; permission engine + `@requires` + grants-versioning; audit chain writer/verifier; settings typed store; attachments store (pipeline w/o UI); backup container format writer/validator/restorer + journal (headless services); activation service (state machine); auth service (argon2 policy/calibration/sessions/step-up); validation library; FTS sync; conformance test suite (schema-vs-doc, decorator inventory, cascade policies); fault-injection harness; perf micro-baseline (50k synthetic).
- **Accept:** unit+integration coverage gate met for these packages; migration from 0001..head matrix green; kill-soak 20× clean; authz negative suite skeleton all-denied where expected; backup completeness test green headless (restore into temp dirs).
- **Gate to P4:** every service used later exists *tested*; no UI beyond a bare shell window.

### Phase 4 — Design system & application shell
- **Deliver:** token system frozen (ADR-018 visuals) + component gallery; shell (header per REQ-SHELL-01, collapsible grouped nav, router+guards, status/busy bar, toast system, dialog framework, lock screen UI, notification center UI shell); global icon set generated + **Dentiva Pro app icon generated & validated per REQ-UX-08 at all sizes** (generation via image tooling, inspection checklist in report); offscreen screenshot baselines; DPI matrix pass on CI + recorded human-matrix protocol; window min-size/resize invariants; empty/loading/error vocabulary components.
- **Accept:** gallery golden set; state-matrix tests for all gallery components; DPI sweeps green; nav/route/permission integration tests; icon QA table complete in report.
- **Gate to P5:** shell + tokens freeze; any visual debt ticketed & fixed or consciously accepted *documented*.

### Phase 5 — Onboarding, activation, auth, users/roles, settings, About
- **Deliver:** activation screen (REQ-ACT-*), first-run wizard (atomic, resumable), login/lock/step-up UX, Staff & Users screens, Role editor, Settings hub skeleton (Clinic, Dentists, Preferences, Security) + About, audit viewer v1, notification rule wiring (auth events live).
- **Accept:** E2E install-like boot (fresh dir) → activation → wizard → admin login → settings round-trips → restart persistence; interruption matrix at each wizard step; bypass tests (route/hotkey/service) against seeded roles; auto-lock timing suite (fake clock); About compliance with REQ-ABOUT-01/04 wording.
- **Gate to P6:** setup/authz/settings provably enforced; no clinical data paths exist yet.

### Phase 6 — Patients domain
- **Deliver:** patient registration/edit (validation incl. BN phone leniency), patient code service, list (date filters, keyset paging, default recent), advanced search + FTS, profile page (all sections wired to services incl. timeline projection, notes chain, attachments UI, referral list), duplicate-review flow, archive flow (REQ-PAT-12), patient quick-action rail (visit/appt/invoice/rx/payment/attachment/note/referral openers).
- **Accept:** CRUD E2E with persistence; 50k-dataset budgets (reduced CI scale); Bengali long-name torture; restart persistence; timeline parity test; duplicate detection fixture; archive semantics incl. history retention.
- **Gate to P7:** patient data layer is the reference-quality integration exemplar.

### Phase 7 — Appointments & queue
- **Deliver:** calendar (day/week/list) + appointment CRUD + status transitions UI, reschedule/cancel with history, check-in → queue atomic action, queue board (order/priority/actions/persistence), dashboard appointment widgets live, notification rules (upcoming/missed), working-hours config effects.
- **Accept:** transition-matrix E2E; queue survives navigation/restart (REQ-QUEUE-03); attended-vs-missed report views; double-booking policy tests; drag-rescheduling invariants (no data loss).
- **Gate to P8.**

### Phase 8 — Clinical workflows
- **Deliver:** visit builder (C/C, O/E, R/E+advice with library pickers + free text), dental chart editor (adult/pediatric FDI, surfaces, episodic findings, legend from catalog), treatment plan lines from catalog, prescription composer (draft editing/reordering, options catalogs, PRN), finalization flows + amendment viewer, clinical library admin UI, treatment catalog admin UI, timeline integration (visits/rx/chart events), notification hooks (nothing financial yet).
- **Accept:** multi-visit history integrity tests (REQ-PAT-09/REQ-CHART-03), finalize/amend audit checks, picker round-trips with Bengali entries, chart property tests (hypothesis: no overlap of finding rects, current-status derivation), large patient chart perf.
- **Gate to P9.**

### Phase 9 — Billing & payments
- **Deliver:** invoice builder (catalog/custom lines, discounts, tooth refs), totals engine (poisha), finalize/void flows (ledger-safe), payments module (record/partial/reversal, methods incl. wallets), patient financial history view, outstanding-balance surfaces (permission-gated), dashboard financial widgets live for `finance.view`, receivables report, invoice numbering service (gapless).
- **Accept:** arithmetic property suite; ledger-identity at 1k random sequences; partial/settle flows E2E; RBAC matrix for invoice-create-without-reports role (exact prompt scenario); restart-consistency of balances; snapshot immutability (REQ-PAT-11/REQ-TREAT-03).
- **Gate to P10.**

### Phase 10 — Inventory & accounting
- **Deliver:** stock items + suppliers CRUD, movement ledger UI (purchase/consume/waste/adjust), current-stock derivation + cache parity job, low-stock/expiry rules → notifications + dashboard, accounting entries + categories, salary module, expense↔purchase link (REQ-INV-05), income/expense & method reports, accounting void/reversal, report pack completion (REQ-REPORT-01 list).
- **Accept:** ledger recomputation exactness; negative-stock prevention (or configurable allow-with-warning, documented); report SQL parity; permission enforcement incl. salary masking; stress at 300k movements.
- **Gate to P11.**

### Phase 11 — Printing subsystem
- **Deliver:** full ADR-011 engine (model, layout, sinks, profiles UI, preview UI, print dialog flow), prescription/invoice/receipt templates per PRINTING.md, PDF export, thermal handling, snapshot builders for all doc types, golden corpus + harness, `regen_print_goldens.py`, Windows Print-to-PDF CI leg, hardware-validation protocol doc.
- **Accept:** golden suite green (all fixtures × papers × sinks); signature-clearance property tests; equivalence triad on CI (preview/PDF/Windows-print); Bengali coverage/shaping gates green; draft watermark + reprint markers verified; no-printer graceful state verified.
- **Gate to P12.** *(Physical-hardware rows recorded as hardware-unavailable unless owner provides.)*

### Phase 12 — Backup/restore, audit UX, notifications completion
- **Deliver:** Backup & Restore screens (dest, run, progress, history, validate utility, restore flow incl. multi-file + pre-restore safety), scheduler+retention+catch-up, crash-safe journal UX (recovery dialog), notification rules completion (all REQ-NOTIF-01 types incl. financial gating), audit viewer completion (filters, export, chain banner), Settings backup/notification panes.
- **Accept:** REQ-BKP-06 matrix green incl. corrupted/partial/empty-install/restore-interruption (kill harness); completeness test green (fresh bootstrap restore diff); notification de-dup + per-user state tests; audit tamper detection E2E.
- **Gate to P13.**

### Phase 13 — Full integration
- **Deliver:** connective tissue hardening: every cross-module relationship exercised (patient→visit→chart→rx→invoice→payment→accounting→reports→dashboard→notifications→audit→backup), global search completion, deep-link matrix, cross-module actions from profile, workflow smoke suite (multi-user day simulation), data integrity background checks surfaced in Settings.
- **Accept:** integration scenario suite (scripted clinic day ×3 roles with financial split) green end-to-end; zero disconnected modules (traceability statuses reviewed); search completeness tests per type.
- **Gate to P14.**

### Phase 14 — UX/UI audit (dedicated)
- **Deliver:** systematic visual+interactive audit of every screen per REQUIREMENTS §7/§8 checklist (invisible/clipped/overlap/overflow/alignment/tab states/scrolling/DPI/long text/Bengali/large data), fix-all pass, re-audit, updated goldens.
- **Accept:** audit issue ledger: 0 open severity high/medium at gate; low items explicitly accepted with reason in report; screenshot matrix re-recorded.
- **Gate to P15.**

### Phase 15 — Security & data-integrity audit (dedicated)
- **Deliver:** full execution of TESTING §5 (authz matrix refresh, bypass campaign incl. alternate-path attempts, secret scans incl. binary string sweep, audit chain attacks, backup spoofing, attachment traversal set, lockout/step-up behavior, log redaction corpus), fixes, re-run.
- **Accept:** zero exploitable findings; residual-risk list = exactly the documented ones (SECURITY §8), wording-reviewed; negative-test additions merged to permanent CI.
- **Gate to P16.**

### Phase 16 — Functional QA campaign (dedicated)
- **Deliver:** systematic positive/negative per feature matrix (CRUD, boundaries, invalid/empty/long/dup values, cancel/retry, restart mid-op, DB lock contention, large attachments, multi-payments, multi-dentists, multi-users, backup/restore, print preview, PDF, Bengali, permission edges); scripted manual QA sheets executed offscreen + owner-run Windows sheet where needed; fixes + regression tests for every finding.
- **Accept:** QA ledger: all findings fixed & re-verified or downgraded-with-rationale; full pytest suite green on both OSes; coverage re-gate.
- **Gate to P17.**

### Phase 17 — Stress & reliability
- **Deliver:** full-scale datasets per TESTING §7; perf & leak reports (numbers, not adjectives); 8-hour soak + kill-harness 100×; rapid-interaction fuzz (random clicks/keys via Qt test harness); navigation-cycle leak guard; backup/restore at 500 MB-scale; long-session lock cycles.
- **Accept:** every REQ-PERF budget green on full scale (or documented hardware-normalized adjustment *approved by owner*); zero unexplained errors in soak logs; startup-after-kill clean 100/100.
- **Gate to P18.**

### Phase 18 — Clean-machine & installation validation
- **Deliver:** CI-built artifact installed on fresh VMs (Win10/Win11) per TESTING §9; uninstall/reinstall data matrix; icon/version-info/manifest inspection; SmartScreen guidance tested; **owner-run hardware rows**: printers (if available) recorded honestly.
- **Accept:** checklist 100% rows resolved (pass / owner-delegated with recorded plan); no blocker rows; report + evidence archived.
- **Gate to P19.**

### Phase 19 — Complete release audit (re-check against the master prompt)
- **Deliver:** line-by-line master-prompt → REQ → status → evidence re-read (fresh, from first sentence to last — not memory); TRACEABILITY final sweep: every ID `Verified` or blocked-fixer list; dead-code/TODO/placeholder/license/unused-dep scans; build reproducibility spot check; docs accuracy diff (architecture vs code vs tests).
- **Accept:** **zero** "implemented-needs-correction" or "not-implemented" rows remain (fix + retest loops until true); audit report signed off.
- **Gate to P20 (absolute release gate: no build until green).**

### Phase 20 — Final release build & verification
- **Deliver:** tag → `release.yml` full pipeline on the exact artifact; full suite against installed artifact; checksums + manifest; GitHub Release attempt → `dist/` fallback decision *with evidence*; final production audit report (architecture → release location, known limitations, gate confirmations).
- **Accept:** published (or dist-committed) artifact hash == tested hash; every acceptance criterion in this roadmap green; final report complete.

## 2. Dependency spine (why this order)

schema/services (P3) precede UI (P4) per REQ-PROD-05; authz/activation/setup
(P5) precede data entry (P6+) so every subsequent screen inherits enforced
security; printing (P11) after both document domains (P8/9) exist; backups
(P12) after all persisted shapes stabilize; integration (P13) before audits
(P14–17) so audits attack a *complete* system; clean-machine (P18) needs
release-grade artifact; audit (P19) needs everything; release (P20) gated by all.

## 3. Cross-phase invariants (every phase re-asserts)

1. `quality.yml` + architecture conformance green.
2. No new TODO/placeholder/dead code; sweep scripts clean.
3. TRACEABILITY updated with evidence links; honesty labels on verification scope.
4. Docs (`ARCHITECTURE/DATABASE/SECURITY/PRINTING/BACKUP/TESTING/BUILD-RELEASE`) diffed if behavior changed.
5. Phase report committed; owner "Continue" recorded at top of next report.
