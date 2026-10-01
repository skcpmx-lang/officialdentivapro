# Dentiva Pro — Phase Reporting Protocol & Index

Master-prompt rule: "At the end of every phase, stop and produce a structured
phase completion report. Continue only when the product owner explicitly says
Continue." This file defines the template + ledger. Reports live in
`docs/reports/phase-NN-<slug>.md`.

## Completion definition

A phase is complete **iff** every acceptance criterion in `docs/ROADMAP.md` for
that phase is green with *executed evidence* (CI run URL or archived local run
output) — not because code exists (REQ-GOV-06/07).

## Report template (copy verbatim; sections are mandatory)

```
# Phase NN — <name>
- Owner directive: (record the exact "Continue" that started this phase, or "initial")
- Branch/commit range:
- Objective (from ROADMAP §1):

## Work completed
(module-by-module, honest granularity; include what was NOT done)

## Files/modules created or modified
(list; generated files noted)

## Database changes
(migrations added, seeds, doc-diff — or "none")

## UI changes
(screens/components; state-matrix coverage)

## Tests executed
| suite | runner | passed | failed | skipped | evidence |
(failures: original + re-run status; skips: justification)

## Static checks
lint / type / coverage numbers / arch-conformance / license-audit / secret-scans

## Perf & scale observations
(numbers vs budgets; environment caveats)

## Issues found & fixed
## Known issues & risks (explicit; empty means none — never omitted)
## Decisions made this phase (link ADR/conflict updates)
## Traceability delta (REQ IDs moved to Verified; pending reservations)
## Verification-scope labels
sandbox-verified | windows-CI-verified | hardware-required(available|unavailable) | owner-run(pending|done)

## Next phase
P(n+1) title + prerequisites; explicit stop-gate: "Awaiting owner Continue."
```

## Index

| Phase | Report | Status |
|---|---|---|
| 1 — Discovery, requirements, architecture | `reports/phase-01-discovery-architecture.md` | ✅ Complete (2026-10-01) |
| 2 — Engineering foundation | `reports/phase-02-engineering-foundation.md` | ✅ Complete (2026-10-01; Linux + Windows CI green) |
| 3 — Database/domain/core services | — | Planned |
| 4 — Design system & shell | — | Planned |
| 5 — Onboarding/activation/auth/users/settings | — | Planned |
| 6 — Patients | — | Planned |
| 7 — Appointments & queue | — | Planned |
| 8 — Clinical workflows | — | Planned |
| 9 — Billing & payments | — | Planned |
| 10 — Inventory & accounting | — | Planned |
| 11 — Printing subsystem | — | Planned |
| 12 — Backup/restore, audit UX, notifications | — | Planned |
| 13 — Full integration | — | Planned |
| 14 — UX/UI audit | — | Planned |
| 15 — Security & integrity audit | — | Planned |
| 16 — Functional QA campaign | — | Planned |
| 17 — Stress & reliability | — | Planned |
| 18 — Clean-machine validation | — | Planned |
| 19 — Release audit | — | Planned |
| 20 — Final release build & verification | — | Planned |
