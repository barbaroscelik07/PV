"""
PV-DOC — Giriş Noktası
"""

import sys
import os

# PyInstaller frozen EXE ve normal çalışma için path ayarı
if getattr(sys, 'frozen', False):
    # EXE olarak çalışıyor — _MEIPASS geçici dizini
    BASE_DIR = sys._MEIPASS
else:
    # Normal Python olarak çalışıyor
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Kök dizini path'e ekle
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.ana_pencere import AnaPencere


def main():
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("PV-DOC")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("PV-DOC")

    font = QFont("Arial", 11)
    app.setFont(font)

    pencere = AnaPencere()
    pencere.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()



def main():
    # HiDPI desteği
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("PV-DOC")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("PV-DOC")

    # Uygulama geneli font
    font = QFont("Arial", 11)
    app.setFont(font)

    pencere = AnaPencere()
    pencere.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
