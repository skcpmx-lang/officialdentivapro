# ADR-011 — Printing subsystem: custom Qt painter layout engine, one model → preview / PDF / printer

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-PRINT-01..10, REQ-RX-05, REQ-BILL-09, CONFLICT-C4, REQ-LOC-01

## Context
Prescriptions and invoices are flagship deliverables: exact signature-zone
clearance, paper-size adaptation (A4/A5/80 mm/58 mm/custom), multi-page
tables, Bengali shaping, embedded-font PDFs, native printer access, and — the
hard one — a preview that *is* the print (not an approximation), with no paid
components and no network.

## Decision
Build a **deterministic layout engine on QPainter primitives** (package
`dentiva.printing`):

1. **Document model:** documents are composed as typed block trees
   (`Header(logo, clinic lines, dentist block)`, `PatientRow`, `ClinicalSection("C/C")`, `LineTable(items, columns, rules)`, `SignatureBlock(zone_height_mm)`, `FooterNote`) generated from frozen DB snapshots (REQ-DATA-05). No HTML, no templates-that-reflow-unpredictably.
2. **Layout pass:** pure computation (mm-space) producing positioned
   draw-operations + resolved pagination (`PagePlan`), honoring width-class
   rules (ADR-011 §4), min/max font bands, orphan rules, and **hard
   reservations** (signature zone is a reserved rect; engine asserts nothing
   draws inside; overflow paginates — never collides).
3. **Render pass:** identical `DrawOp` stream consumed by three sinks:
   `QPdfWriter` (PDF, embedded subset fonts) → `QPrinter` (physical), and
   raster `QImage` at preview DPI (preview shows the actual PagePlan pages,
   zoomed). Because all sinks execute the same op stream, REQ-PRINT-02
   equivalence is structural; CI verifies raster-of-PDF ≈ raster-of-preview
   (perceptual hash threshold) and QPrinter-output ≈ QPdfWriter-output on
   Windows CI via Microsoft Print to PDF.
4. **Text:** Qt rich text engine (HarfBuzz) through `QStaticText`/`QRawFont`
   with the bundled font manifest; shaping/glyph-coverage checks before draw
   (fallback chain documented ADR-013). Line breaking respects Bengali
   clusters (no mid-conjunct breaks) via `QTextLine` natural language splits.
5. **Printer integration:** native `QPrinter`/`QPrintDialog`; paper profiles
   map to `QPageSize` named sizes + `QPageSize(QSizeF(w_mm,h_mm))` custom for
   receipt widths; margins from profile; thermal continuous-feed simulated in
   engine by tall-page pagination (80 mm × computed height) with documented
   driver caveats; printer *availability* never assumed (graceful no-printer
   state = PDF path).
6. **Units:** engine math in millimeters (float ok for geometry, never for
   money — layout is display-space only), output DPI from device; 0.2 mm grid
   snapping for professional alignment across fonts/DPIs.

## Alternatives considered
- **`QTextDocument` + HTML templates:** fast to author, but pagination,
  signature-zone guarantees, receipt widths, and print fidelity differ
  subtly between print paths and preview; the "preview must be actual output"
  requirement fights the HTML reflow model. Rejected for documents; HTML
  remains *out* everywhere to keep one rendering culture.
- **ReportLab:** excellent PDF, BSD-licensed — but its text pipelines shape
  only via plug-ins; Bengali conjunct correctness would require extra
  dependencies and still diverge from Qt's preview raster (two engines = two
  truths). Rejected on the single-renderer guarantee.
- **weasyprint + Pango:** stronger CSS pagination, but heavy native-dep
  chain (cairo/pango) in frozen Windows builds and preview-via-Web engine
  breaks single-renderer. Rejected.
- **Direct `IPrintDialog`/Win32 spooler interop:** only needed for features
  Qt lacks; none apply. Rejected.
- **Windows print queue PDF conversion for preview:** second rendering truth. Rejected.

## Consequences
- The layout engine is a real engineering asset (~2–3k lines + goldens),
  built in Phase 11 with headless tests from day one (op-stream snapshot
  tests are pure-Python, no display needed).
- Golden fixtures: reference PDFs + rasters per doc type × paper profile
  live in `tests/printing/goldens`; regenerated only via explicit approved
  command, diffs reviewed in phase reports (prevents silent visual drift).
- Thermal 1-bit friendliness: engine auto-switches to line-art logo + no
  hairlines < 0.35 mm for receipt width classes (REQ-PRINT-10).
