# ADR-007 — Concurrency & threading model: single GUI thread + one controlled worker pool

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-PERF-04, REQ-SHELL-06, REQ-TXN-*, REQ-QUEUE-03

## Context
Qt requires all widget work on the GUI thread. Clinic screens must stay
responsive during search, backup, PDF rendering, and stress-scale queries
(budgets in REQUIREMENTS §44), and "database writes are transactional" must
hold with a single writer.

## Decision
- **One GUI thread** (Qt event loop) and a **bounded worker pool** (default 2 workers + 1 dedicated backup/restore worker, `ThreadPoolExecutor`) with a `JobRunner` abstraction: `run(work, on_done, kind=...)`; results are delivered back via queued Qt signals. UI never blocks > 100 ms synchronously (REQ-PERF-04).
- **One writer, at most one transaction in flight:** services serialize commits through a `CommitGate` (queue + re-entrancy guard). Read-only queries run freely on worker threads (WAL allows readers alongside writer).
- Each worker task creates its **own SQLAlchemy Session** via the container's session factory; sessions never cross threads (asserted in debug builds).
- Long jobs (backup, restore, big exports, stress searches) expose progress + cancellation (cooperative checkpoints) with determinate progress; cancellation is safe by construction (read-only, or transaction abort with rollback).
- Timers (auto-lock, notification scheduler, backup scheduler) are Qt timers on the GUI thread that *schedule* work; schedulers themselves are pure functions of (clock, state) for testability.

## Alternatives considered
- **`asyncio` throughout (qasync):** elegant for I/O-bound web apps; desktop SQLite+Qt work is CPU/latency-bound, qasync adds a runtime coupling risk with PyInstaller and complicates every unit test. Rejected.
- **`QThread` per task without a pool:** thread churn and lifecycle bugs in frozen apps. Rejected in favor of the bounded pool.
- **Any-Q offloading (twisted trio style):** heavier dependency for no benefit here. Rejected.
- **Multi-process workers:** unnecessary isolation cost for SQLite single-writer reality. Rejected.

## Consequences
- UI code paths must never call services synchronously except for trivial cached reads (< a few ms, whitelisted); conformance lint guards obvious violations (service calls from `paintEvent` etc. impossible by structure since painters bind to view-model state).
- Deterministic testing: tests can inject a synchronous executor (`DirectExecutor`) — every worker code path is unit-testable headless.
- Backup/restore worker exclusivity guarantees no UI transaction can interleave with snapshotting (paired with REQ-BKP atomicity).
