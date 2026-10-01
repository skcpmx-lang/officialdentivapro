"""Minimal Phase 2 Qt entry point used to verify the packaged runtime."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence


def _create_window() -> object:
    from PySide6.QtWidgets import QLabel, QMainWindow

    from dentiva.core.i18n import _

    window = QMainWindow()
    window.setObjectName("DentivaFoundationWindow")
    window.setWindowTitle(_("Dentiva Pro — Engineering Foundation"))
    window.setMinimumSize(640, 420)
    label = QLabel(
        _("Engineering foundation booted. Clinical workflows are not part of this build.")
    )
    label.setWordWrap(True)
    label.setMargin(24)
    window.setCentralWidget(label)
    return window


def main(argv: Sequence[str] | None = None) -> int:
    """Start the foundation shell, or perform a one-event-loop headless smoke."""
    import argparse

    parser = argparse.ArgumentParser(prog="dentiva")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="create and close the foundation window without entering the event loop",
    )
    arguments = parser.parse_args(argv)
    if arguments.smoke:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([sys.argv[0]])
    application.setApplicationName("Dentiva Pro")
    application.setOrganizationName("Dentiva Pro")
    window = _create_window()
    window.show()
    application.processEvents()

    if arguments.smoke:
        visible = window.isVisible()  # type: ignore[attr-defined]
        window.close()  # type: ignore[attr-defined]
        application.processEvents()
        return 0 if visible else 1
    return application.exec()
