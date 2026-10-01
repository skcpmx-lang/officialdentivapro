# ADR-005 — Money representation: integer poisha + Decimal policy

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-DATA-09, REQ-MONEY-01/02, REQ-BILL-03/08

## Context
"Financial calculations must be performed in a reliable manner using
decimal-safe monetary handling rather than binary floating-point" is an
absolute requirement: invoices, balances, reports, and accounting must never
drift.

## Decision
- **Storage:** `INTEGER` columns in **poisha** (1 BDT = 100 poisha). Exact, index-friendly, sortable, aggregate-safe in SQL (`SUM` of integers is exact). Negative poisha exist only for adjustment/reversal columns, never for invoice line amounts (CHECK constraints).
- **Logic:** Python `decimal.Decimal` (quantized to 2 dp, `ROUND_HALF_UP` explicit at every input boundary) via a `Money` value object (`Money.from_display`, `.poisha`, `.to_display`, formatting delegates to the currency presenter). Binary floats are banned in money code paths (custom ruff/import rule + type-level guard: `Money.__float__` raises).
- **Rounding policy:** round once at entry (unit×qty per line), sum rounded lines, apply discount basis-points (integer per-mille-mille) then round once to poisha; documented in ARCHITECTURE §11 and property-tested (hypothesis) for associativity identities and ledger conservation.
- **Percentages/ratios** stored as integer basis points (10_000 = 100%) — never floats.

## Alternatives considered
- **DECIMAL/NUMERIC affinity in SQLite:** SQLite's NUMERIC affinity converts to REAL for non-representable literals — silent float leakage. Rejected (classic trap).
- **`decimal` stored as TEXT:** exact but kills SQL aggregation and ordering performance at 50k-invoice scale. Rejected after poisha option.
- **float everywhere + rounding on display:** the precise failure mode the prompt forbids. Rejected.
- **Micro-units (1e-6 BDT):** unnecessary granularity; poisha matches printed precision (2 dp).

## Consequences
- Every money read/write goes through `Money`; new modules inherit safety.
- Reports aggregate in SQL exactly; display formatting centralized (REQ-MONEY-02, South-Asian grouping decision documented there).
- Post-restore/recovery checks can `SUM` ledger vs document totals for consistency audits (BACKUP §5).
