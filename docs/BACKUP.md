# Dentiva Pro — Backup & Restore Specification (v1.0, Phase 1)

Normative companion to ADR-012 implementing REQ-BKP-01..07, REQ-FILE-01,
REQ-TXN-03, REQ-ATT-01/04, REQ-ACT-05. Implementation Phase 12; format frozen
now because other subsystems (attachments, settings) must conform to it from
their first line of code.

## 1. Container `.dvpkg`

ZIP (deflate level 6; stored entries allowed), single file. Members:

```
manifest.json
database/dentiva.sqlite3
attachments/index.json
attachments/files/<xx>/<yy>/<sha256><ext>     (only blobs referenced by DB)
config/bootstrap.json
config/settings-export.json                   (full settings table, JSON)
meta/notes.txt                                (human one-liner: clinic, counts)
```

## 2. `manifest.json` (schema `dvp.manifest/1`)

```json
{
  "format_version": 1,
  "product": {"name":"Dentiva Pro","version":"1.0.0","build":"<commit>","ci_run":"<url-or-local>"},
  "created_utc": "2026-10-01T09:12:44Z",
  "created_local_dhaka": "2026-10-01 15:12:44 (+06)",
  "kind": "manual | auto | pre-restore",
  "machine_id": "<install uuid>",
  "data_root_hash": "<sha256(normalized data_dir) — informational>",
  "schema": {"user_version": N, "revision": "0017", "compatible_min": "0015"},
  "db": {"page_size": 4096, "journal_mode": "wal", "integrity": "ok-quick_check"},
  "counts": {"patients": 1234, "visits": 3456, "invoices": 890, "payments_poisha_total": "...", "attachments": 2100},
  "files": [{"path":"database/dentiva.sqlite3","size":20971520,"sha256":"..."}],
  "integrity": {"algo":"hmac-sha256-v1","key_scope":"archive-key","digest":"..."}
}
```

`archive-key` = HMAC key material stored in the *source* data dir
(`.dvp-archive-key`, 32 bytes) — travels conceptually with the clinic, allows
verification of their own packages on any machine; it is **not** secret
against the same machine's owner (SECURITY §8 honesty) and confers no
confidentiality. Foreign-package verification without the key degrades to
per-file hash + `quick_check` validation (allowed, banner shows
"unverified-origin package" — restore continues only with explicit re-auth).

## 3. Naming & destination

`DentivaPro-Backup-YYYYMMDD-HHMMSSZ-<kind>.dvpkg` (UTC, collision-safe with
`-2` suffix) in the configured destination (validated: exists, writable, free
space ≥ 2× last DB size + margin, not inside quarantine/temp). Destination
may be any local or removable NTFS/ReFS volume; network paths permitted as
plain file targets (the app never *runs* on network, only deposits backups) —
documented in Settings help.

## 4. Creation protocol (atomic, REQ-BKP-05)

1. Acquire backup worker + `CommitGate.drain(timeout)` (no new transactions;
   in-flight complete; UI modal progress but responsive).
2. `PRAGMA wal_checkpoint(TRUNCATE)` (best-effort, re-verified after).
3. Snapshot DB via sqlite3 **online backup API** into `staging/<tmp>.sqlite3`;
   `PRAGMA integrity_check` on the copy.
4. Build attachment index + copy referenced blobs (hash spot-verify sample,
   full verify configurable) into staging.
5. Emit manifest (with `files[]` hashes computed over staged bytes); zip staging
   → `<dest>/.<name>.tmp` on the destination volume (same-volume rename);
   reopen zip, verify every member hash + manifest HMAC + JSON parse;
   `FlushFileBuffers`/fsync; atomic rename to final; `backup_history` row +
   audit `backup.completed` (or failed).
6. Interruption at any step leaves only dotfile temp; next backup sweeps
   stale temps (>24 h, audited).
Failure mode: any exception → cleanup + `backup.failed` notification (danger)
+ audit; the live DB is never touched after step 1's drain releases.

## 5. Validation tooling

`scripts/dvpkg_validate.py` (ships in repo; referenced by support docs):
zip structural → member whitelist → path-safety regex (no `..`, no absolute —
zip-slip tests) → hash all → manifest schema (jsonschema-lite validator in
`backup/format.py`) → DB `integrity_check` + counts vs `manifest.counts`
(tolerance: counts may drift *only* for post-backup rows — exact compare on
restore). Used by CI matrix and exposed in the app's "Check a backup file"
utility (read-only) — REQ-BKP-03 pre-restore validation uses the same code.

## 6. Restore protocol (journal-safe, REQ-BKP-03/04, REQ-TXN-03)

Stages (journal `<data>/.restore-journal` JSON: `{stage, package, staged_dir,
quarantine_dir, ts, actor}`):

```
verify-package (full, §5)            ── any fail: abort, nothing changed
require-auth (step-up + ack dialog incl. counts diff)
pre-restore safety backup (kind=pre-restore) ── mandatory; if it fails → abort
stage: unpack package → staged/ (+ integrity + counts compare)
drain & quiesce (CommitGate closed; workers idle; UI modal)
swap: move live db+attachments → quarantine/ (rename ops only; no deletes yet)
      move staged db+attachments+config → live; write meta origin markers
verify-live: integrity_check + settings load + counts spot + FTS reindex
commit journal → cleanup quarantine after next successful app start
fail/unknown at swap window → auto-rollback from quarantine (or safety pkg) → audit restore.failed → guided retry UI
```

- **Activation policy (REQ-ACT-05):** restored `meta.activation` from an
  *activated* source keeps the install activated (activation travels with
  data). If the source was not activated (dev/legacy package) the live install
  re-prompts once — never loops.
- **Multiple-file selection (REQ-BKP-03):** presented sorted by `created_utc`,
  explicit warning + last-wins ordering confirmation; implemented as sequential
  restores (each fully validated + journaled), not a merged database (merging
  two backups is a distinct, unrequested feature — documented).
- **Restore into empty install:** fresh bootstrap dir + restore = full state
  return (activation included per above); CI matrix case.
- **Interrupted restore:** startup journal reader: `staged` → discard +
  normal boot; `swapping` → rollback path auto-runs with progress dialog;
  `committed-with-cleanup-pending` → complete cleanup silently, audit.
- Post-restore: notification + audit `restore.completed{package, sha256}`;
  login required again (session invalidation).

## 7. Scheduling & retention (REQ-BKP-02/07)

Scheduler = settings interval (off/7/15/30 d): evaluated on startup and
hourly Qt timer using `Clock`; `next_due = last_success + interval`;
startup catch-up if overdue ≥ 1 interval → auto (config) or prompt;
backup worker serializes with itself; retention N (default 12) prunes oldest
auto-kind files (manual never auto-pruned) — pruning = delete after
re-hash, audited names (REQ-DEL-02 philosophy for backups themselves: they
are user data; the clinic chooses retention).
Status UI: Settings→Backup page: last success/failure, next due, destination,
"Back up now", "Validate a backup file", "Restore from backup…".
Notification rules `backup_due` (warning, 3-day lead) / `backup_failed`
(danger).

## 8. Backup contents completeness table (self-containment contract)

| Data | Included | Mechanism |
|---|---|---|
| All relational state (patients…audit) | ✅ | DB snapshot |
| Attachments (files) | ✅ referenced | index+store copy (ADR-013) |
| Settings incl. print profiles | ✅ | `config/settings-export.json` + DB |
| Clinic identity files (logo) | ✅ | via files/attachments (logo row references sha256) |
| Activation record | ✅ (in meta table) | travels; policy §6 |
| Logs | ❌ by design | diagnostic only; path listed in `meta/notes.txt` |
| Quarantine/temp/staging | ❌ | runtime scratch only |
| The installer itself | ❌ | re-download; version pinned in manifest for provenance |

A CI test (`TestBackupCompleteness`, Phase 12) builds a data dir exercising
every table, backs up, restores into a *fresh* temp dir with a *fresh*
bootstrap, and diffs the DB semantic dump + file store listing — anything the
product stores but the container drops fails the gate.

## 9. User-facing promises (exact strings live in i18n catalog)

Plain-language: what's included, where files go, what restore destroys, that
backups are not encrypted (advisory), naming, and a "test your restores"
recommendation. No fear-marketing, no silence.
