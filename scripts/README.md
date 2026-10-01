# Engineering scripts

- `dev_checks.py` runs lint, format, strict-core type checks, doc/catalog/lock/license
  drift gates, an artifact-tree dry run, and the complete pytest suite.
- `check_lock_policy.py` checks that each locked runtime and development package
  has a CPython 3.12 Windows x64 compatible wheel.
- `gen_license_inventory.py` builds `THIRD-PARTY-NOTICES.json` from the locked
  dependency graph and installed package metadata; runtime policy follows ADR-019.
- `audit_artifact.py` audits an explicit built tree. Phase 2 runs it against the
  source package as a dry run; this is not a packaged-artifact certification.
- `extract_i18n.py` deterministically checks the gettext template against literal
  `_()` and `translate()` calls in `src/dentiva`.
- `activation_selftest.py` reads activation input without echoing it or putting it
  in process arguments; it is an owner-side derivation check.

Every command exits non-zero on a failed check. `dev_checks.py --failure-probe`
uses a deliberately lint-broken temporary file and confirms Ruff returns a failure.
