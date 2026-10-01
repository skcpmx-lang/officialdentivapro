# ADR-013 — Attachments: content-addressed managed store with sniffed validation

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-ATT-01..04, REQ-VAL-03, REQ-SEC-02, REQ-BKP-05

## Context
Clinics attach prior prescriptions, scans, reports, images. Fragile absolute
paths break on move/backup; unvalidated files are a security and reliability
risk; the prompt demands managed storage, metadata, duplicate handling, and
open-in-viewer support.

## Decision
- **Store:** `<data>/attachments/<xx>/<yy>/<sha256hex><.ext>` (2-level fanout; extension from *validated* sniffed type, never from user filename). DB keeps hash, original filename, size, mime, uploader, timestamps, link rows (patient, expense, visit…).
- **Intake pipeline (synchronous hash + sniff, async copy):** size cap (default 25 MB, configurable) → stream SHA-256 → magic-byte sniff (PNG/JPEG/GIF/BMP/WebP/PDF/OOXML containers/TXT) → whitelist ∧ sniff must agree or reject with named reason → dedupe: existing hash ⇒ reference-only insert (`TestAttachmentDedup`) → store temp → fsync → atomic rename.
- **Original filename:** sanitized for storage listing only (keep unicode incl. Bengali; strip control chars/path separators); display column, never a path component — no path traversal surface by construction.
- **Opening:** materialize a copy with original filename+extension into per-session temp (`<data>/temp/opens/`, cleaned on open cycle), launch via `os.startfile` (Windows shell association). No in-process parsers of untrusted formats (no image re-encode except thumbnailing via Qt for images at intake — thumbnail cached in DB as PNG blob ≤ 160 px for gallery UX; PDFs get a first-page raster thumbnail via Qt PDF engine in Phase 11 window; if unavailable, icon-only — never a crash).
- **Integrity:** periodic + on-restore verification that each referenced blob exists with matching hash; missing ⇒ red state on attachment with "file missing — attempt restore" guidance (never silent).
- **Deletion:** soft-remove rows; files pruned only by explicit maintenance action (post-verified-backup) with re-auth — matches REQ-DEL-02 philosophy.

## Alternatives considered
- **BLOBs in SQLite:** simpler transactions, but bloats the transactional store, slows backups, complicates streaming/verify, and drags multi-GB attachments into every consistency check. Rejected after weighing transactional purity (mitigated by hash-verify + same-transaction metadata rows).
- **Copy into date folders with original names:** path fragility + traversal/collision risk — exactly the fragility the prompt forbids. Rejected.
- **Windows-only external viewers / ActiveX:** no. Rejected.
- **Antivirus scanning engines:** no paid/offline-viable scanner embeds cleanly; policy = strict whitelist + sniff + execute-nothing. Honest residual risk documented (SECURITY §7).

## Consequences
- Attachment availability after restore is an invariant with tests (Phase 12).
- 50k-attachment stress: index-only listings, thumbnails lazy (REQ-PERF-03).
- Temp copies are predictable and cleaned; malware spread limited by
  extension whitelist and "open = user intent" (documented in SECURITY §7).
