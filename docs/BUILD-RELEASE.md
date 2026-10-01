# Dentiva Pro — Build, Installer & Release Process (v1.0, Phase 2 update)

Normative for REQ-BUILD-01..08, REQ-QA-03/04; decisions ADR-015/016/017/019,
CONFLICT-C3/D3/O3. This is the contract the Phase 2 CI foundation implements
and Phases 18/20 execute.

## 1. Versioning & build metadata

- Planned product version `MAJOR.MINOR.PATCH` (1.0.0 baseline); build id =
  `+<shortsha>` for dev, CI sets `+<shortsha>.<run_attempt>` on releases.
  The current package version `0.1.0` labels the non-product foundation only.
- Planned single source: `src/dentiva/__init__.py::__version__`; installer reads it via
  a precompile script (no duplicate constants); `buildinfo.json`
  `{version, commit, branch, ci_run_url, built_utc, python, pyside, schema_rev}`
  embedded in resources, shown in About (REQ-ABOUT-01) and every log header.
- Tags `v1.0.0` trigger `release.yml`; branch builds are snapshot-only (never
  tagged as releases).

## 2. Dependency & lock management

- `pyproject.toml` declares exact runtime and development pins; `uv.lock` is
  the single committed lockfile. **Phase 2 selected `uv==0.12.21`** (ADR-020)
  because its lock stores cross-platform wheel URLs and SHA-256 hashes while
  resolving one deterministic graph for Linux quality and Windows validation.
  CI runs `uv sync --locked`; dependency changes require a reviewed lock diff.
- `scripts/check_lock_policy.py` traverses the locked runtime + dev dependency
  graph and checks for CPython 3.12 / Windows x64 compatible wheels. It reads
  the lockfile rather than reaching out to PyPI at check time.
- Current runtime pins: PySide6-Essentials 6.11.2, SQLAlchemy 2.0.54,
  Alembic 1.20.0, argon2-cffi 25.1.0, and tzdata 2026.4 (for IANA zones on
  Windows). `requires-python` is `>=3.12,<3.13`;
  exact transitive releases and artifact hashes are in `uv.lock`.

## 3. Planned production build pipeline (not implemented in Phase 2)

The diagram below remains the Phase 18/20 release contract. The current
`release.yml` is deliberately validation-only: it installs the lock on
`windows-latest`, runs tests and the offscreen foundation-shell smoke, and
publishes no product, installer, or release assets. No Phase 2 green check is a
production-build or clean-machine claim.

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

## 4. Planned installer details (ADR-016 contract; no `.iss` in Phase 2)

64-bit, per-machine, Program Files, fixed AppId GUID, LZMA2, license page
(EULA `installer/license.txt` incl. third-party appendix pointer), custom
messages in plain English, icons from generated set (REQ-UX-08), uninstall
data-preserving default + explicit opt-in page for data deletion (unchecked;
requires typing `DELETE` on that page's confirmation — same rigor as REQ-DEL),
restart-manager integration for in-use files, upgrade in-place detection,
downgrade refusal message, optional VC-runtime (only if a dependency ever
needs it — CI verifies absence on clean VM).

## 5. Planned signing & SmartScreen guidance (not implemented in Phase 2)

- Default plan: unsigned (owner decision O3 / CONFLICT-D3). `SignTool`
  parameters and certificate-backed release signing are not wired yet; enabling
  requires owner-provided CI secrets.
- Clinic guidance is a release deliverable: SmartScreen "More info → Run", AV
  exception guidance for the onedir folder, and checksum verification steps
  (`certutil -hashfile … SHA256` vs published).

## 6. Planned release publication & `dist/` fallback (Phase 20)

No publication attempt occurs in Phase 2. The planned final release job attempts
GitHub Release on a tag (body: version, checksums, changelog pointer,
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
condition; Windows job remains the release oracle (D1 honesty). Developers
run `uv run --locked python -m dentiva` from the source tree — never promote the
foundation shell to a release artifact (`audit_artifact.py` rejects source-tree
patterns in actual packaged-tree mode).

## 10. Rollback & operations notes (final non-upgrade product)

No updater exists by design; "upgrade" = run new installer (in-place) —
pre-upgrade automatic backup prompt (reuses REQ-BKP machinery, flagged in
wizard when schema revisions differ); rollback = restore from pre-upgrade
package. Uninstall keeps data; reinstall restores. All paths covered by
Phase-18 checklist rows.
