# ADR-019 — Legal & license compliance: runtime allowlist, generated inventory, bundled texts

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-PLAT-04, REQ-BUILD-04, ADR-002/008/014/015/016/017

## Context
Commercial closed-source redistribution mandates a license audit of every
bundled component *before release* — runtime and build-time alike.

## Decision
- **Policy (runtime):** allow MIT, BSD-2/3, Apache-2.0, PSF, ISC, zlib/libpng,
  OFL (with no-RFN embedding checks), and **LGPL-3.0 only with the compliance
  posture below**. **Deny** GPL/AGPL/MPL-copyleft in anything shipped inside
  the frozen artifact (dev-only tools are fine and listed separately).
- **LGPL (Qt/PySide6) compliance posture:** dynamic Python imports of
  unmodified PySide6, license texts + "you may replace/relink" notice in
  `THIRD-PARTY-LICENSES/`, no static amalgamation of Qt into app code, no
  anti-modification lock (product is not tivoized). Documented in EULA
  appendix.
- **Generation:** `scripts/gen_license_inventory.py` reads the locked
  dependency graph → `THIRD-PARTY-NOTICES.json` (+ human `THIRD-PARTY-LICENSES/`
  directory incl. full texts, PySide6/Qt, SQLite (public domain), argon2 stack,
  fonts (OFL incl. per-font copyright lines), Inno Setup acknowledgement
  (build tool, not bundled in app payload but acknowledged in docs per its
  license), Python runtime notice (PSF)). CI policy job fails on: unknown
  license id, denied id, missing text, version drift.
- **Audit cadence:** regenerated in `quality.yml` every push (cheap) and
  verified in `release.yml` against the *artifact tree*; Phase 19 re-runs the
  audit as release gate (explicit master-prompt requirement).

## Alternatives considered
- **"Audit once manually":** drifts between phases; automated inventory is the
  only enforceable form of the requirement.
- **GPL alternative stack (PyQt):** would require open-sourcing the app or a
  paid license — both conflict with product mandates. Rejected (already ADR-002).
- **Skipping font OFL texts:** OFL requires bundled license/copyright notices
  when redistributing — automated here.

## Consequences
- Every future dependency addition = lockfile change = automatic re-audit in
  CI; no honor-system updates.
- EULA text (owner-facing, drafted Phase 2) embeds the third-party appendix.
- Honest documentation that *unselected* theoretical stack alternatives are
  irrelevant post-decision; only shipped components are audited.
