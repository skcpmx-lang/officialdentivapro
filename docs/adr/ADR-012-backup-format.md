# ADR-012 — Backup format: `.dvpkg` ZIP container with manifest, hashes, and crash-safe restore journal

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-BKP-01..07, REQ-ATT-01, REQ-TXN-03/04, REQ-DATA-03

## Context
Backups must be self-contained (DB + managed attachments + configuration),
deterministically named, integrity-validated before use, safe under
interruption, and restorable onto an empty install — the clinic's only
disaster-recovery mechanism.

## Decision
- **Container:** `<name>.dvpkg` = ZIP (stored or deflate; **not** encrypted in 1.0 — documented) containing:
  - `manifest.json` — schema: version, product_version, schema_revision, created_utc, created_by, app-machine-id, counts snapshot, per-file `{path,size,sha256}`, engine options (`journal_mode`, `page_size`), `integrity: {algo:"sha256"}`; signed with an HMAC using an **archive key** derived from data-dir bootstrap secret (detects casual tampering; not a confidentiality claim — honest doc).
  - `database/dentiva.sqlite3` — snapshot from `sqlite3` **online backup API** (consistent copy while the app runs; never zip the live file mid-transaction), `pr wal_checkpoint(TRUNCATE)` beforehand to minimize WAL coupling; verified with `PRAGMA quick_check` post-copy.
  - `attachments/index.json` + `attachments/files/aa/bb/<hash>` — content-addressed set filtered to DB-referenced blobs (orphans skipped, reported).
  - `config/bootstrap.json` (relocatable subset), `THIRD-PARTY-NOTICES/` omitted (from app dir, not data).
- **Write protocol (REQ-BKP-05):** build into `dvpkg.tmp` in destination → hash-verify in place → `fsync` → atomic rename to final name (same volume). Interrupted builds leave only `.tmp` (garbage-collected next backup, audited).
- **Restore protocol:** (1) verify manifest hashes + zip integrity + schema_revision ≤ app's + `quick_check` on staged copy; (2) **automatic pre-restore safety package** (kind=`pre-restore`) first; (3) exclusive mode: UI frozen (modal progress), all services quiesced via CommitGate drain, backup worker owns the swap; (4) journal file `<data>/.restore-journal` records stage `staged|swapping|committed|failed` with paths; (5) swap = move current DB+attachments aside into `restore-quarantine/`, move staged package files in, `integrity_check`, counts-vs-manifest spot checks, flip journal `committed`; (6) any failure/unknown state at startup → auto-rollback from quarantine (or safety package) with explicit dialog; (7) activation record is *not* replaced if restoring into an activated install (REQ-ACT-05 policy: `meta.activation` merged-forward, documented in BACKUP §6); (8) post-restore: audit event + re-index FTS + notification "restore completed".
- **Multiple-file selection:** sequential restore with explicit last-wins confirmation listing each package's timestamp + counts (REQ-BKP-03 policy made deterministic).
- **Scheduling:** interval config (off/7/15/30 d) evaluated on startup + hourly tick; missed window ⇒ catch-up prompt/auto per setting; retention prunes oldest beyond N (pruned names audited); destination free-space pre-flight.

## Alternatives considered
- **Plain file copy of .sqlite3 ± wal:** unsafe while running; fails REQ-BKP-05. Rejected.
- **SQLite `.backup` only, no container:** loses attachments/config — the prompt demands self-containment. Rejected.
- **7z solid archives:** better ratio, external codec dependency in frozen app; clinic backups are GB-scale at most — ZIP is dependency-free (stdlib) and robustly repairable by common tools. Chosen for zero-dependency reliability over ratio.
- **VSS/shadow copies:** overkill for single-file DB with backup API. Rejected.
- **Encrypted containers (age/cryptography):** tempting, but "offline restore on fresh install" becomes key-management UX; the archive-key HMAC above is the honest middle. Post-1.0 option documented.

## Consequences
- Format spec doubles as the restore-compatibility contract (BACKUP.md); any change = new `format_version` handled by restore validator (older app refusing newer packages is correct behavior, with clear message).
- Restore into *empty install* explicitly tested (CI matrix) — including activation-record carry-over semantics.
- Backup size grows with attachment store; dedup via content-addressing already; docs give clinic guidance on destination choice.
