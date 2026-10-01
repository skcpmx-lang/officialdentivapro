# dist/ — release artifact staging

This directory is the **fallback location** for final distributable artifacts if
GitHub Release publication is unavailable (mandated by the product master
requirements, see `../docs/BUILD-RELEASE.md` §6).

Current state: **empty — no release has been built.**

- Phase 20 (final release build) is the only phase permitted to place
  production artifacts here (`DentivaPro-Setup-<version>.exe`,
  `SHA256SUMS.txt`, release manifest JSON).
- Any file that appears here before the Phase 19 audit gate passes is a
  process violation and must not be treated as a release.

Planned layout at release time:

```
dist/
  README.md                       # this file, updated with release state
  DentivaPro-Setup-<version>.exe  # Inno Setup installer (the product)
  SHA256SUMS.txt                  # checksums of all artifacts
  release-manifest.json           # version, commit, CI run, test summary, file hashes
```
