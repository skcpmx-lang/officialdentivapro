# Phase 02 — Engineering foundation

- Owner directive: `Continue`
- Branch/commit range: `arena/01a0f68b-officialdentivapro`, `5435836..f4c98b4` (foundation code, docs, and CI evidence)
- Objective (from ROADMAP §1): establish the repository skeleton, pinned dependency/tooling baseline, foundational logging/SQLite/migrations/core primitives, and green Linux + Windows CI on the non-product shell.

## Work completed

- Added a `src/dentiva` package tree and matching `tests/` tier layout, including per-module service/screen package directories. Added `TestArchitectureConformance` checks for the documented structure and initial dependency boundaries.
- Added `pyproject.toml`, CPython 3.12 support metadata, `.python-version`, `uv.lock`, and pinned Ruff, mypy, pytest/pytest-qt, Hypothesis, and runtime dependencies. ADR-020 records the `uv==0.12.21` choice. `tzdata==2026.4` is pinned so `ZoneInfo("Asia/Dhaka")` works on clean Windows installations.
- Added `scripts/dev_checks.py`; Ruff lint/format, strict mypy on the foundation core, exact traceability/i18n drift checks, locked Windows wheel policy, license inventory policy, artifact-tree dry run, and pytest are fail-closed checks. The workflow runs a deliberately broken F401 fixture and confirms Ruff returns a failure.
- Added stdlib structured errors, integer-poisha `Money`, an injectable Dhaka-aware `Clock`, Decimal length conversions, gettext fallback, and an AST-based `.pot` extractor. The small foundation shell externalizes its two visible strings.
- Added bounded rotating `app.log`/`errors.log` handlers, labelled-field redaction, exception-message suppression in normal logs, and an atomic diagnostic-bundle writer that stores error identity/version/frame locations only. No network calls are made by the bundle writer.
- Added the SQLAlchemy SQLite engine factory and ADR-003 pragmas, portable single-instance OS locking, startup/clean-shutdown marker, Alembic environment, and an intentionally empty `0001_foundation_baseline`.
- Added the pure activation derivation and non-secret test vectors. The expected input is read from the existing private planning document only during the source-hygiene test; the input is not embedded in `src/` or the activation test code.
- Added a clearly non-product Qt foundation shell. `--smoke` creates a `QApplication`/window, processes an event, closes the window, and exits without opening a clinic database.
- Added a lock-derived 34-package `THIRD-PARTY-NOTICES.json` inventory and runtime license policy gate. This is package/license metadata, not the human-readable license-text bundle required for an installer.
- Added validation-only GitHub Actions workflows. Both the Linux quality workflow and Windows foundation validation workflow passed on CPython 3.12. Neither produces or publishes a product/installer artifact.
- Updated ARCHITECTURE, BUILD-RELEASE, ROADMAP, SECURITY, TESTING, README, traceability generator/matrix, ADR index, and development setup notes. Corrected the Phase 1 report's stale “222 rows” typo to 254.

## Files/modules created or modified

- Foundation package: `src/dentiva/{app.py,__main__.py,bootstrap/,core/,data/,domain/,security/}`.
- Repository/package skeleton: `src/dentiva/{appstate,attachments,backup,printing,services,ui,resources}/` with the documented service and screen subpackages. Resource README files keep otherwise-empty folders present in Git; there are no fonts, icons, seed records, or license texts yet.
- Tests: `tests/{unit,integration,gui,security,architecture}/` (38 sandbox-run non-GUI tests; 39 tests in each CI run), plus reserved `printing`, `perf`, `chaos`, and `fixtures` directories.
- Tooling/config: `pyproject.toml`, `uv.lock`, `.python-version`, `.gitattributes`, `alembic.ini`, `.github/workflows/{quality,release}.yml`, `scripts/{dev_checks,check_lock_policy,gen_license_inventory,audit_artifact,extract_i18n,activation_selftest}.py`.
- Generated: `THIRD-PARTY-NOTICES.json`, `src/dentiva/resources/i18n/messages.pot`, `docs/TRACEABILITY.md` (generated only by `scripts/gen_traceability.py`).
- Installer directory is a README contract stub only; no `.iss`, EULA, or installer executable was created.

## Database changes

- Added a SQLite engine factory configuring WAL for file databases, `foreign_keys=ON`, `busy_timeout=5000`, `synchronous=FULL`, `temp_store=MEMORY`, and a bounded page cache.
- Added cross-platform instance-lock and abnormal-shutdown-marker primitives, with tests for SQLite pragmas, lock contention/reacquisition, and dirty/clean marker lifecycle.
- Added an empty Alembic foundation baseline. A clean upgrade creates only `alembic_version`; **no clinic/domain tables or seeds exist in Phase 2**.

## UI changes

- Added only `Dentiva Pro — Engineering Foundation`, a `QMainWindow` with one explanatory label used by `--smoke`.
- No navigation, clinic workflow, or enabled business controls were added. The Qt UI packages are structural directories only.

## Tests executed

| suite/check | runner | passed | failed | skipped | evidence |
|---|---|---:|---:|---:|---|
| Full pytest suite, including Qt offscreen shell smoke | GitHub Actions, Ubuntu, CPython 3.12 | 39 | 0 | 0 | [Quality run 36842890347](https://github.com/skcpmx-lang/officialdentivapro/actions/runs/36842890347) |
| Full pytest suite, including Qt offscreen shell smoke | GitHub Actions, Windows, CPython 3.12 | 39 | 0 | 0 | [Windows foundation run 36842890419](https://github.com/skcpmx-lang/officialdentivapro/actions/runs/36842890419) |
| Non-GUI unit/integration/security/architecture subset | Sandbox, CPython 3.11.2, pytest with Qt plugin autoload disabled | 38 | 0 | 0 | Executed locally on 2026-10-01; one `qt_api` config warning because the native Qt plugin could not load in this sandbox |
| Deliberately invalid Ruff F401 fixture | Sandbox + both CI workflows | 1 probe | 0 unexpected | 0 | `scripts/dev_checks.py --failure-probe` returned success only after Ruff produced a non-zero result |
| Alembic baseline, SQLite pragma/lock/shutdown, activation vectors, redaction/bundle, catalog, traceability, artifact-audit tests | Included in the 39-test Linux and Windows runs | pass | 0 | 0 | CI run links above |
| Traceability exact drift check | Sandbox + both CI workflows | 254/254 | 0 | 0 | `scripts/gen_traceability.py --check` |
| CPython 3.12 Windows x64 wheel policy | Sandbox + both CI workflows | 34 packages | 0 | 0 | `scripts/check_lock_policy.py` |
| Lock-derived license inventory/policy | Sandbox + both CI workflows | 34 packages | 0 | 0 | `scripts/gen_license_inventory.py --check` |

## Static checks

- `ruff check src tests scripts`: pass.
- `ruff format --check src tests scripts`: pass.
- `mypy`: pass; 21 foundation source files checked under strict mode.
- Coverage reported by both CI runs: **79.6% line coverage (359/451 lines), 63.2% branch coverage (43/68 branches)**. Phase 2 sets no feature-coverage threshold because the service/domain features are not implemented yet.
- Architecture boundary tests, source TODO/FIXME/placeholder sweep, `TestNoNetworkImports`, catalog drift, exact traceability drift, CPython 3.12 Windows wheel policy, 34-package license policy, and source-tree artifact dry run: pass.
- The audit ran in `--source-tree` dry-run mode; it is not a packaged-artifact audit.

## Perf & scale observations

N/A. Phase 2 establishes primitives and CI only; no clinic dataset or performance budget was measured.

## Issues found & fixed

1. Initial remote architecture checks exposed that empty `fonts/`, `icons/`, `seeds/`, and `notices/` folders are not represented in Git. Added explicit resource README files; both CI workflows then passed the repository-tree check.
2. Initial Windows lock test attempted to inspect the lock file while its exclusive byte lock was held and hit `PermissionError`. The test now reads no file contents while locked; the lock primitive also maps Windows access denial during acquisition to the typed contention error. Windows CI passes.
3. The P1 report said “222 rows” in its traceability delta despite the verified 254-row matrix. Corrected it to 254 and clarified the document-verified vs planned status distinction.
4. The sandbox does not include Qt's native Linux libraries and could not load `libGL.so.1`; an `apt` package installation was unavailable. No fake shared-library stubs were used. The GUI plugin and `--smoke` were verified by both pinned CPython 3.12 CI runners instead.

## Known issues & risks

- This remains a non-product foundation. There are no patient, clinical, billing, reporting, backup, printing, or authentication workflows; no domain schema beyond Alembic's version table; and no installer or release artifact.
- The local sandbox interpreter is CPython 3.11.2, while the committed lock targets CPython 3.12. Full lock sync, GUI smoke, and Windows compatibility claims therefore rely on the passing CPython 3.12 CI runs, not the sandbox.
- The committed inventory has package/license identities and policy results, but full license texts, Qt relinking instructions in an installer, EULA, and About-screen access remain later-phase work.
- `audit_artifact.py` ran against the source package in dry-run mode, not a frozen artifact. Production artifact manifest checks remain future work.
- Open owner decisions O1–O9 remain provisional and may be vetoed at a later gate. No owner default was closed by Phase 2.
- Branch-protection settings and owner-side merge controls were not independently inspected. The session branch is pushed; no PR was opened and no merge was attempted.

## Decisions made this phase

- **ADR-020:** selected pinned `uv==0.12.21` and committed `uv.lock`, with CPython 3.12 Windows x64 wheel checks and a generated license inventory.
- Added pinned `tzdata==2026.4` so `Asia/Dhaka` is available on clean Windows systems without relying on an OS IANA database.
- Kept the Phase 2 release workflow validation-only and explicitly non-product; artifact building/publication remain later gated work.

## Traceability delta

- `Verified` with executed CI evidence: REQ-GOV-01, REQ-GOV-03, REQ-GOV-04, REQ-GOV-06, REQ-GOV-07, and REQ-PLAT-03.
- `Implemented-Unverified` for partial foundations: logging (REQ-LOG-*), package/license audit (REQ-PLAT-04, REQ-BUILD-04), basic SQLite/migration/lock foundations (REQ-DB-02/03, REQ-TXN-03/04), error and architecture scaffolding (REQ-ERR-01, REQ-ARCH-01), activation source derivation (REQ-ACT-02), and selected money/date primitives (REQ-DATA-09, REQ-MONEY-01, REQ-DATE-01). Their remaining ACs are stated in the matrix statuses.
- Production packaging, installer/release publication, Bengali end-to-end rendering, and clinic workflows remain planned. The matrix was regenerated and its exact 254-row check passed.

## Verification-scope labels

- **sandbox-verified:** Ruff, format, mypy, 38 non-GUI tests, red-branch probe, traceability/catalog/wheel/license checks, and source-tree audit.
- **windows-CI-verified:** CPython 3.12 Windows foundation workflow, Qt offscreen shell smoke, full 39/39 pytest suite, wheel/license policy, and final required gate ([run 36842890419](https://github.com/skcpmx-lang/officialdentivapro/actions/runs/36842890419)).
- **sandbox-verified + windows-CI-verified:** Linux quality workflow and full 39/39 pytest suite ([run 36842890347](https://github.com/skcpmx-lang/officialdentivapro/actions/runs/36842890347)).
- **hardware-required(unavailable):** physical printers/thermal devices, clean-machine VM, and real-monitor DPI matrix are later-phase requirements and were not tested here.
- **owner-run(pending):** O1–O9 vetoes, branch-protection inspection, and all manual merge decisions remain with the product owner.

## Next phase

**Phase 3 — Data domain & core services** (ROADMAP §1): normalized SQLAlchemy models, first real schema migration, repositories/UoW, authorization/audit, backup/auth/settings services, and conformance/fault-injection tests. **Stop gate: Phase 2 is complete; awaiting the product owner's explicit `Continue` before starting Phase 3.**