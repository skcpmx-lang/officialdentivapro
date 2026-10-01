# ADR-010 — Offline activation: derived-hash verification with honest threat documentation

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-ACT-01..05, CONFLICT-C1, REQ-BUILD-02

## Context
One-time offline activation with fixed code `1516591935015165`. It must not
appear as plaintext in source/binary, must be deterministic and testable, and
must never falsely re-lock an activated install. The prompt itself demands
documentation that local-only secrets are recoverable by determined attackers.

## Decision
- **Verification material:** the P2 implementation fixes the encoding: `inner = SHA256(b"dvp.legacy.2026:" + candidate.encode("utf-8") + b":dvp").digest()` and `verifier = SHA256(b"dvp.act.v1:" + inner + b"dentiva-pro:1.0").digest()`. The artifact contains only the resulting 32-byte verifier; `hmac.compare_digest` checks a candidate's identical derivation in constant time. Public test vectors use benign sample inputs; they are not the activation input.
- **No plaintext, no plaintext fragments:** the code string never appears in `src/`, resources, docs beyond this planning set (which stays private in the repo — acceptable; the *binary* is what ships) and — decisively — is absent from built-binary string scans (`TestActivationBinaryHygiene` in release CI: `strings`-style scan of the packaged tree for the literal and for a 3-char sliding-fragment set against the constant path).
- **State machine:** `ACT_REQUIRED → (code ok) → ACTIVATED` written as `activation_record(id=1, install_id=uuid4, ts, fingerprint_hash)` in one transaction with schema setup; app refuses clinical use until `ACTIVATED`. Fingerprint = SHA-256(machine-guid + data-dir-path-normalized) stored **for audit display only** — it never gates re-entry (prevents false locks on OS updates/hardware changes; the requirement explicitly warns against lockouts).
- **Reinstall/restore semantics:** activation state lives in the *data directory*, so reinstalling app files over existing data keeps the install activated; a restore carries its source install's activation with it (fresh restore into empty machine prompts activation with the same one-time code — deterministic, supported path).
- **Testability:** the derivation is a pure function; unit tests pin published vectors (input → digest); a dev-tool `scripts/activation_selftest.py` regenerates the constant so owners can rotate salts on rebuild without touching product code.
- **Threat honesty:** SECURITY §2 states plainly: this raises the bar against casual copying/plaintext leakage, not against a reverse engineer with a disassembler; no cryptographic non-repudiation is claimed; the product is licensed per-clinic by trust + invoice.

## Alternatives considered
- **Machine-bound derived keys / HW fingerprints as gate:** creates the exact false-lockout hazard the prompt forbids (Dell BIOS updates, reimaged PCs). Rejected as gate; kept as informational field.
- **Ed25519-signed offline license files (issuer-side signing):** stronger anti-forgery, but the fixed-code prompt wording specifies a single shared activation code, and issuing per-machine licenses needs an owner workflow the prompt doesn't include. Documented as a possible future licensing evolution; not 1.0.
- **Obfuscation services / encryption-of-the-checker:** theater against REs, adds AV false-positive risk on top of unsigned builds. Rejected.
- **Storing the plain constant in a resource:** trivially exposed; violates the stated mandate. Rejected.

## Consequences
- The salt strings are *not* secrets (they ship in the binary); they only prevent casual grep. Accepted and documented.
- Activation UX: single input field, paste-tolerant (digits-only strip, hyphen/spacing tolerant), clear error, no hints about the expected value; support path = owner communicates the code (already public within the product's distribution).
- Any future code change requires regenerating the constant via the selftest tool — one-line, deterministic, CI-guarded (build fails if constant and vectors diverge).
