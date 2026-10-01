# ADR-018 — Design system & motion policy (QSS tokens + custom painters; restrained animation)

- Status: Accepted (Phase 1) — visual freeze completes in Phase 4
- Date: 2026-10-01
- Related: REQ-UX-01..07, REQ-DPI-01..04, CONFLICT-O8

## Context
"Premium flagship" visual bar, consistency across ~25 screens, animations that
never lag, and a token system defined *before* implementation.

## Decision
- **Token source of truth:** `src/dentiva/ui/theme/tokens.json` (+ generated
  `tokens.py` at build-prep) defines semantic colors (the full named palette
  from REQ-UX-01), typography scale (family × role × size × weight × line-height),
  4-px base spacing scale, radius tiers (4/8/12/16), elevation (3 shadow specs,
  Qt graphics-effect based), density modes (comfortable/compact for tables),
  component metrics (control height 36/40, nav 56, dialog size classes
  S/M/L/XL incl. chart/preview override REQ-DPI-04), motion (durations
  80/120/180/240 ms, standard/emphasis curves). UI code consumes **only** tokens
  (lint rule bans literals).
- **Visual direction (O8 default):** clinical teal primary (`#0F766E`-family)
  on deep-navy ink (`#0B1220`-family) with warm-neutral surfaces; semantic
  red/amber/green tuned for print-safe contrast; light theme is 1.0 default,
  a validated dark theme token set ships disabled-by-default behind a setting
  (Phase 4 audits contrast; "no theme switch" avoids half-tested surfaces).
  Final hexes frozen in Phase 4; the *system* is frozen now.
- **Rendering:** QSS for widget skinning; custom `QStyledItemDelegate`s for
  tables (alternating density, focus rings, selection); hand-painted for
  cards/sparklines/chart; icons from a single SVG set (Phosphor-family, MIT)
  rasterized at token sizes, 1.5px stroke discipline at 20px base —
  no icon-fonts (DPI/emoji fallback hazards).
- **Motion:** transform/opacity-only, default 120 ms micro / 180 ms panels /
  ≤ 240 ms route transitions; `prefers-reduced-motion` honored + app setting
  ("Animations: Full/Balanced/Off"); never animate geometry that reflows text
  (no layout thrash); spinner + progress vocabulary defined once (REQ-SHELL-06).
- **Accessibility floors:** focus rings always (2 px accent + 1 px offset);
  min contrast 4.5:1 body text; hit areas ≥ 32 px, primary ≥ 40; mnemonics +
  tab order rules (REQ-KBD-*).

## Alternatives considered
- **Qt Quick/QML visual system:** motion ceiling slightly higher, toolchain
  complexity rejected in ADR-002; widgets reach the bar with painters.
- **Bootstrap/Tailwind-flavored re-skin (via QWebEngine):** contradicts
  fidelity/DPI/print-culture and package size. Rejected.
- **Heavy parallax/lottie:** fails "never distract, low-power degrade". Rejected.

## Consequences
- Phase 4 delivers the component gallery + token docs + screenshot baselines;
  Phase 14 audits drift with a checklist tied one-to-one to REQ-UX IDs.
- Every screen added later inherits states by construction (base form/table
  classes), which is what makes "no broken empty states" a testable property.
