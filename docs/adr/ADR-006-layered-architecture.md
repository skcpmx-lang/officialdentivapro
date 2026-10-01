# ADR-006 — Application architecture: layered monolith, single process, explicit composition

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-ARCH-01..04, REQ-SHELL-04, REQ-PROD-05, REQ-GOV-01

## Context
The product must be "a coherent system", not screens bolted onto logic. It is a
desktop app: one process, one user at a time, offline, with hard transactional
and security boundaries. Microservice-style separation would add nothing;
unstructured monoliths fail the traceability and enforcement requirements.

## Decision
A **layered modular monolith** with strict one-way dependencies:

```
ui  →  app (presentation state, view-models, actions)  →  services (use-cases, authorization, transactions)
                                                          ↓
                                       domain (entities, value objects, rules, errors)
                                       data   (SQLAlchemy models, repositories, UoW, migrations)
                                       security, backup, printing, notifications, search, audit (cross-cutting services)
```

- `domain` imports nothing outside stdlib (pure). `data` may import domain. `services` owns UoW + permission checks + validation orchestration. `app` owns view-models, action dispatch, background-job coordination, and route registry. `ui` binds Qt widgets to view-models — **no business rules, no SQL, no repository access in UI**.
- **Composition root** (`bootstrap/container.py`) is the only place wiring real instances (DB engine, services, printers, clock, scheduler). UI/test layers receive via constructor/DI — enabling the fault-injection and offscreen test strategies.
- **Architecture conformance tests** (Phase 3, CI every phase): import-graph checks (`import-linter`-style rule engine, custom implementation to avoid an extra dep), "UI layer contains no `select(`/`session.`" grep-rule, service methods carry `@requires(...)` decorators (AST-checked inventory), error boundary wraps every action dispatcher.
- **Errors:** typed hierarchy `DentivaError(Validation|Permission|NotFound|Conflict|Integrity|BackupIntegrity|IO)`, mapped at the boundary to user dialogs + error-id-keyed logs (REQ-ERR-01).
- **Clock/injectable time:** all "today" logic through a `Clock` service (Asia/Dhaka aware) — determinism in tests and across restarts.

## Alternatives considered
- **MVVM framework layer:** Qt signals + lightweight view-models achieve the same separation without a third-party binding framework (none are mature in Python/Qt). Adopted pattern informally, enforced by tests instead of framework structure.
- **Hexagonal/ports-heavy:** overkill for one-process desktop; the service layer *is* the ports boundary. Simplified consciously.
- **UI-driven scripting (no service layer)** typical of small PyQt apps: fails REQ-RBAC-03 (enforcement outside UI) and testability. Rejected explicitly.

## Consequences
- One process = simple lockfile discipline, no IPC classes, clean crash semantics (REQ-TXN-04).
- Discipline is automated (conformance tests), not aspirational.
- Every phase report must show the conformance suite green.
