# ADR-015 — Frozen build & packaging: PyInstaller (onedir, windowed) with hardened spec

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-BUILD-01/02, REQ-PLAT-02, REQ-UX-08, REQ-ARCH-02

## Context
The shipped product must run on clean Windows machines with zero developer
setup. Deterministic builds, embedded icon/metadata, small-ish footprint, and
AV-friendliness all matter; GitHub Actions Windows runners are the build farm.

## Decision
- **PyInstaller 6.x onedir**, `windowed=True`, built with the pinned CPython 3.12 (ADR-001) in CI on `windows-latest` only — never shipped from a dev laptop.
- **Spec hardening:** explicit `hiddenimports` for SQLAlchemy dialects/argon2 bindings; `excludes` for PySide6 GUI fat (WebEngine absent by not installing Addons-WebEngineWidgets; QtNetwork/QtQml/QtTest etc. excluded); data bundling: fonts, clinical seed library JSON, i18n catalog, THIRD-PARTY-LICENSES, generated `buildinfo.json` (version, commit, CI run URL).
- **App metadata:** `version_info` + icon (REQ-UX-08 `.ico` 16→256) embedded; product name "Dentiva Pro", legal copyright "Shohan Khan"; manifest declares PerMonitorV2 DPI awareness (Qt does this when built windowed with the Windows manifest; asserted by CI PE-manifest inspection).
- **onedir over onefile:** onefile's self-extraction to temp worsens AV false positives, cold-start (budget REQ-PERF-01), and patchability; onedir installs under Program Files via installer — chosen.
- **Artifact hygiene (REQ-BUILD-02):** post-build audit script (ADR-018) enforces: no `tests/`, no `.py` sources beyond pyc-in-PYZ (we compile only; source not shipped as loose files), no `.env`/secrets, no sample data, presence of license dir + manifest; forbidden-strings scan includes activation literals (REQ-ACT-02).
- **Reproducibility discipline:** same inputs → same file inventory + stable hashes; timestamps in PE/zip normalized where controllable; documented tolerance list.

## Alternatives considered
- **Nuitka:** best binary fidelity, compiles to C — long CI times, higher AV-noise variance, and a heavier debugging story; kept as a *documented future option*, not 1.0 baseline. Rejected on build-pipeline risk vs benefit.
- **cx_Freeze:** viable, thinner ecosystem docs for Qt6 edge cases today. Rejected (PyInstaller's Qt hooks + hook database).
- **Embeddable Python + script launcher (no freeze):** simpler, but leaves a visible interpreter surface and weaker metadata/UX; not "real Windows product" grade. Rejected.
- **MSIX packaging:** store-oriented ceremony, sandbox filesystem fights our data-dir + local-printer assumptions. Rejected for direct-distribution (kept as post-1.0 possibility).

## Consequences
- Frozen-environment quirks (module graph, `--run` smoke) are CI-automated, and Phase 18 runs the *full test suite against the built tree* using the packaged interpreter (test harness attaches to artifact, sources excluded from artifact itself).
- Build time budget: ≤ 12 min release job build step; documented.
