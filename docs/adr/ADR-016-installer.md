# ADR-016 — Installer: Inno Setup 6.4.3 (free-for-commercial licensed version), data-preserving uninstall

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-BUILD-03, REQ-PLAT-02, REQ-PROD-09, CONFLICT-O3

## Context
Commercial distribution to clinics, installable on clean Windows by a
non-technical user; uninstall must never silently destroy clinic data; single
`.exe` artifact; CI-headless build.

## Decision
- **Tool:** Inno Setup **6.4.3**, pinned. Its license (BSD-like, jrsoftware) permits free commercial use through 6.4.x; 6.5.0+ moved commercial use to paid licensing, so the pin is a **licensing decision** recorded here (upgrade only if the owner purchases a license — flagged in BUILD-RELEASE §4).
- **Package:** per-machine install (`PrivilegesRequired=admin`), default `Program Files\Dentiva Pro`, app-id GUID fixed, `ArchitecturesInstallIn64BitMode=x64compatible`, LZMA2 solid compression, single `DentivaPro-Setup-<version>.exe`.
- **Behavior:** modern wizard pages — license (EULA), location, tasks (desktop shortcut, launch after), install progress; upgrade = in-place over previous (same GUID) with running-app check (`CloseApplications`), data dir untouched; downgrade refused with message.
- **Uninstall:** removes app files + shortcuts + registry entries; **never** touches `%LOCALAPPDATA%\DentivaPro` (data preservation); optional task (default OFF) "also delete clinic data" requiring that checkbox to be an explicit choice on the uninstall confirmation page — per prompt's explicit-and-safe strategy. Leftover data dir gets a README pointer. Uninstall log written next to data dir.
- **VCL-style branding:** installer shows the generated app icon (REQ-UX-08), clinic-neutral branding (owner's clinic identity is inside the product, not the installer — one build serves all clinics).
- **Signing slot:** `SignTool` parameters wired but empty by default (CONFLICT-D3); enabling signing = secret injection in Actions, zero script changes.

## Alternatives considered
- **WiX v5 (MSI):** enterprise-deployment idioms; authoring complexity + MSI patch semantics buy nothing for clinic installs; single-exe UX is explicitly friendlier here. Rejected (documented as future enterprise option).
- **NSIS:** capable but scripting ergonomics/defaults weaker than Inno for this wizard pattern; Inno's uninstaller/data-dir patterns are best-in-class. Rejected (preference, recorded).
- **MSIX:** conflicts with data-dir/print-driver assumptions and sideload ceremony. Rejected (consistent with ADR-015).
- **Latest Inno (6.5+/6.7):** commercial licensing required — unnecessary cost for this product; pin documented so the audit doesn't mistake "free license text" for current policy. Rejected for cost + stability.

## Consequences
- CI installs the built setup silently (`/VERYSILENT`), launches, runs artifact smoke tests, uninstalls, and asserts the data-preservation invariants — every release (see ADR-018 pipeline steps).
- Owner's product keys/signing remain parameters, not architecture.
