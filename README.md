# Dentiva Pro

**Premium offline-first dental clinic management software for Windows — built for dental clinics in Bangladesh.**

- Interface language: professional English; all clinical and business data may be entered and printed in **Bengali Unicode**, Latin, or mixed.
- Currency: **Bangladeshi Taka (BDT / ৳)**, decimal-safe end to end.
- Fully **offline**: no cloud, no paid APIs, no subscription services in the core product.
- Status: **Phase 1 complete** — product discovery, requirements normalization, architecture strategy, and implementation roadmap. Implementation begins in Phase 2 (see `docs/ROADMAP.md`).

> ⚠️ This repository is currently in the planning/foundation stage. No production application code or functionality exists yet. Every module listed below is scheduled and tracked in the traceability matrix; nothing here should be presented or mistaken for a working product until its phase gate passes.

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
| [`docs/PHASE-REPORTS.md`](docs/PHASE-REPORTS.md) | Phase report template and the running index of completed phases. |

## Repository plan (established in Phase 2)

```
src/dentiva/          # application package (app, domain, data, services, ui, print, backup, security, i18n, resources)
tests/                # unit / integration / gui / security / perf suites
scripts/              # build, packaging, validation, dataset-generation scripts
installer/            # Inno Setup configuration
docs/                 # this documentation spine
. github/workflows/   # CI/CD (quality + windows release)
```

## Release artifacts

Final distributables are published through GitHub Releases when the connected
environment permits; otherwise they are placed in `dist/` with the fallback
documented (see `docs/BUILD-RELEASE.md` §6). `dist/README.md` always explains
the current state of local artifacts.

## Credits

Created and developed by **Shohan Khan** — helloiamshohan@gmail.com.
