"""
PV-DOC — Üretim Prosesi ve Akış Şeması (Modül 4)
Proses adımları tablosu + Akış şeması editörü
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QTabWidget, QAbstractItemView, QTableWidget,
    QTableWidgetItem, QHeaderView, QApplication, QSizePolicy,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush

from core.models import ProjeVerisi, UrunFormu
from ui.stiller import (
    RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    RENK_YESIL, RENK_YESIL_BG, FONT_AILESI
)
from ui.akis_editoru import AkisEditoruWidget


class ProsesAkisWidget(QWidget):
    kaydedildi = pyqtSignal()
    degisti = pyqtSignal()

    def __init__(self, proje: ProjeVerisi, parent=None):
        super().__init__(parent)
        self._proje = proje
        self._setup_ui()
        self._yukle()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        # Toolbar
        tb = QFrame()
        tb.setStyleSheet(
            f"background:{RENK_BG_BIRINCIL};border-bottom:1px solid {RENK_KENARLIK};")
        tb.setFixedHeight(46)
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(16,0,16,0); tbl.setSpacing(8)
        lbl = QLabel("Üretim Prosesi ve Akış Şeması")
        lbl.setStyleSheet(
            f"font-size:13px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        tbl.addWidget(lbl); tbl.addStretch()

        self.lbl_durum = QLabel(""); self.lbl_durum.setVisible(False)
        self.lbl_durum.setStyleSheet(f"""
            font-size:11px; color:{RENK_PRIMARY_KOYU};
            background:{RENK_PRIMARY_ACIK}; border-radius:4px; padding:2px 8px;
        """)
        tbl.addWidget(self.lbl_durum)

        btn_kaydet = QPushButton("💾  Kaydet")
        btn_kaydet.setFixedHeight(30); btn_kaydet.setMinimumWidth(90)
        btn_kaydet.setStyleSheet(f"""
            QPushButton{{background:{RENK_PRIMARY};color:#FFFFFF;border:none;
            border-radius:6px;font-size:12px;font-weight:bold;
            font-family:{FONT_AILESI};padding:0 14px;}}
            QPushButton:hover{{background:{RENK_PRIMARY_KOYU};}}
        """)
        btn_kaydet.clicked.connect(self._kaydet)
        tbl.addWidget(btn_kaydet)
        layout.addWidget(tb)

        # Akış şeması editörü
        self._akis_editoru = AkisEditoruWidget()
        self._akis_editoru.degisti.connect(self._on_degisti)
        layout.addWidget(self._akis_editoru, 1)

    def _yukle(self):
        elemanlar = getattr(self._proje, 'akis_elemanlar', [])
        oklar = getattr(self._proje, 'akis_oklar', [])
        if elemanlar or oklar:
            self._akis_editoru.yukle(
                {"sekiller": elemanlar, "oklar": oklar})
        self.lbl_durum.setVisible(False)

    def _on_degisti(self):
        self.lbl_durum.setText("● Kaydedilmemiş değişiklik")
        self.lbl_durum.setStyleSheet(f"""
            font-size:11px; color:{RENK_PRIMARY_KOYU};
            background:{RENK_PRIMARY_ACIK}; border-radius:4px; padding:2px 8px;
        """)
        self.lbl_durum.setVisible(True)
        self.degisti.emit()

    def _kaydet(self):
        data = self._akis_editoru.to_data()
        self._proje.akis_elemanlar = data.get("sekiller", [])
        self._proje.akis_oklar = data.get("oklar", [])
        self.lbl_durum.setText("✓ Kaydedildi")
        self.lbl_durum.setStyleSheet(f"""
            font-size:11px; color:{RENK_YESIL};
            background:{RENK_YESIL_BG}; border-radius:4px; padding:2px 8px;
        """)
        self.lbl_durum.setVisible(True)
        self.kaydedildi.emit()

    def proje_guncelle(self, proje: ProjeVerisi):
        self._proje = proje
        self._yukle()
