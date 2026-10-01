# ADR-001 — Engineering baseline: language, version pin, and product positioning

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-PROD-01, REQ-PLAT-01/02, REQ-BUILD-01, CONFLICT-C8

## Context
The master prompt mandates Python as the implementation language and a real,
commercially distributable Windows desktop product that runs fully offline.
Python desktop products live or die by packaging fidelity, wheel availability
for the target OS, and long-lived runtime stability.

## Decision
- **Language/runtime:** CPython **3.12.x** (latest patch at build time; pin exact micro in `pyproject.toml`/lockfile). Rationale: every required Windows wheel exists for cp312 (Qt, SQLite tooling, argon2, optional sqlcipher); 3.12 is mature (security releases through 2026), and PyInstaller 6.x fully supports it. 3.13/3.14 evaluated at Phase 19 re-pin gate, never a blocker.
- **Distribution model:** proprietary binary distribution; source private; third-party licenses inventoried (ADR-019).
- **Product claims boundary:** management and clinical-record workflow software; no diagnosis, no statutory compliance claims (REQ-PROD-04).

## Alternatives considered
- **Python 3.14/3.15:** newer; but several Windows-only C-extension wheels (notably sqlcipher3-wheels) publish only up to cp312; free-threaded builds incompatible with Qt bindings. Rejected for 1.0 (compatibility beats novelty for a final release).
- **3.10/3.11:** longer ecosystem support but older; no feature need. Rejected — 3.12 gives better error messages/`zoneinfo` behavior and remains security-supported through 2028.
- **Non-Python stack (e.g. Go/Fyne, C#/.NET, Tauri):** better single-binary packaging or native WPF richness, but explicitly excluded by the "senior Python engineer"/Python-ecosystem framing of this project and by the requirement to justify Python-appropriate tooling. Recorded and rejected on prompt mandate, not on technical grounds.

## Consequences
- All dependency pins must have cp312 win_amd64 wheels (CI verifies).
- Future maintainers must re-validate pins before any rebuild; documented in BUILD-RELEASE §3.
