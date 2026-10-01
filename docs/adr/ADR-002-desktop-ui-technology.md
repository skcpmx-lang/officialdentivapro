# ADR-002 — Desktop UI technology: PySide6 (Qt 6) with a custom-widget design system

- Status: Accepted (Phase 1)
- Date: 2026-10-01
- Related: REQ-UX-*, REQ-DPI-*, REQ-PRINT-*, REQ-PLAT-01..06, REQ-PROD-02

## Context
Requirements: premium custom look with tokens/animations, high-DPI per-monitor
v2, Bengali Unicode + shaping, native Windows printing with real paper sizes
(including thermal widths), offline, commercially redistributable under a
non-copyleft application license, and packaging as a frozen Windows product.

## Decision
Use **PySide6 (Qt 6 Widgets; PySide6-Essentials + Addons as needed)** with:
- A **QSS-driven design-token theme** (tokens generated from a single Python/JSON source; no raw hexes in code) plus custom-painted widgets (cards, sparklines, chart, steppers) where QSS cannot reach.
- **QGraphicsScene/QPainter** for the dental chart (zoom/pan/precision hit-testing).
- Qt's rich-text/HarfBuzz text stack everywhere text renders (Qt uses HarfBuzz for all shaping — correct Bengali conjuncts), including print (ADR-010).
- `QVariantAnimation` for motion with reduced-motion policy (REQ-UX-07).
- `QtPrintSupport` (`QPrinter`, `QPrintDialog`, `QPdfWriter`) — printing is first-class, not an afterthought.
- QtWebEngine, multimedia, and network modules are **excluded** from the build (size + attack surface + offline guarantee). `PySide6-Shiboken/Essentials` minimal install set; `Addons` only if a widget demands it.

Licensing: PySide6 is `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only` (PyPI metadata). We distribute under LGPL-3.0 with the Qt "dynamic linking / Python import" compliance posture: unmodified PySide6 shipped as separate DLLs/pyd in the bundle, LGPL text bundled, relink instructions in THIRD-PARTY-NOTICES (ADR-019). Application code remains proprietary.

## Alternatives considered
- **PyQt6:** identical technical fit, but GPL-3 **or paid Riverbank commercial license** — violates "no paid services" spirit and adds cost risk. Rejected (license economics).
- **Tkinter/CustomTkinter:** trivially packageable but no real shaping guarantees, weak printing, poor high-DPI story, cannot credibly hit "premium flagship" visual bar. Rejected.
- **wxPython:** native widgets are stable but visual customization (tokens/animations/rounded surfaces) fights the platform; packaging quirks with PyInstaller history. Rejected (design ceiling).
- **Kivy:** own GL pipeline; desktop ergonomics (text fields, IME, table density, printing) are weak for a clinic app. Rejected.
- **Qt Quick/QML:** premium animation ceiling, but QML tooling in frozen Windows builds adds complexity; Widgets+painters deliver the same result with deeper data-grid ergonomics and simpler testing. Rejected as primary; QML may power isolated showcase widgets if ever needed (not planned).
- **pywebview/Tauri/Electron-class:** shipping a browser for a dense-data clinic app — memory, printing fidelity, and offline trust all worse. Rejected.
- **Dear PyGui/Fyne/non-Python:** outside language mandate or ecosystem fit. Rejected/documented.

## Consequences
- Installer size grows (Qt runtime ≈ 60–90 MB compressed after module pruning) — accepted for capability; mitigated by excluding unused modules.
- LGPL obligations are procedural (texts, unmodified dynamic imports) — automated in release checks.
- Everything testable offscreen (`QT_QPA_PLATFORM=offscreen`) on Linux CI; Windows CI covers shell integration.
