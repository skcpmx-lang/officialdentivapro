# Dentiva Pro — Security & Privacy Model (v1.0, Phase 1)

Normative for REQ-ACT-*, REQ-AUTH-*, REQ-RBAC-*, REQ-AUDIT-*, REQ-LOG-02,
REQ-ATT-*, REQ-BKP-*; decisions ADR-008/009/010/013/003/014.

## 1. Principles

1. **The service layer is the only trust boundary.** The UI is untrusted input
   (including its own widgets: shortcuts, dialogs, restored state). Every read
   of sensitive data and every write goes through a permission-checked service.
2. **Deny by default.** Missing decorator = CI failure (ADR-009). Unknown
   permission codes fail closed (no grants, error logged).
3. **Fail safe, not open.** Integrity/verification failures degrade to
   read-only/guided-recovery modes; they never skip checks to "keep working".
4. **Least log.** Diagnostic data is redacted; secrets never in transit to
   disk (REQ-LOG-02).
5. **Honesty about limits.** This document names residual risks explicitly.
   Security is defense-in-depth for a single-station, physical-access-threat
   environment (clinic PC theft/shoulder-surfing/misconfigured sharing) — not
   a fortress against a privileged local attacker with the binary.

## 2. Activation — mechanism and admitted ceiling

- Product activation gate: one-time code `1516591935015165` (REQ-ACT-01).
- Verification: the P2 pure derivation uses UTF-8 input bytes and the exact
  ADR-010 composition `inner = SHA256(b"dvp.legacy.2026:" + input + b":dvp")`,
  `verifier = SHA256(b"dvp.act.v1:" + inner_digest + b"dentiva-pro:1.0")`;
  `hmac.compare_digest` compares the result to a 32-byte compiled digest.
  `hashlib`/`hmac` are stdlib; no network or external service is used.
- Phase 2 publishes benign derivation vectors (not the activation input):
  `Dentiva-vector-1` → `43440802d7f333d3fef5fa78e443cd45fd86a4307ed35e14ad1ec77ae8ec6225`;
  `Dentiva-vector-2` → `dc5c7fa500cb5b11e5b09d9aabca4673ce3083750987be3b28b6ec3c948fa117`.
  The executable checks format and vectors without any UI or activation
  lifecycle implementation; those remain Phase 5 work.
- State: `meta.activation` is a future product record, written in the same
  transaction as first-run setup completion (REQ-SETUP-04 atomicity); startup
  re-verifies presence/format, never re-derives from volatile hardware;
  fingerprint is audit-only and never gates (prevents false lockouts, REQ-ACT-04).
- **Admitted limitation (REQ-ACT-03, verbatim spirit of the master prompt):**
  a fully offline, single fixed activation code cannot be made cryptographically
  unrecoverable. A determined attacker with the binary can locate the constant
  and the comparison routine and bypass or extract. Our goal, and what is
  achieved: no casual exposure (no plaintext in source, resources, or
  `strings`-level inspection of the artifact; no fragment-based recovery),
  deterministic UX, and truthful documentation. Marketing must not call this
  "licensing security"; it is an activation formality.
- Phase 2 tests: `tests/unit/test_activation_vectors.py` pins non-secret
  derivation vectors and checks source-tree absence of the documented input.
  Binary-string/fragments scan (REQ-ACT-02) and 30× activation-lifecycle
  restart regression remain Phase 15/5 release work. `scripts/activation_selftest.py`
  reads owner input without echoing it or placing it in process arguments.

## 3. Authentication (REQ-AUTH-01/02, ADR-008)

- Argon2id PHC storage; per-password 16-byte CSPRNG salt (OS entropy);
  calibrated work factor (CONFLICT-C5); `check_needs_rehash` on login; params
  recorded in the hash string (verifier-agnostic future proof).
- Admin policy: ≥12 chars + deny-list; staff ≥8; composition warnings only
  (length+entropy is the enforced axis). Password strength meter never stored.
- Anti-enumeration: uniform "invalid username or password"; pacing delays
  0/3/10/30 s on consecutive failures per username; `locked_until_ms` in DB is
  *delay* based (no silent permanent lockouts — support via owner's admin can
  reset any account; admin self-lockout guard: last active Owner cannot be
  disabled/locked by self — REQ-SET-06).
- First-run: wizard creates Owner account (REQ-SETUP-03); no default
  credentials anywhere (no backdoor, ever).

## 4. Sessions & lock (REQ-AUTH-03/05, ADR-008)

- In-memory session; nothing persisted; process death = implicit logout.
- Idle watchdog on real input events; 5/10/15/30 min policy; lock modal
  preserves view state, drafts in RAM only; step-up challenges for sensitive
  ops with 60 s window; all transitions → `sessions_audit`.
- Clipboard: financial report copies require `finance.view`; clipboard content
  from masked fields never contains masked-out originals (masking happens in
  service responses, not view formatting).
- Multi-account switching = lock → login flow (no concurrent sessions in one
  process, by design and stated in About/help).

## 5. Authorization & enforcement (REQ-RBAC-*, ADR-009)

- Permission codes + role templates + per-user grants (§DATABASE.md §9).
- `@requires(...)` decorator resolves principal from ambient session context;
  raises `PermissionDeniedError` → error boundary shows access-denied +
  `authz.denied` audit row (attempt is evidence).
- Read-path rule: services raise before querying rows the caller cannot see
  (no fetch-then-filter) — verified with spy tests (REQ-BILL-10, REQ-SEARCH-01,
  REQ-DASH-02). Row-scoped rules (own drafts) inside predicates.
- Grants version counter: session caches it; every UoW start revalidates —
  mid-session revocations bite at the next operation (REQ-RBAC-06).
- Bypass tests (Phase 15): direct service calls under a clerk principal across
  the entire public service inventory (auto-enumerated), hotkey paths,
  deep-link routes, "show me anyway" dialogs, DB file opened through the app's
  own dev-console (there is none — absence asserted), and export writers.

## 6. Audit integrity (REQ-AUDIT-*)

- Hash chain `hash = SHA256(prev || canonical_json(entry_without_hashes))`;
  genesis = product tag; chain verified at startup + viewer open; broken chain
  → banner + severity notification + read-only mode option until acknowledged
  with re-auth (documented recovery: restore from last-good backup).
- Engine-level triggers reject `UPDATE/DELETE` on `audit_log`; no repository
  methods exist for mutation (absence is API surface, tested).
- Redaction: detail JSON pass-through `redact()` (drops password fields,
  activation material, clinical note bodies beyond key ids) — single choke
  point with unit corpus (REQ-AUDIT-01, REQ-LOG-02).
- Honest ceiling: chain detects casual/manual tampering by app users; it is
  not a CA-signed archive. Documented.

## 7. File & content attack surface (REQ-ATT-*, ADR-013)

- Attachments: whitelist ∧ magic-sniff ∧ size-cap; content-addressed storage;
  never parsed in-process beyond Qt image decode (guarded try) and PDF first
  page via QtPdf (guarded); open = shell association on a temp copy;
  executable extensions rejected by construction.
- Path handling: only store-relative composition (`os.path.join(root,
  validated_hex2, validated_hex2, validated_hex64 + ext`); restore validates
  every `.dvpkg` member name against `^[A-Za-z0-9._/-]+$` and root-anchored
  extraction (zip-slip rejected by unit test).
- Installer/EULA: bundled notices; no macros/active content.
- Config bootstrap & settings values are JSON-schema-checked at load —
  malformed files fail to a repair prompt, never "defaults + continue" for
  security-relevant keys (auto-lock min, allow_hard_delete default-off).

## 8. Data protection posture & residual risks (explicit)

| Risk | Posture | Residual |
|---|---|---|
| Physical theft of clinic PC | Data under per-user `%LOCALAPPDATA%`; app session lock; passwords Argon2id | **DB contents readable by a local admin with the machine.** Mitigations shipped: guidance (BitLocker, Windows hello, standard-user accounts) in setup tips; **SQLCipher+DPAPI profile is the documented 1.0.1 path (ADR-003 seam)** |
| Backup copies unencrypted | `.dvpkg` integrity-signed not encrypted (ADR-012); docs advise password-protected archive/encrypted drives at destination choice | Same local-media threat; stated plainly in Backup settings help |
| Multi-station file sharing corruption | Refused by design (lockfile + CONFLICT-C2); restore = migration | None (feature absence is the protection) |
| Malicious attachments | ADR-013 pipeline | Zero-day in an OS viewer opening a whitelisted file type (out of product control; open is user-intent) |
| Reverse-engineered activation bypass | §2 | Accepted, documented, not claimed otherwise |
| Clinical privacy | No telemetry/network at runtime (REQ-PLAT-03 static scan); logs redacted; audit stores metadata-first | Clinic staff misuse is an operational-control (RBAC+audit) matter, enforced per §5 |

## 9. Input hardening beyond §7 (REQ-VAL-*)

Parameterized SQL everywhere (no string SQL with user data — lint rule +
audit); SQLAlchemy Core only; LIKE queries escape `%/_` with explicit ESCAPE;
Bengali/unicode NFC at intake; length-capped TEXT; identifier fields
casefold-collated; numeric parsing strict (`Decimal` constructor, no
`float()`); date bounds sane; money parser ADR-005; filename sanitizers
display-only.

## 10. Privacy of patient data in support workflows

Crash bundles (REQ-LOG-03) contain stack + ids, never record bodies. Any
future support export must remain an explicit, user-initiated, redacted
artifact; 1.0 ships no automatic export of any kind.

## 11. Phase mapping

AuthN/RBAC shell enforcement: Phases 3 (tests) & 5 (E2E) · audit chain:
Phase 3/12 · activation: Phase 5 · attachment pipeline: Phase 6 · backup
security: Phase 12 · bypass campaign: Phase 15 · log hygiene: continuous
from Phase 2 (CI scan) · clean-machine: Phase 18.
