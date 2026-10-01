# Dentiva Pro — Conflicts, Resolutions & Decisions Log (Phase 1)

Rule from the master prompt: *"If a requirement conflicts with another requirement, stop and document the conflict during the planning phase, propose a technically coherent interpretation, and obtain direction if an actual product decision is required. Do not silently substitute a different feature."* This file discharges that rule. Resolved items bind implementation; open items are surfaced at each phase gate until decided.

## A. Requirement conflicts — resolved with professional interpretation

| # | Conflicting requirements | Resolution (binding) | Affected REQs |
|---|---|---|---|
| C1 | "Activation must be secure / not plaintext" vs "fully offline, fixed one-time code" | **Technically impossible to make unrecoverable locally.** Implement derived-hash protection (salted SHA-256 constant in binary, constant-time compare, no plaintext anywhere), and document the limitation verbatim in-app (SECURITY §2). The requirement itself already anticipates this; we adopt the "avoid casual exposure, no false unbreakability claims" reading. | REQ-ACT-02/03 |
| C2 | "Support multiple monitors/printers/clinics" vs "offline desktop product" scope | Interpretation: multi-*entity* support inside one clinic installation (dentists, users, printers, paper sizes) — **not** multi-clinic tenancy and **not** multi-station live sharing. SQLite-on-SMB is corruption-prone; shipping it would violate the data-integrity requirements. 1.0 = one installation = one clinic = one active workstation per data directory. Backup/restore is the migration vehicle between machines. | REQ-PROD-07, REQ-TXN-04 |
| C3 | "Soft-delete where possible" vs explicit destructive powers ("delete all data", reset, delete users) | Both hold: entity-level operations default to archive/soft-delete; **global** destructive operations (reset, delete-all) exist but are admin-only, re-auth + typed-confirmation gated, with mandatory safety backup beforehand. Hard deletes for entities with no history dependency only. | REQ-DEL-*, REQ-DATA-06 |
| C4 | "Preview must be exactly what prints" vs "no paid libraries / offline-only" (paid pixel-perfect engines are the usual shortcut) | Solve architecturally instead of commercially: **one layout engine, three sinks** (preview pixmap, QPdfWriter, QPrinter) consuming identical layout output (ADR-010). Pixel fidelity is then a code-path identity, not an approximation. Physical-printer ink-level fidelity cannot be *guaranteed* by any software (drivers rasterize) — stated honestly in docs and verified by hardware test when hardware exists. | REQ-PRINT-02, REQ-GOV-07 |
| C5 | "Secure passwords / modern work factor" vs usability on old clinic PCs (hash must be verifiable fast enough to not annoy, slow enough to resist offline attack) | Argon2id with tiered policy: default m=64 MiB, t=3, p=4 (OWASP high-end) with automatic **degrade-to-minimum profile** (m=19 MiB, t=2) detected by a 1-second calibration probe on first login after install; rehash-on-login upgrades/lowers transparently. Password policy: ≥ 8 chars for staff, ≥ 12 for admin (no composition theater beyond length+common-password refusal). | REQ-AUTH-01 |
| C6 | "Appropriate validation" vs "must not reject legitimate Bangladeshi data" | Lenient-by-default validator design: phone accepts `01X-XXXXXXX`, `+8801XXXXXXXXX`, `09606…`/`096XX…` service codes, spaces/dashes variants; anything else yields a **warning, not a block**. Hard blocks only where data integrity demands (duplicate username, past-DOB dates, negative money). Documented in `docs/REQUIREMENTS.md` REQ-VAL-01. | REQ-VAL-01 |
| C7 | "Print on A4/A5/thermal/mini/Bluetooth" vs "no reliance on one printer model" | Treat Windows as the abstraction: enumerate drivers via Qt; support named paper presets + arbitrary custom widths; PDF path is the universal fallback and the test oracle. "All printers work" is explicitly *not* claimed; "all drivers that Windows exposes are addressable, with per-profile tuning" is what is implemented and tested. | REQ-PLAT-06, REQ-PRINT-* |
| C8 | Python-language mandate vs newest CPython (3.14/3.15) availability vs dependency wheel maturity (e.g. sqlcipher3-wheels publishes cp312; broad Windows wheel coverage lags newest CPython) | Ship on **CPython 3.12.x (latest patch, pinned)** for 1.0 — mature wheels for every dependency, LTS-quality behavior, PyInstaller-supported. 3.13/3.14 evaluated at Phase 19 as an optional re-pin if the full wheel matrix validates; not a release criterion. | ADR-001, REQ-BUILD-01 |
| C9 | Bengali-in-UI freedom vs "professional English primary interface" | Interface chrome = English only in 1.0 (i18n catalog ready for later, REQ-LOC-04); all *content* areas accept and render Bengali. No mixed-language labels. | REQ-PROD-02, REQ-LOC-02 |
| C10 | "Historical invoices must retain charged amounts" vs "patient list must show outstanding balance reflecting later payments" | Two different data paths, both required: document snapshots (immutable, printed truth) vs ledger-derived balances (live, computed). Enforced by schema separation (DATABASE.md §6). Never store a mutable "balance" on the invoice row. | REQ-DATA-05, REQ-BILL-08 |
| C11 | Signature zone "sufficient blank space" vs dense receipt (58 mm) formats | Layout rule: signature zone minimum height is preserved on every width class; on receipt widths the zone becomes a bottom band with 18 mm clearance, and medicine table compresses first. Engine asserts clearance; it is never traded away silently (overflows paginate instead). | REQ-PRINT-07 |

## B. Environment & capability constraints (must be honest in reports)

| # | Constraint | Consequence & handling |
|---|---|---|
| D1 | The Arena development sandbox is **Linux, headless, no Windows, no physical printers**. | All Windows-shell/print/installer *execution* verification moves to GitHub Actions `windows-latest` jobs (Qt runs fully there incl. offscreen and real `Print to PDF`) and to the product owner's clean-machine checklist (Phase 18). In-sandbox we verify everything verifiable there (PySide6 offscreen, headless logic, PDF generation, Bengali shaping). Phase reports must label each item: `sandbox-verified` / `windows-CI-verified` / `hardware-required(available|unavailable)`. |
| D2 | GitHub connectivity is required **only** for the dev/release pipeline (Actions, Releases) — never for clinic operation. | Recorded as scope clarification of "no internet": runtime has zero network code (REQ-PLAT-03 static scan). |
| D3 | No code-signing certificate is available in this project context. | Artifacts ship unsigned with published SHA-256; SmartScreen guidance documented; signing slot is a parameter in the release workflow so the owner can add it without architecture change (REQ-PLAT-07). |
| D4 | Physical thermal/BT printers likely unavailable even on CI. | Validation = PDF-oracle equivalence + driver-level paper math + (if owner hardware exists at Phase 18) real prints. Reports must distinguish the two (master prompt rule). |
| D5 | Repo currently carries only an initial commit; everything here is greenfield. | Phase 2 scaffolds the tree; this doc set is the committed foundation. |

## C. Product-owner decisions required (default adopted; veto at any phase gate)

Each item has a **default** so development is never blocked; the owner may override before the implementing phase starts.

| # | Question | Default adopted | Overridable where |
|---|---|---|---|
| O1 | Data directory location & multi-station ambition | `%LOCALAPPDATA%\DentivaPro\data` (relocatable; roaming profile excluded); single-station per data dir; LAN multi-station is out of 1.0 (C2). | Settings (relocation); roadmap (post-1.0) |
| O2 | Patient code format | `DVP-` + 6-digit zero-padded sequence, configurable prefix; never reused. | REQ-SET-03 config |
| O3 | Code signing / SMIME | Unsigned + checksums + guidance (D3). | release workflow param |
| O4 | Invoice numbering | `{PREFIX}{YYYY}{-}{5-digit seq}` per calendar year, prefix default `INV-`, credit notes `CN-`; configurable prefix only (sequence continuity guaranteed). | REQ-SET-03 |
| O5 | Password policy | C5 tiers (staff 8+, admin 12+, common-password deny-list ~ top 200). | security settings (display, not enforcement level, in 1.0) |
| O6 | "Delete patient" existence | Offered **only** as archive by default; true delete behind `ops.destructive` + reset-style flow with mandatory backup (C3). Owner can disable hard-delete entirely via feature flag. | settings flag `allow_hard_delete` (default off) |
| O7 | Bengali digits in printed money | Latin digits default; per-clinic toggle (Bengali digits) for prescriptions/invoices; never in audit/export CSV. | REQ-LOC-02 |
| O8 | Brand palette direction | "Clinical teal + deep navy ink" primary family (premium, non-generic; final hexes frozen in design tokens Phase 4). | REQ-UX-01 |
| O9 | Auto-lock default for first admin | 15 minutes (one of the four allowed values). | REQ-AUTH-03 |

## D. Explicit non-goals for 1.0 (documented, not silently omitted)

- Cloud sync, telemetry, analytics, crash upload — forbidden by offline mandate.
- Multi-clinic tenancy; LAN multi-station live database (C2).
- Insurance/claims integration; government reporting formats (not in master requirements; no basis to invent).
- Patient-facing portals/SMS reminders (no paid SMS gateway allowed; Bluetooth/wireless printing is not a comms dependency).
- Machine-learning diagnosis aids (also forbidden by REQ-PROD-04).
- Updater infrastructure — product is declared final non-upgrade version by the owner; only backup/restore and reinstall-over-preserved-data exist.
- Statutory accounting/tax compliance features (REQ-PROD-04/REQ-ACC-05).
- Bengali UI localization (English primary per mandate; REQ-LOC-04 leaves the door open).

Every non-goal above is traceable to a master-prompt constraint or an explicit gap decision — none removes a stated requirement.
