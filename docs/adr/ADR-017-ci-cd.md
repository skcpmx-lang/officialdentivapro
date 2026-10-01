# ADR-017 — CI/CD: two GitHub Actions workflows (quality on Linux, release on Windows) with fail-loud gates

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-BUILD-01..08, REQ-GOV-03, REQ-QA-01..04, CONFLICT-D1/D2

## Context
GitHub Actions is mandatory for production release building; the sandbox is
Linux (no Windows/printer hardware); the workflow must "fail rather than
silently producing a broken build"; releases to GitHub Releases or the
documented `dist/` fallback; merges stay manual (owner gate).

## Decision
**Two workflows, both versioned in-repo and branch-protected by their own
gates (branch protection is owner-side; we verify with a recorded settings
checklist, CONFLICT-D5-style honesty):**

1. `quality.yml` (PR + main push, `ubuntu-latest`, fast < 12 min):
   install pinned deps from lockfile → `ruff` (lint+format check) → `mypy`
   (strict on core packages) → architecture conformance tests → pytest unit +
   integration + **GUI offscreen** (`QT_QPA_PLATFORM=offscreen`, xvfb-free) →
   migration chain test → print-layout op-stream tests + PDF generation (Bengali
   assertions run *here* — Qt+HarfBuzz work identically headless) → license
   inventory policy check → artifact audit **dry-run** (rules against build
   tree from a Linux parity build where meaningful). Artifacts: test reports,
   coverage, log excerpts uploaded even on failure.
2. `release.yml` (version tag `v*` + manual dispatch, `windows-latest`):
   restore venv with same pins → **full test suite against dev tree** → PyInstaller
   build (ADR-015) → artifact audit + PE manifest/version-info/icon checks →
   Inno Setup compile (ADR-016) → **install setup silently → run smoke suite +
   print-to-PDF fidelity checks against the installed tree → uninstall → assert
   data preservation → reinstall-persist test** → generate `SHA256SUMS.txt` +
   `release-manifest.json` → publish GitHub Release (`gh` via `GITHUB_TOKEN`;
   `softprops/action-gh-release`-style step, pinned action SHAs) → **fallback
   job:** if release step fails on permissions/connector, upload artifacts to
   the workflow run AND commit them to `dist/` with updated `dist/README.md`
   status (REQ-BUILD-06, never ambiguous).
- **Fail-loud contract:** every job: `defaults: run: shell: bash`, `set -euo pipefail`, no `continue-on-error` anywhere, checksums verified after download steps (fonts, Inno setup binary pinned by digest from repo-submirror with pinned-URL + digest check), and a final `gate` job that *requires* all upstreams — the release only exists if the gate is green. A deliberate red-branch test (recorded in Phase 2 report) proves failure propagation.
- **Pinning:** action SHAs pinned; pip from hash-verified lock (`uv` or `pip-tools` — chosen in Phase 2, decision ADR-lite recorded there); tool versions pinned in `[tool.*]` sections.
- **Caching:** venv + PyInstaller cache keyed on lockfile hash; cache poisoning guarded (key includes tool version).

## Alternatives considered
- **Windows-only CI (single workflow everywhere):** slow feedback, costs, and offscreen Linux covers 95% of logic; rejected.
- **Linux cross-build of the Windows exe (wine+PyInstaller):** fragile; Windows-native runner is reliable and free-tier-compatible for release cadence. Rejected.
- **Buildkite/self-hosted:** no infrastructure budget allowed by offline product economics; Actions satisfies the mandate directly. Rejected.
- **Auto-merge/release on main push:** violates the owner's explicit merge gate; releases only from tags. Enforced by workflow design.

## Consequences
- "Tested on Windows" claims become `windows-CI-verified` with run URLs; the
  *physical-hardware* rows in Phase 18 remain owner-side and are labeled as
  such (REQ-GOV-07 honesty rule).
- Print *hardware* matrix can never fully close in CI — PDF-oracle equivalence
  plus owner-hardware spot checks is the documented honest ceiling (C4/D4).
- The dist/ fallback path is a *tested code path* (workflow contains it with a
  conditional), not an emergency invention.
