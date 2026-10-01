# Dentiva Pro

**Premium offline-first dental clinic management software for Windows — built for dental clinics in Bangladesh.**

- Interface language: professional English; all clinical and business data may be entered and printed in **Bengali Unicode**, Latin, or mixed.
- Currency: **Bangladeshi Taka (BDT / ৳)**, decimal-safe end to end.
- Fully **offline**: no cloud, no paid APIs, no subscription services in the core product.
- Status: **Phase 2 — engineering foundation**. The repository now has the pinned engineering toolchain, database/logging foundations, CI, and a minimal headless-testable Qt shell.

> ⚠️ This is **not a clinic-ready or production product**. The shell is only a foundation smoke target; patient, appointment, clinical, billing, reporting, printing, backup, and installer workflows are not implemented. No release artifact is produced by the current workflows. Do not present this repository as a usable clinic system.

## Documentation map

| Document | Purpose |
|---|---|
| [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) | Normalized requirements register — every requirement from the master specification, with IDs, acceptance criteria, dependencies, and gap analysis. |
| [`docs/CONFLICTS-DECISIONS.md`](docs/CONFLICTS-DECISIONS.md) | Requirement conflicts, professional resolutions, open product-owner decisions, and environment limitations. |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System architecture: layers, module boundaries, threading, transactions, error handling, performance budgets. |
| [`docs/DATABASE.md`](docs/DATABASE.md) | Relational schema design: every table, key, constraint, index, snapshot rule, migration strategy. |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Security model: activation, authentication, sessions, RBAC, audit log, threat model, secret handling. |
| [`docs/PRINTING.md`](docs/PRINTING.md) | Printing subsystem: layout engine, print/PDF/preview single-renderer guarantee, paper profiles, Bengali text. |
| [`docs/BACKUP.md`](docs/BACKUP.md) | Backup/restore container format (`.dvpkg`), integrity, scheduling, crash-safe restore protocol. |
| [`docs/TESTING.md`](docs/TESTING.md) | Test strategy: tiers, determinism rules, negative-permission tests, stress datasets, acceptance gates. |
| [`docs/BUILD-RELEASE.md`](docs/BUILD-RELEASE.md) | PyInstaller build, Inno Setup installer, GitHub Actions CI/CD, release artifacts, checksums, dist fallback. |
| [`docs/TRACEABILITY.md`](docs/TRACEABILITY.md) | **Living** requirements → module → test traceability matrix (updated at every phase gate). |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Phase 2–20 plan with acceptance criteria per phase. |
| [`docs/adr/`](docs/adr/) | Architecture Decision Records — every technology selection with rationale and rejected alternatives. |
| [`docs/reports/`](docs/reports/) | Structured phase completion reports. |
| [`docs/dev-setup.md`](docs/dev-setup.md) | Pinned development environment, lock manager, headless Qt setup, and foundation smoke command. |
| [`docs/PHASE-REPORTS.md`](docs/PHASE-REPORTS.md) | Phase report template and the running index of completed phases. |

## Repository plan (established in Phase 2)

```
src/dentiva/          # application package and current engineering foundation
tests/                # unit / integration / gui / security / printing / perf / chaos
scripts/              # quality, lock/license, activation, catalog, and artifact checks
installer/            # reserved installer area; no installer is built in Phase 2
docs/                 # requirements, design spine, reports
.github/workflows/    # quality + Windows foundation validation
```

## Release artifacts

Final distributables are published through GitHub Releases when the connected
environment permits; otherwise they are placed in `dist/` with the fallback
documented (see `docs/BUILD-RELEASE.md` §6). `dist/README.md` always explains
the current state of local artifacts.

## Credits

Created and developed by **Shohan Khan** — helloiamshohan@gmail.com.
