# ADR-004 — ORM / data-access: SQLAlchemy 2.x Core + declarative models, repository/UoW pattern, Alembic migrations

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-ARCH-01, REQ-DB-01..03, REQ-TXN-01, REQ-DATA-04

## Context
The prompt requires an explicit ORM/data-access strategy for a normalized
schema with transactions, migrations, and audit hooks, running on SQLite via a
frozen build.

## Decision
- **SQLAlchemy 2.x** (MIT): declarative ORM for domain entities + **Core** for reporting/aggregate queries (dashboard, reports, search) where hand-written SQL gives index control and predictable plans. `expiring_on_rollback`, typed columns, `Session` bound to a Unit-of-Work.
- **Repository + Unit-of-Work layer** (ADR-006): services never touch `Session` directly; repositories expose intent-level queries; UoW owns `begin/commit/rollback`, flush hooks, and the audit-outbox writer (ADR-009).
- **Alembic** (MIT) migrations: forward-only, linear revision chain, each tagged schema revision tested in CI (`upgrade head from each historical tag`); `schema.md` doc conformance test compares live `sqlite_master` to `docs/DATABASE.md` inventory (REQ-DB-01).
- **Engine seam:** DB URL + connect-args constructed by one factory; this is the hook where an optional SQLCipher profile (ADR-003) or diagnostics (echo in dev) attach without touching code.
- Money/date column types: `Integer` poisha newtypes (`MoneyInt`) + ISO-8601 TEXT timestamps with CHECK format enforcement at DDL level — correctness even if a bug bypasses the ORM.
- FTS5 virtual tables maintained by SQLAlchemy event hooks (insert/update/delete sync), not SQLite triggers — keeps logic in one audited place; performance verified at 50k rows (REQ-PERF-02).

## Alternatives considered
- **Raw `sqlite3` everywhere:** maximum control, but entity/relationship/migration ergonomics would be hand-rolled (bug risk on exactly the integrity requirements this product depends on). Rejected.
- **SQLModel:** thin layer over SQLAlchemy with less mature migration story; adds indirection without capability. Rejected.
- **Tortoise ORM:** async-first, weaker SQLite introspection/migration tooling for this style of app. Rejected.
- **Dataset/Pony/peewee:** peewee is a credible alternative (single-file, MIT, great SQLite fit) but loses Alembic's mature migration graph and the wider Core query toolkit needed for reports; both would force reinventing schema versioning. Peewee recorded as runner-up; rejection is tooling-ecosystem based.

## Consequences
- Pin `SQLAlchemy>=2.0,<2.1` + `alembic` (both MIT; verified py3-none-any, frozen-build friendly — no C extensions).
- Team must respect the rule "ORM for writes/entity flow, Core for aggregates" — enforced via architecture tests (no `session.execute(text(` outside allowed report modules).
- Frozen-build compatibility asserted by CI import smoke (SQLAlchemy/Alembic import clean under PyInstaller with hidden-import list).
