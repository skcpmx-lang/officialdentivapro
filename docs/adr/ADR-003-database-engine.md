# ADR-003 — Database engine: SQLite (WAL, integrity-hardened); SQLCipher deferred to 1.0.1 evaluation

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-DB-02, REQ-TXN-*, REQ-BKP-*, REQ-DATA-*, CONFLICT-C2

## Context
The product stores clinical records and finances for single-station Windows
PCs, offline, with strong reliability demands (crash safety, backup/restore,
integrity checks) and moderate concurrency (one writer process).

## Decision
**SQLite 3.4x+ (bundled via the frozen runtime), production configuration:**
- `journal_mode=WAL`, `synchronous=FULL`, `foreign_keys=ON`, `busy_timeout=5000`, `temp_store=MEMORY`, tuned `cache_size`; `PRAGMA user_version` migrations stamp.
- WAL + `-shm`/`-wal` files live beside the DB in the data dir; **clean-shutdown checkpointing** and startup `PRAGMA integrity_check` gated by an owner-flag file that detects abnormal termination (REQ-TXN-03/04).
- Single-process discipline enforced by an exclusive lock file in the data dir (friendly refusal message; REQ-TXN-04).
- Attachments are **never** BLOBs in the DB — managed content-addressed files (ADR-012) keep the DB lean and backup-friendly.
- FTS5 (bundled in standard SQLite) for patient-name/note free-text search, external-content tables to avoid duplication (REQ-PAT-05).

Encryption-at-rest: **explicitly deferred**. v1.0 relies on Windows user-profile isolation (data under `%LOCALAPPDATA%`), and documents residual risk in SECURITY §8. **1.0.1 evaluation path (non-gating):** ship optional build profile with `sqlcipher3-wheels` (BSD/zlib; verified cp312 win_amd64 wheels) + key protected by Windows DPAPI (`CryptProtectData`, no key in code) — architecture keeps a driver seam (ADR-004 §engine factory) so this is additive, not a rewrite. This avoids: backup-container coupling, wheel fragility on pinned CPython, and DPAPI-vs-roaming complexity, in exchange for a documented honest gap for 1.0.

## Alternatives considered
- **SQLCipher immediately:** real privacy gain, but complicates backup verification, WAL handling, restore flows, and packaging on the pinned interpreter; each added failure mode threatens the reliability requirements more than the threat it mitigates for the assumed attacker model (physical PC theft, where BitLocker guidance matters more). Deferred with a concrete seam.
- **PostgreSQL embedded (portable distribution):** operational weight (service, ports, pgpass, corruption surface) absurd for a clinic desktop app. Rejected.
- **DuckDB:** analytics-first, not a transactional record system. Rejected.
- **TinyDB/JSON stores / SQLAlchemy+no schema:** cannot express FK/CHECK/trigger-grade integrity or indexed query performance required by REQ-DB-01/02. Rejected.
- **Access/Jet:** archaic, corruption-prone, Windows-legacy. Rejected.

## Consequences
- Zero-configuration, zero-service data layer that meets every reliability requirement offline.
- Documented residual risk (unencrypted-at-rest for 1.0) with BitLocker recommendation for clinics (SECURITY §8, About/Setup tips).
- All DB SQL must remain portable within SQLite; no vendor assumptions beyond it.
