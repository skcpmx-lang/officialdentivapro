# ADR-020 — Dependency lock manager: uv with a committed cross-platform lock

- Status: Accepted (Phase 2)
- Date: 2026-10-01
- Related: ADR-001, ADR-017, ADR-019; REQ-BUILD-01/04/05, REQ-GOV-03

## Context
Dentiva must ship only exact, wheel-available dependencies for CPython 3.12
Windows x64, while Linux CI runs the same locked dependency graph. Dependency
hashes and transitive versions must be reviewed, license-audited, and installed
without ad-hoc upgrades. The sandbox's interpreter is CPython 3.11, so lock
resolution and product-runtime verification are distinct claims.

## Decision
Use **uv 0.12.21** as the lock manager and commit `uv.lock`.

- `pyproject.toml` carries exact direct runtime and tool pins; `uv.lock` carries
  resolved transitive versions and artifact SHA-256 hashes for supported
  platforms.
- CI installs the pinned lock manager, then runs `uv sync --locked` on CPython
  3.12. Lock drift is a hard failure; dependency changes update the lock in a
  deliberate dependency PR/change set.
- `scripts/check_lock_policy.py` computes the locked dependency closure for the
  Windows CPython 3.12 x64 marker environment and requires a compatible wheel
  for every runtime and development package.
- `scripts/gen_license_inventory.py` derives version/license records from the
  lock graph plus installed distribution metadata and fails on version drift,
  missing license identity, or a disallowed runtime license. Qt's LGPL route is
  limited to PySide6-Essentials/Shiboken6 under ADR-019's dynamic-import plan.

## Alternatives considered
- **pip-tools (`requirements.in` + hashed `requirements.txt`):** reliable and
  familiar, but requires a second requirements source of truth and has weaker
  visibility into cross-platform wheel metadata in the committed artifact.
  Rejected for this Windows/Linux matrix.
- **Unpinned pip resolver at install time:** non-repeatable; rejected.
- **Poetry/PDM lock ecosystems:** capable alternatives, but add project/workflow
  semantics not needed here; the chosen workflow can be installed from one
  pinned Python tool and one standards-based `pyproject.toml`.

## Consequences
- The lock manager itself is pinned in the development group and in CI setup;
  `uv.lock` is reviewed, never regenerated implicitly during CI.
- Runtime includes the pinned `tzdata` wheel so `ZoneInfo("Asia/Dhaka")` works on
  clean Windows installations that do not provide an IANA database.
- The lock is scoped to `>=3.12,<3.13`; the sandbox's CPython 3.11 cannot run
  the same lock install as a product-runtime verification. GitHub's pinned
  CPython 3.12 jobs are authoritative for that check.
- License inventory generation is not equivalent to shipping license texts.
  Full attribution texts remain an installer/release deliverable.
