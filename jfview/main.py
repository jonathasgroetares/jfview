"""Entry point for JFView application."""

import sys
import os

# Ensure the parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from jfview.mainwindow import MainWindow, get_app_icon


def main():
    # Enable high-DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    app = QApplication(sys.argv)
    app.setApplicationName("jfview")
    app.setOrganizationName("JFView")
    app.setApplicationVersion("1.0.0")
    app.setDesktopFileName("jfview.desktop")

    # Set application icon globally
    icon = get_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    window = MainWindow()
    window.show()

    # Open file from command line argument
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if os.path.isfile(filepath):
            window.open_file(filepath)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
