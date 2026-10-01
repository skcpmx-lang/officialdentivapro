# ADR-009 — Authorization: permission-code RBAC enforced in services; tamper-evident audit via hash chain

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-RBAC-01..07, REQ-AUDIT-01..04, REQ-BILL-10, REQ-DASH-02

## Context
The master prompt is explicit: financial and destructive access must be
enforced in business logic, provable with negative tests; audit must resist
casual editing. The app is single-process, so enforcement is about *layer
placement and completeness*, not network authentication.

## Decision
- **Stable permission codes** (dot-namespaced strings, catalog frozen in `docs/DATABASE.md` §9): e.g. `patient.read/create/edit/archive`, `clinical.visit.finalize`, `clinical.chart.edit`, `rx.create/finalize/print/manage_library`, `billing.invoice.create/finalize/print/void`, `billing.payment.record`, `finance.view`, `inventory.manage`, `accounting.view/edit`, `staff.manage`, `users.manage`, `roles.manage`, `settings.manage`, `backup.operate`, `audit.read`, `report.view/print`, `ops.destructive`. `finance.view` is the independent switch the prompt demands (REQ-RBAC-04).
- **Assignment model:** built-in role templates (Owner/Dentist/Front desk/Billing clerk/Inventory) seed the DB; roles hold grants; users get a base role + additive/subtractive overrides; effective set computed once at login, re-checked on every operation via decorator, and invalidated immediately if roles change mid-session (REQ-RBAC-06 "next operation" policy made concrete: session caches `(user_id, grants_version)` and revalidates against DB counter at transaction start).
- **Enforcement point:** `@requires("code")` on every public service operation; the decorator resolves the *ambient principal* from the session context (not from UI state). UI hiding is derived from `permission.can(...)` queries but is cosmetic only. An AST conformance test enumerates public service methods and fails CI if any lacks a policy decorator (deny-by-default; explicit `@public` for the tiny allowlist like clock/format helpers).
- **Audit:** `audit_log` table is append-only (no UPDATE/DELETE API exists; SQLite triggers block UPDATE/DELETE at the engine level as defense-in-depth). Each entry: `(seq, ts_utc, user_id, action_code, entity_type, entity_id, summary, detail_json, hash_prev, hash_cur)` where `hash_cur = SHA-256(hash_prev || canonical(entry))` — a tamper-evident chain verified at startup and on viewer open (REQ-AUDIT-02). Detail JSON passes a redactor (no password material, no full clinical text — REQ-LOG-02 rules apply).
- **Write path:** services enqueue audit entries in the same transaction via the UoW flush hook — a record change without its audit row is impossible by construction (and tested with fault injection).

## Alternatives considered
- **ACLs per record:** over-engineered for one clinic; permissions + row-scope rules (e.g. own drafts editable) live in service predicates instead.
- **JWTs / token plumbing:** pointless inside one process; ambient session + layer tests suffice. Rejected.
- **Row-level triggers for audit:** SQL-side audit loses rich context (before/after) and complicates redaction; app-side within-transaction chosen. Rejected.
- **External signing/HSM chain roots:** out of scope offline desktop; the chain detects casual/manual tampering — its honest ceiling documented (SECURITY §6).

## Consequences
- Negative-authorization test matrix (Phase 5 seed → Phase 15 completion) is a first-class deliverable.
- Permission catalog is versioned: adding codes = migration + docs update; removing = explicit deprecation list.
- Audit chain cost: one SHA-256 per entry — negligible; chain verification at 2M rows must stay < 2 s (windowed incremental verify; perf budget REQ-PERF-07).
