# ADR-014 — Fonts & text: bundled OFL families (Inter + Noto Sans/Serif Bengali) with coverage verification

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-FONT-01..03, REQ-LOC-01..03, REQ-PRINT-05

## Context
The product must render Bengali correctly in UI, print, and PDF regardless of
what the clinic PC has installed, embed fonts in PDFs, and remain legally
redistributable in a closed commercial product.

## Decision
- **Bundled set (fixed versions, checksummed in a font manifest):** UI Latin — **Inter** (OFL; modern, tabular figures available for money columns); UI/print Bengali — **Noto Sans Bengali** (OFL; Regular/Bold, synthesized obliques documented); print headings optional **Noto Serif Bengali** for prescription elegance (Phase 11 golden review decides). License texts shipped.
- **Load strategy:** `QFontDatabase.addApplicationFont` for every bundled face at bootstrap; application font = Inter with fallback chain `["Inter","Noto Sans Bengali","Segoe UI","Tahoma"]` (Tahoma historically safe on down-level Windows); print faces registered separately and selected *per text run* by script detection (Qt auto-fallback covers mixed runs; the engine additionally asserts run coverage).
- **Coverage gate:** startup self-check + CI verify required codepoint sets per face (Latin+BD punctuation incl. `৳ U+09F3`, Bengali letters, matras, digits ০–৯, nukta combos) using `QRawFont.coverageForText`/glyph checks; **zero `.notdef` allowed** in the test corpora. Tofu = build failure, not field bug.
- **PDF embedding:** Qt subsets/embeds registered app fonts automatically (verified by PDF font-resource assertions in print goldens); no reliance on viewer-side fonts ever.
- **Normalization:** NFC applied at input boundaries (REQ-LOC-03); shaping by Qt's HarfBuzz engine (Qt uses HarfBuzz for all shaping) — Bengali conjuncts correct without manual clusters.

## Alternatives considered
- **Segoe UI + system Bengali fallback (Solapani/Vrinda):** zero bundle size, but print/PDF on machines lacking the face breaks, VRinda is legacy-quality, and licensing forbids redistribution of Windows fonts. Rejected — the prompt's "verify fonts, don't assume" rule mandates bundling.
- **Nirmala UI embedding:** not redistributable (Microsoft). Rejected.
- **Vrinda-only Bengali:** no bold, weak hinting at print DPI. Rejected.
- **Source Han / SimSun-based pan-CJK for size savings:** enormous for needs; Noto localized is correct. Rejected.
- **User font installation as a requirement:** contradicts clean-machine mandate. Rejected.

## Consequences
- +~2–4 MB install size (subsettable if ever needed via fonttools — not required).
- OFL means fonts can be embedded in PDFs and redistributed with the app without copyleft (no Reserved Font Name conflicts for Noto/Inter — verified in license audit, ADR-019).
- Aesthetic finalization (weights/sizes) happens in Phase 4 design-token freeze; the *families* are frozen here for legal/packaging reasons.
