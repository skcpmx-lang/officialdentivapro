# Development setup — Phase 2 foundation

The application target is CPython 3.12.x on Windows x64 (ADR-001). Install the
same interpreter on Linux/macOS development machines, then install the pinned
lock manager and synchronize the committed lockfile:

```sh
python -m pip install uv==0.12.21
uv sync --locked --all-groups
uv run --locked python scripts/dev_checks.py
```

Linux GUI/smoke tests use Qt's offscreen platform; Ubuntu CI installs the
runtime libraries `libgl1`, `libegl1`, `libxkbcommon0`, `libdbus-1-3`, and
`libfontconfig1` before running tests. The foundation shell can be started with
`uv run --locked python -m dentiva`; `--smoke` creates and closes the window
without entering the user event loop.

Do not use source builds as a released product. The Phase 2 `release.yml` only
validates the Windows environment and foundation shell; it produces or publishes
no product artifact. Installer and production packaging are later gated work.

The sandbox currently provides CPython 3.11 and may lack Qt's native Linux
runtime libraries. In that environment, run the pure checks (`ruff`, `mypy`,
lock policy, catalog/traceability checks) with the sandbox interpreter; rely on
the pinned CPython 3.12 GitHub Actions jobs for the full Qt smoke and Windows
wheel checks. Do not replace missing Qt system libraries with fake shared-library
stubs.
