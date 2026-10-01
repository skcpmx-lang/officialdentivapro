# Dentiva Pro — Build, Installer & Release Process (v1.0, Phase 1)

Normative for REQ-BUILD-01..08, REQ-QA-03/04; decisions ADR-015/016/017/019,
CONFLICT-C3/D3/O3. This is the contract the Phase 2 CI foundation implements
and Phases 18/20 execute.

## 1. Versioning & build metadata

- Product version `MAJOR.MINOR.PATCH` (1.0.0 baseline); build id =
  `+<shortsha>` for dev, CI sets `+<shortsha>.<run_attempt>` on releases.
- Single source: `src/dentiva/__init__.py::__version__`; installer reads it via
  a precompile script (no duplicate constants); `buildinfo.json`
  `{version, commit, branch, ci_run_url, built_utc, python, pyside, schema_rev}`
  embedded in resources, shown in About (REQ-ABOUT-01) and every log header.
- Tags `v1.0.0` trigger `release.yml`; branch builds are snapshot-only (never
  tagged as releases).

## 2. Dependency & lock management

- `pyproject.toml` declares runtime extras (`[project.dependencies]`) + dev
  group; `uv lock` (or pip-tools) pins exact versions + hashes; CI installs
  from lock only; renovate-style bumps = PRs through quality gates.
- Wheel policy: every pinned runtime dep must publish `win_amd64` wheels for
  the pinned CPython (CI check `scripts/check_wheels.py` hits PyPI metadata) —
  protects the frozen build from source-build-only surprises on Windows.

## 3. Build pipeline (release, `windows-latest`)

```
checkout@pin → setup-python (pinned 3.12.x) → venv from lock (cache on hash)
→ full pytest (dev tree) → pyinstaller build (onedir)
→ scripts/audit_artifact.py:
    · forbidden: tests/, *.env, sample secrets, activation literals, __pycache__, .py loose sources, docs sources
    · required: THIRD-PARTY-LICENSES/*, resources fonts+seeds+notices, buildinfo, icon+version_info (pefile inspect), DPI manifest (PerMonitorV2)
→ installer compile (Inno 6.4.3 pinned by digest; ISCC path from tool cache)
→ silent install → artifact-suite (tests against installed tree) →
   Print-to-PDF golden subset → uninstall → data-preservation assert →
   reinstall-persist assert
→ artifacts: DentivaPro-Setup-1.0.0.exe + SHA256SUMS.txt + release-manifest.json
→ publish (GitHub Release via GITHUB_TOKEN) OR fallback:
   workflow upload + commit into dist/ + dist/README update (REQ-BUILD-06)
```
Every step `set -euo pipefail`, pinned action SHAs, no continue-on-error;
final `gate` job needs all upstreams (ADR-017 fail-loud proof from Phase 2).

## 4. Installer details (ADR-016 contract, `installer/DentivaPro.iss`)

64-bit, per-machine, Program Files, fixed AppId GUID, LZMA2, license page
(EULA `installer/license.txt` incl. third-party appendix pointer), custom
messages in plain English, icons from generated set (REQ-UX-08), uninstall
data-preserving default + explicit opt-in page for data deletion (unchecked;
requires typing `DELETE` on that page's confirmation — same rigor as REQ-DEL),
restart-manager integration for in-use files, upgrade in-place detection,
downgrade refusal message, optional VC-runtime (only if a dependency ever
needs it — CI verifies absence on clean VM).

## 5. Signing & SmartScreen

- Default: unsigned (owner decision O3 / CONFLICT-D3). `SignTool` params wired
  (cert via CI secrets) — enabling = secrets only.
- Clinic guidance page (docs/support): SmartScreen "More info → Run", AV
  exception guidance for onedir folder, checksum verification steps
  (`certutil -hashfile … SHA256` vs published). Documented, honest, no blame UX.

## 6. Release publication & `dist/` fallback

Attempt GitHub Release (tag, body: version, checksums, changelog pointer,
known-limitations section copied from traceability). If `gh`/Actions
permissions fail: `release.yml` fallback job downloads artifacts and commits
to `dist/` with updated status block in `dist/README.md` (present + verifiable
+ checksummed per master requirement). The *chosen path* is reported in the
Phase 20 report with evidence either way (run URL or dist commit hash).

## 7. Post-build verification (Phase 20 exact-artifact rule)

The suite run in §3 *is* the verification (same bytes installed); additionally:
`release-manifest.json` schema-check, checksum recompute from final artifact
cache, and a final human pass on the installed copy (activation/setup/one-day
sim) recorded in `docs/reports/phase-20-release-build.md`. No rebuilds after
the green gate — the published file hash must equal the tested file hash
(asserted by manifest `setup_sha256` vs release asset digest).

## 8. Reproducibility discipline

Inputs pinned (interpreter, lock, Inno digest, font checksums); PyInstaller
build path randomized per CI (path-reproducible hooks); timestamp normalization
in zip/PYZ where controllable; documented residual variance list (PE timestamp).
"Reproducible" is claimed only for the enumerated normalization scope.

## 9. Development vs release parity

`quality.yml` runs the identical pytest suite (minus Windows-only dirs marked
`windows-only`) on Linux offscreen — a Linux-green tree is a *necessary*
condition; Windows job remains the release oracle (D1 honesty). Dev machines
run `scripts/dev_app.py` (source tree, console logging) — never promoted to
release artifacts (audit_artifact forbids source-tree patterns).

## 10. Rollback & operations notes (final non-upgrade product)

No updater exists by design; "upgrade" = run new installer (in-place) —
pre-upgrade automatic backup prompt (reuses REQ-BKP machinery, flagged in
wizard when schema revisions differ); rollback = restore from pre-upgrade
package. Uninstall keeps data; reinstall restores. All paths covered by
Phase-18 checklist rows.
