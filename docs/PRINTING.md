# Dentiva Pro — Printing Subsystem (v1.0, Phase 1)

Normative companion to ADR-011 implementing REQ-PRINT-*, REQ-RX-05, REQ-BILL-09,
REQ-LOC-01, REQ-FONT-*, REQ-DATA-05. Full engine build is Phase 11; this spec is
its acceptance contract.

## 1. Pipeline (single renderer guarantee — REQ-PRINT-02)

```
document snapshot (DB, frozen) → DocumentModel (typed blocks)
 → LayoutEngine(width-class rules, mm-space) → PagePlan[] (positioned DrawOps)
 → sinks: ① QPdfWriter(PDF)  ② QPrinter(physical)  ③ QImage raster (preview)
```
All three consume the identical `PagePlan`; equivalence is structural, verified
by raster-diff goldens in CI (Linux, offscreen) and Print-to-PDF parity on
Windows CI. Money strings arrive pre-formatted from core (no float).

## 2. Document model

Blocks (dataclasses, `printing/model.py`): `ClinicHeader{logo, name, address[],
phone[]}`, `DentistBlock{name, designations[], certifications[]}`,
`PatientLine{name, gender, age, date, code}`, `Section{title, lines[]}` (C/C,
O/E, R/E+advice), `MedTable{columns[], rows[]}` (rx), `ChargeTable{rows,
totals, status}` (invoice), `NoteBlock{clinic_message, availability}`,
`SignatureBlock{reserved_height_mm}`, `PageMeta{no, of, doc_no, copy_kind}`,
`Watermark{text}` (draft). Each document type has a **builder** that reads
*only* the stored snapshot (REQ-DATA-05); builders are pure functions —
golden-JSON tested against fixtures.

## 3. Layout & pagination rules

- **Units:** mm floats for geometry; snapping to 0.2 mm grid; fonts in pt with
  line-height multipliers from the doc theme.
- **Width classes:** `A-series` (A4/A5: two-column patient line, full tables),
  `Receipt80` (single column, compressed clinic header, totals right-aligned,
  logo optional auto-threshold 1-bit), `Receipt58` (same minus logo by default;
  min font band 7.5 pt). Custom widths resolve class by thresholds (≥140 A4-ish,
  ≥100 A5-ish, ≥70 Receipt80, else Receipt58).
- **Font bands:** body 9.5–11 pt (receipts 7.5–9), headings 13–16; the engine
  shrinks *before* it breaks tables and never crosses min band (overflow →
  new page, REQ-PRINT-03/04).
- **Tables:** header repeats every page; column weights adaptive; numeric
  columns right-aligned tabular figures (Inter tnum); row orphan rules
  (min 2 rows per page tail); Bengali text wraps at cluster boundaries (Qt
  line-breaking respects shaping — validated in goldens).
- **Signature zone (REQ-PRINT-07):** `SignatureBlock` reserves
  `min(28 mm, remaining)` height at lower right (receipts: full-width band,
  18 mm); layout asserts `content_rect ∩ signature_rect = ∅` per page —
  violation raises `LayoutError` (a print bug becomes a test failure, never a
  clipped signature). Thin optional signature baseline only if configured.
- **Draft/finalize marks:** preview of non-finalized doc renders diagonal
  "DRAFT" watermark + copy of finalized adds footer marker `REPRINT
  yyyy-mm-dd hh:mm by <user>` (REQ-FINALIZE-01).

## 4. Paper & printer integration (REQ-PRINT-01/06/10)

- Profiles stored in DB (`print_profiles`, DATABASE.md §2); resolution order:
  explicit user pick → profile default for doc type → system default printer
  with profile paper.
- `QPrinter` setup: named `QPageSize` for A4/A5; `QPageSizeF(QSizeF(w,h),
  QPageSize.Millimeter)` custom for 80/58 mm (height = chosen paper length or
  297 mm for continuous preview; thermal continuous feed = tall-page mode with
  page-break-at-content-end semantics; driver-dependent actual cut behavior
  documented to clinics).
- Margins default 10 mm / 6 mm receipts; per-profile override; duplex &
  copies pass-through when the driver advertises them (capability checks, no
  assumptions — absent features are disabled, not hidden-crashed).
- No printers installed (CI included): every flow works to PDF; UI shows
  "No printer detected — Print to PDF available" state (REQ-PLAT-06 honesty).
- Printer list refresh on dialog open; Bluetooth/wireless printers appear as
  any Windows driver — zero app-side coupling (validated at hardware time,
  labeled hardware-unavailable otherwise per CONFLICT-D1/D4).

## 5. Print preview UI (REQ-PRINT-08)

Preview page renders PagePlan rasters at fit-width with zoom (10–400%), page
nav, profile switcher (re-layouts live), Print / Save-PDF buttons, copies and
duplex controls (capability-gated), and a "what will print" status line
(printer · paper · margins · pages). The preview *is* PagePlan — there is no
separate preview layout path by construction.

## 6. PDF output (REQ-PRINT-05)

`QPdfWriter` at chosen resolution (default 300 dpi print-quality, vector text
— rasters only for logo/thumbs); PDF version 1.7; fonts embedded+subset (Qt);
metadata: title `Dentiva Pro – Rx INV-2026-00042`, author clinic name;
no encryption. "Microsoft Print to PDF" path is also smoke-tested on Windows
CI as the driver-compat oracle. PDFs open in Edge/standard readers without
local font dependencies (assertion: no system-font fallback required — CI
checks embedded font names present in doc resources).

## 7. Bengali rendering verification (REQ-LOC-01, REQ-FONT-02/03)

- **Coverage gate:** startup + CI verify bundled faces cover the required
  codepoint corpus (Bengali block essentials, ৳, digits, danda `।`, matras,
  conjunct samples) via `QRawFont` glyph checks; any `.notdef` in test corpora
  fails the build.
- **Shaping:** reference strings (য+ক→য্ক, ট+র→ট্র, ক্ষ, দ্ধী, ী/ু/ে/ৈ mats,
  nukta য় ড়) rasterized in CI and compared to committed goldens (perceptual
  diff ≤ threshold); UI and print share the same check.
- **PDF:** CI parses golden PDFs, asserts embedded font subsets carry the
  glyph ids used; no Type3 fallback, no missing-glyph warnings; mixed runs
  (English drug name + Bengali instruction) keep correct baseline spacing
  (golden-measured).
- Numerals: Bengali digit mode (O7) tested in goldens incl. money grouping
  switch; defaults remain Latin.

## 8. Test fixtures & goldens (Phase 11)

Corpora: empty invoice, 1-line, 52-line (exact page), 53-line (+1), 200-line
(multi-page), 200-char Bengali patient + long address clinic, discount +
partial payment, void/copy reprint, draft watermark, large totals (৳1,00,00,000.00),
12 medicines PRN mix. Every fixture renders × {A4, A5, 80, 58, custom 76×130}
× {PDF, preview raster} in the golden suite; regeneration only via
`scripts/regen_print_goldens.py` (CI refuses diffs).

## 9. Failure policy

Print failure (spooler error, driver rejection) → typed error dialog with the
exact profile used and the PDF fallback one-click (auto-saved to
`data/temp/print-fallback/`) + audit row `print.failed`. Cancellation at dialog
= success no-op. Preview never blocks UI (worker, JobRunner kind=print).
Partial multi-page jobs: the engine always produces complete PagePlans before
first paint (no streaming into a half-broken job).

## 10. Hardware validation protocol (honesty rule REQ-GOV-07)

Phase 11 validates engine/PDF/preview equivalence fully in CI. Physical
matrix (thermal, BT, laser, inkjet; A4/A5/80/58) executes when hardware
exists: Phase 18 checklist rows `printer-<name>-<paper>` recorded as
`hardware-validated` vs `hardware-unavailable (validation: PDF-oracle only)`.
No claim in any report may blur the two.
