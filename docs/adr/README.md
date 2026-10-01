# ADR Index — Dentiva Pro

Every technology, architecture, and process selection carries an ADR. "Rejected"
options are recorded so future maintainers never re-litigate silently. Decisions
binding implementation; conflicts/decisions log in `docs/CONFLICTS-DECISIONS.md`.

| ADR | Title | Status | Key requirements |
|---|---|---|---|
| ADR-001 | Engineering baseline (Python 3.12 pin, positioning) | Accepted | REQ-PROD-01, REQ-BUILD-01 |
| ADR-002 | Desktop UI: PySide6 (Qt 6) + custom design system | Accepted | REQ-UX-*, REQ-DPI-* |
| ADR-003 | Database: SQLite WAL hardened; SQLCipher seam deferred | Accepted | REQ-DB-*, REQ-TXN-* |
| ADR-004 | Data access: SQLAlchemy 2 + repositories/UoW + Alembic | Accepted | REQ-DB-01..03 |
| ADR-005 | Money: integer poisha + Decimal policy | Accepted | REQ-DATA-09, REQ-MONEY-* |
| ADR-006 | Layered monolith, composition root, conformance tests | Accepted | REQ-ARCH-01..04 |
| ADR-007 | Threading: GUI thread + bounded worker pool, single writer | Accepted | REQ-PERF-*, REQ-TXN-* |
| ADR-008 | AuthN: Argon2id, in-memory sessions, step-up | Accepted | REQ-AUTH-* |
| ADR-009 | RBAC permission codes + hash-chained audit | Accepted | REQ-RBAC-*, REQ-AUDIT-* |
| ADR-010 | Offline activation: derived-hash, honest limits | Accepted | REQ-ACT-* |
| ADR-011 | Printing: custom Qt layout engine, one model → preview/PDF/printer | Accepted | REQ-PRINT-* |
| ADR-012 | Backup `.dvpkg` container + journal-safe restore | Accepted | REQ-BKP-* |
| ADR-013 | Attachments: content-addressed store, sniffed validation | Accepted | REQ-ATT-* |
| ADR-014 | Fonts: Inter + Noto Bengali (OFL), coverage gates | Accepted | REQ-FONT-*, REQ-LOC-* |
| ADR-015 | PyInstaller onedir freeze + artifact audit | Accepted | REQ-BUILD-01/02 |
| ADR-016 | Inno Setup 6.4.3 installer, data-preserving uninstall | Accepted | REQ-BUILD-03 |
| ADR-017 | CI/CD: quality(Linux) + release(Windows) fail-loud | Accepted | REQ-BUILD-05..08 |
| ADR-018 | Design system & motion policy (freeze Phase 4) | Accepted | REQ-UX-* |
| ADR-019 | Legal/license inventory automation | Accepted | REQ-PLAT-04, REQ-BUILD-04 |
| ADR-020 | Dependency lock manager: pinned uv + cross-platform lock | Accepted | REQ-BUILD-01/04/05, REQ-GOV-03 |

Note: numbering follows content, not creation order; filenames carry the ADR number.
