# ADR-008 — Authentication & session security: Argon2id, stateless-in-DB sessions, step-up

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-AUTH-01..06, CONFLICT-C5, REQ-LOG-02

## Context
Real clinic PCs, shared desks, sensitive patient/financial data; fully offline
— no identity providers. Login must be strong against offline attack, fast
enough on old hardware, and auditable.

## Decision
- **Hashing:** `argon2-cffi` (Apache-2.0; ships Windows wheels + bundled `argon2_cffi_bindings`) — Argon2id, random 16-byte salt per password, PHC-encoded storage. Policy tiers per CONFLICT-C5 with a first-run calibration probe choosing the highest profile under ~350 ms; `check_needs_rehash` transparently upgrades on successful login. If argon2 import fails in a frozen environment (belt-and-braces CI check), an explicit build fails rather than falling back silently — no bcrypt downgrade path in 1.0; this is tested by artifact import smoke (Phase 18).
- **Verification:** `PasswordHasher.verify` (constant-time internally); mismatch and unknown-user paths return identical UI text/delay floor (anti-enumeration, REQ-AUTH-02). Progressive delay: 0 s, 3 s, 10 s, 30 s after consecutive failures per username+device; failures audited.
- **Session:** in-memory only (`Session` object owned by the composition root): principal id, granted permission set snapshot, login timestamp, last-activity timestamp updated by real input events. **No tokens/cookies/persistent session rows** — nothing to steal from disk; DB stores only `auth_event` audit rows.
- **Auto-lock:** idle watchdog (5/10/15/30 min setting) → modal lock overlay; app state stays resident; unlock re-verifies password (same pacing rules); wrong unlocks count toward escalation lockout (temporarily disables unlock attempts for increasing intervals). Unsaved drafts: held in memory, never written to disk by lock logic.
- **Step-up re-auth:** independent challenge (fresh password entry, 60 s validity) for: restore, reset, delete-hard ops, permission/user edits, export of financial reports. Implemented as a service-layer gate decorator (`@step_up`) so it cannot be bypassed by UI paths.
- **Startup integrity:** verify activation, schema, and audit hash chain before unlocking the shell (SECURITY §5).

## Alternatives considered
- **bcrypt/scrypt:** Argon2id is the current OWASP-first recommendation; bcrypt has 72-byte input quirks. Rejected.
- **PBKDF2-HMAC-SHA256 (stdlib):** zero-dependency fallback quality; weaker GPU resistance at equal latency. Documented as the *only* fallback if a future environment forbids argon2 — not shipped in 1.0 to keep the policy single-track.
- **OS credential prompts / Windows Hello:** couples the product to domain/hardware configs clinics may not have; offline reliability first. Rejected for 1.0 (documented future option).
- **Persistent "remember me" sessions on disk:** contradicts the lock-down posture; users re-login (≤ a few seconds). Rejected.

## Consequences
- argon2 native DLL must pass frozen-artifact smoke (Phase 18 checklist row).
- Time-based behavior is fully fake-clock testable (Clock injection).
- Clinic guidance doc: BitLocker + Windows lock screen recommended alongside (defense in depth for unencrypted-at-rest, ADR-003).
