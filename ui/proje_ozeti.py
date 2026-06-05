"""
PV-DOC — Proje Özeti Widget
Kullanıcı proje temel bilgilerini buradan düzenleyebilir.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import ProjeVerisi, UrunFormu, TabletYapisi
from ui.stiller import (
    RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    RENK_YESIL, RENK_YESIL_BG, FONT_AILESI
)


class ProjeOzetiWidget(QWidget):
    """Proje temel bilgilerini düzenleme sayfası."""

    kaydedildi = pyqtSignal()
    degisti = pyqtSignal()

    def __init__(self, proje: ProjeVerisi, parent=None):
        super().__init__(parent)
        self._proje = proje
        self._setup_ui()
        self._yukle()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(
            f"background:{RENK_BG_BIRINCIL};border-bottom:1px solid {RENK_KENARLIK};")
        toolbar.setFixedHeight(46)
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(16, 0, 16, 0); tb.setSpacing(8)

        lbl = QLabel("Proje Özeti")
        lbl.setStyleSheet(
            f"font-size:13px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        tb.addWidget(lbl)
        sep = QLabel("/"); sep.setStyleSheet(f"color:{RENK_KENARLIK};")
        tb.addWidget(sep)
        alt = QLabel("Temel proje bilgilerini düzenleyin")
        alt.setStyleSheet(f"font-size:12px;color:{RENK_YAZI_IKINCIL};")
        tb.addWidget(alt)
        tb.addStretch()

        self.lbl_durum = QLabel("")
        self.lbl_durum.setVisible(False)
        self.lbl_durum.setStyleSheet(f"""
            font-size:11px;color:{RENK_PRIMARY_KOYU};
            background:{RENK_PRIMARY_ACIK};border-radius:4px;padding:2px 8px;
        """)
        tb.addWidget(self.lbl_durum)

        btn_kaydet = QPushButton("💾  Kaydet")
        btn_kaydet.setFixedHeight(30); btn_kaydet.setMinimumWidth(90)
        btn_kaydet.setStyleSheet(f"""
            QPushButton{{background:{RENK_PRIMARY};color:#FFFFFF;border:none;
            border-radius:6px;font-size:12px;font-weight:bold;
            font-family:{FONT_AILESI};padding:0 14px;}}
            QPushButton:hover{{background:{RENK_PRIMARY_KOYU};}}
        """)
        btn_kaydet.clicked.connect(self._kaydet)
        tb.addWidget(btn_kaydet)
        layout.addWidget(toolbar)

        # Scroll içerik
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        icerik = QWidget()
        icerik.setStyleSheet(f"background:{RENK_BG_BIRINCIL};")
        ic_layout = QVBoxLayout(icerik)
        ic_layout.setContentsMargins(24, 20, 24, 20)
        ic_layout.setSpacing(16)

        # Bilgi notu
        info = QLabel("Bu sayfada proje oluştururken girdiğiniz bilgileri düzenleyebilirsiniz.")
        info.setStyleSheet(f"""
            font-size:11px;color:{RENK_YAZI_IKINCIL};
            background:{RENK_BG_IKINCIL};border:1px solid {RENK_KENARLIK};
            border-radius:6px;padding:8px 12px;
        """)
        ic_layout.addWidget(info)

        # Firma ve Ürün
        ic_layout.addWidget(self._bolum_baslik("Firma ve Ürün Bilgileri"))
        grid1 = QGridLayout(); grid1.setHorizontalSpacing(16); grid1.setVerticalSpacing(10)

        self.input_firma = QLineEdit()
        self.input_firma.setPlaceholderText("Firma adı")
        self.input_firma.textChanged.connect(self.degisti)
        grid1.addWidget(self._form_satiri("Firma Adı", self.input_firma), 0, 0)

        self.input_urun = QLineEdit()
        self.input_urun.setPlaceholderText("Ürün adı")
        self.input_urun.textChanged.connect(self.degisti)
        grid1.addWidget(self._form_satiri("Ürün Adı", self.input_urun), 0, 1)

        self.input_pvp_no = QLineEdit()
        self.input_pvp_no.setPlaceholderText("AG-PV-001")
        self.input_pvp_no.textChanged.connect(self.degisti)
        grid1.addWidget(self._form_satiri("Doküman No (PVP)", self.input_pvp_no), 1, 0)

        self.input_pvr_no = QLineEdit()
        self.input_pvr_no.setPlaceholderText("AG-PV-001-R")
        self.input_pvr_no.textChanged.connect(self.degisti)
        grid1.addWidget(self._form_satiri("Doküman No (PVR)", self.input_pvr_no), 1, 1)

        self.input_revizyon = QLineEdit()
        self.input_revizyon.textChanged.connect(self.degisti)
        grid1.addWidget(self._form_satiri("Revizyon No", self.input_revizyon), 2, 0)

        self.input_tarih = QLineEdit()
        self.input_tarih.textChanged.connect(self.degisti)
        grid1.addWidget(self._form_satiri("Tarih", self.input_tarih), 2, 1)
        ic_layout.addLayout(grid1)

        # Ürün Formu (sadece göster)
        ic_layout.addWidget(self._bolum_baslik("Ürün Formu ve Yapısı"))

        form_info = QFrame()
        form_info.setStyleSheet(f"""
            background:{RENK_BG_IKINCIL};border:1px solid {RENK_KENARLIK};
            border-radius:8px;
        """)
        fi_layout = QHBoxLayout(form_info)
        fi_layout.setContentsMargins(16, 12, 16, 12); fi_layout.setSpacing(24)

        self.lbl_urun_formu = QLabel("")
        self.lbl_urun_formu.setStyleSheet(f"font-size:13px;color:{RENK_YAZI_BIRINCIL};font-weight:bold;")
        fi_layout.addWidget(QLabel("Ürün Formu:"))
        fi_layout.addWidget(self.lbl_urun_formu)

        self.lbl_tablet_yapisi = QLabel("")
        self.lbl_tablet_yapisi.setStyleSheet(f"font-size:13px;color:{RENK_YAZI_BIRINCIL};font-weight:bold;")
        fi_layout.addWidget(QLabel("Tablet Yapısı:"))
        fi_layout.addWidget(self.lbl_tablet_yapisi)
        fi_layout.addStretch()

        uyari = QLabel("⚠ Ürün formu ve tablet yapısı değiştirilemez.")
        uyari.setStyleSheet(f"font-size:10px;color:{RENK_YAZI_UCUNCUL};")
        fi_layout.addWidget(uyari)
        ic_layout.addWidget(form_info)

        # Etken Maddeler (sadece göster)
        ic_layout.addWidget(self._bolum_baslik("Etken Maddeler"))
        self.lbl_etkenler = QLabel("")
        self.lbl_etkenler.setStyleSheet(f"""
            font-size:12px;color:{RENK_YAZI_BIRINCIL};
            background:{RENK_BG_IKINCIL};border:1px solid {RENK_KENARLIK};
            border-radius:6px;padding:10px 16px;
        """)
        self.lbl_etkenler.setWordWrap(True)
        ic_layout.addWidget(self.lbl_etkenler)

        em_uyari = QLabel("⚠ Etken maddeler değiştirilemez. Değişiklik için yeni proje oluşturun.")
        em_uyari.setStyleSheet(f"font-size:10px;color:{RENK_YAZI_UCUNCUL};")
        ic_layout.addWidget(em_uyari)

        # Seri Bilgileri
        ic_layout.addWidget(self._bolum_baslik("Seri Bilgileri"))
        grid2 = QGridLayout(); grid2.setHorizontalSpacing(16); grid2.setVerticalSpacing(10)

        self.input_seri1 = QLineEdit()
        self.input_seri1.setPlaceholderText("YYY-P01")
        self.input_seri1.textChanged.connect(self.degisti)
        grid2.addWidget(self._form_satiri("Seri 1 No", self.input_seri1), 0, 0)

        self.input_seri2 = QLineEdit()
        self.input_seri2.setPlaceholderText("YYY-P02")
        self.input_seri2.textChanged.connect(self.degisti)
        grid2.addWidget(self._form_satiri("Seri 2 No", self.input_seri2), 0, 1)

        self.input_seri3 = QLineEdit()
        self.input_seri3.setPlaceholderText("YYY-P03")
        self.input_seri3.textChanged.connect(self.degisti)
        grid2.addWidget(self._form_satiri("Seri 3 No", self.input_seri3), 0, 2)

        self.input_seri_boyutu = QLineEdit()
        self.input_seri_boyutu.setPlaceholderText("150.000 ftb")
        self.input_seri_boyutu.textChanged.connect(self.degisti)
        grid2.addWidget(self._form_satiri("Seri Boyutu", self.input_seri_boyutu), 1, 0)
        ic_layout.addLayout(grid2)

        ic_layout.addStretch()
        scroll.setWidget(icerik)
        layout.addWidget(scroll, 1)

    def _bolum_baslik(self, metin: str) -> QLabel:
        lbl = QLabel(metin.upper())
        lbl.setStyleSheet(f"""
            font-size:9px;font-weight:bold;color:{RENK_YAZI_UCUNCUL};
            letter-spacing:0.5px;padding:4px 0 2px 0;
            border-bottom:1px solid {RENK_KENARLIK};
        """)
        return lbl

    def _form_satiri(self, etiket: str, widget: QWidget) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(3)
        lbl = QLabel(etiket)
        lbl.setStyleSheet(
            f"font-size:10px;font-weight:bold;color:{RENK_YAZI_IKINCIL};")
        l.addWidget(lbl); l.addWidget(widget)
        return w

    def _yukle(self):
        self.input_firma.setText(self._proje.firma_adi)
        self.input_urun.setText(self._proje.urun_adi)
        self.input_pvp_no.setText(self._proje.pvp_dokuman_no)
        self.input_pvr_no.setText(self._proje.pvr_dokuman_no)
        self.input_revizyon.setText(self._proje.revizyon_no)
        self.input_tarih.setText(self._proje.tarih)
        self.input_seri1.setText(self._proje.seri_1_no)
        self.input_seri2.setText(self._proje.seri_2_no)
        self.input_seri3.setText(self._proje.seri_3_no)
        self.input_seri_boyutu.setText(self._proje.seri_boyutu)
        self.lbl_urun_formu.setText(self._proje.urun_formu)
        self.lbl_tablet_yapisi.setText(self._proje.tablet_yapisi)
        etkenler = ", ".join(
            [em.ad for em in self._proje.etken_maddeler]) or "—"
        self.lbl_etkenler.setText(f"Etken Maddeler: {etkenler}")
        self.lbl_durum.setVisible(False)

    def _kaydet(self):
        self._proje.firma_adi = self.input_firma.text().strip()
        self._proje.urun_adi = self.input_urun.text().strip()
        self._proje.pvp_dokuman_no = self.input_pvp_no.text().strip()
        self._proje.pvr_dokuman_no = self.input_pvr_no.text().strip()
        self._proje.revizyon_no = self.input_revizyon.text().strip() or "00"
        self._proje.tarih = self.input_tarih.text().strip()
        self._proje.seri_1_no = self.input_seri1.text().strip()
        self._proje.seri_2_no = self.input_seri2.text().strip()
        self._proje.seri_3_no = self.input_seri3.text().strip()
        self._proje.seri_boyutu = self.input_seri_boyutu.text().strip()

        self.lbl_durum.setText("✓ Kaydedildi")
        self.lbl_durum.setStyleSheet(f"""
            font-size:11px;color:{RENK_YESIL};
            background:{RENK_YESIL_BG};border-radius:4px;padding:2px 8px;
        """)
        self.lbl_durum.setVisible(True)
        self.kaydedildi.emit()

    def proje_guncelle(self, proje: ProjeVerisi):
        self._proje = proje
        self._yukle()
