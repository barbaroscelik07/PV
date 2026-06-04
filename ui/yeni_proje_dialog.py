"""
PV-DOC — Yeni Proje Dialog (Modül 1)
Kullanıcı yeni proje oluştururken tüm temel bilgileri tek sayfada girer.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QFrame,
    QSpinBox, QScrollArea, QWidget, QButtonGroup, QRadioButton,
    QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.models import ProjeVerisi, UrunFormu, TabletYapisi, EtkenMaddeSpek
from ui.stiller import (
    RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    FONT_AILESI
)

import datetime


class BolumBasligi(QFrame):
    """İnce bir çizgi ve başlık içeren bölüm ayırıcı."""

    def __init__(self, metin: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 4)
        layout.setSpacing(8)

        lbl = QLabel(metin)
        lbl.setStyleSheet(f"""
            font-size: 10px;
            font-weight: bold;
            color: {RENK_YAZI_UCUNCUL};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(lbl)

        cizgi = QFrame()
        cizgi.setFrameShape(QFrame.Shape.HLine)
        cizgi.setStyleSheet(f"color: {RENK_KENARLIK};")
        layout.addWidget(cizgi, 1)


class FormSatiri(QWidget):
    """Label + input ikilisi."""

    def __init__(self, etiket: str, widget: QWidget, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        lbl = QLabel(etiket)
        lbl.setStyleSheet(f"""
            font-size: 10px;
            font-weight: bold;
            color: {RENK_YAZI_IKINCIL};
        """)
        layout.addWidget(lbl)
        layout.addWidget(widget)


class UrunFormuKarti(QPushButton):
    """Ürün formu seçim kartı."""

    def __init__(self, metin: str, parent=None):
        super().__init__(metin, parent)
        self.setCheckable(True)
        self._guncelle_stil(False)
        self.toggled.connect(self._guncelle_stil)

    def _guncelle_stil(self, secili: bool):
        if secili:
            self.setStyleSheet(f"""
                QPushButton {{
                    border: 2px solid {RENK_PRIMARY};
                    border-radius: 8px;
                    padding: 8px 12px;
                    background-color: {RENK_PRIMARY_ACIK};
                    color: {RENK_PRIMARY_KOYU};
                    font-size: 11px;
                    font-weight: bold;
                    text-align: left;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    border: 1px solid {RENK_KENARLIK};
                    border-radius: 8px;
                    padding: 8px 12px;
                    background-color: {RENK_BG_BIRINCIL};
                    color: {RENK_YAZI_IKINCIL};
                    font-size: 11px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {RENK_BG_IKINCIL};
                    border-color: {RENK_PRIMARY};
                }}
            """)


class EtkenMaddeSatiri(QWidget):
    """Dinamik etken madde giriş satırı."""

    silindi = pyqtSignal(object)

    def __init__(self, no: int, parent=None):
        super().__init__(parent)
        self.no = no
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.lbl_no = QLabel(f"Etken Madde {no}")
        self.lbl_no.setStyleSheet(f"""
            font-size: 10px;
            color: {RENK_YAZI_UCUNCUL};
            min-width: 85px;
        """)
        layout.addWidget(self.lbl_no)

        self.input_ad = QLineEdit()
        self.input_ad.setPlaceholderText("Etken madde adı")
        layout.addWidget(self.input_ad, 1)

        # Katman ataması (çift katmanlı ürünlerde görünür)
        self.combo_katman = QComboBox()
        self.combo_katman.addItems(["Katman I", "Katman II"])
        self.combo_katman.setFixedWidth(95)
        self.combo_katman.setVisible(False)
        self.combo_katman.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {RENK_KENARLIK};
                border-radius: 5px;
                padding: 3px 7px;
                font-size: 11px;
                background: {RENK_BG_BIRINCIL};
            }}
        """)
        layout.addWidget(self.combo_katman)

        self.btn_sil = QPushButton("✕")
        self.btn_sil.setFixedSize(26, 26)
        self.btn_sil.setStyleSheet(f"""
            QPushButton {{
                border: none;
                border-radius: 4px;
                background: transparent;
                color: {RENK_YAZI_UCUNCUL};
                font-size: 12px;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: #FCEBEB;
                color: #A32D2D;
            }}
        """)
        self.btn_sil.clicked.connect(lambda: self.silindi.emit(self))
        layout.addWidget(self.btn_sil)

    def katman_gorunum_guncelle(self, cift_katman: bool):
        self.combo_katman.setVisible(cift_katman)

    def numara_guncelle(self, no: int):
        self.no = no
        self.lbl_no.setText(f"Etken Madde {no}")

    def get_ad(self) -> str:
        return self.input_ad.text().strip()

    def set_ad(self, ad: str):
        self.input_ad.setText(ad)

    def get_katman(self) -> int:
        """0 = Katman I, 1 = Katman II"""
        return self.combo_katman.currentIndex()


class YeniProjeDialog(QDialog):
    """
    Yeni proje oluşturma diyaloğu.
    Tek sayfada tüm temel bilgileri toplar.
    """

    proje_olusturuldu = pyqtSignal(object)  # ProjeVerisi

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Proje Oluştur")
        self.setModal(True)
        self.resize(680, 720)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {RENK_BG_BIRINCIL};
            }}
        """)
        self._etken_maddeler: list[EtkenMaddeSatiri] = []
        self._form_butonlari: list[UrunFormuKarti] = []
        self._setup_ui()

    def _setup_ui(self):
        ana_layout = QVBoxLayout(self)
        ana_layout.setContentsMargins(0, 0, 0, 0)
        ana_layout.setSpacing(0)

        # Başlık çubuğu
        baslik_frame = QFrame()
        baslik_frame.setStyleSheet(f"""
            background-color: {RENK_BG_IKINCIL};
            border-bottom: 1px solid {RENK_KENARLIK};
        """)
        baslik_layout = QHBoxLayout(baslik_frame)
        baslik_layout.setContentsMargins(20, 14, 20, 14)

        ikon = QLabel("📄")
        ikon.setStyleSheet("font-size: 18px; background: transparent;")
        baslik_layout.addWidget(ikon)

        baslik_lbl = QLabel("Yeni Proje Oluştur")
        baslik_lbl.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {RENK_YAZI_BIRINCIL};
            background: transparent;
        """)
        baslik_layout.addWidget(baslik_lbl)
        baslik_layout.addStretch()

        alt_lbl = QLabel("Tüm alanları doldurun")
        alt_lbl.setStyleSheet(f"""
            font-size: 11px;
            color: {RENK_YAZI_UCUNCUL};
            background: transparent;
        """)
        baslik_layout.addWidget(alt_lbl)
        ana_layout.addWidget(baslik_frame)

        # Kaydırılabilir içerik
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        icerik = QWidget()
        icerik.setStyleSheet(f"background-color: {RENK_BG_BIRINCIL};")
        icerik_layout = QVBoxLayout(icerik)
        icerik_layout.setContentsMargins(24, 16, 24, 16)
        icerik_layout.setSpacing(4)

        # ── Firma ve Ürün Bilgileri ──
        icerik_layout.addWidget(BolumBasligi("Firma ve Ürün Bilgileri"))

        grid1 = QGridLayout()
        grid1.setHorizontalSpacing(12)
        grid1.setVerticalSpacing(8)

        self.input_firma = QLineEdit()
        self.input_firma.setPlaceholderText("Firma adını girin")
        grid1.addWidget(FormSatiri("Firma Adı", self.input_firma), 0, 0)

        self.input_urun = QLineEdit()
        self.input_urun.setPlaceholderText("Ürün adını girin")
        grid1.addWidget(FormSatiri("Ürün Adı", self.input_urun), 0, 1)

        self.input_pvp_no = QLineEdit()
        self.input_pvp_no.setPlaceholderText("AG-PV-001")
        grid1.addWidget(FormSatiri("Doküman No (PVP)", self.input_pvp_no), 1, 0)

        self.input_pvr_no = QLineEdit()
        self.input_pvr_no.setPlaceholderText("AG-PV-001-R")
        grid1.addWidget(FormSatiri("Doküman No (PVR)", self.input_pvr_no), 1, 1)

        self.input_revizyon = QLineEdit("00")
        grid1.addWidget(FormSatiri("Revizyon No", self.input_revizyon), 2, 0)

        self.input_tarih = QLineEdit(datetime.date.today().strftime("%d.%m.%Y"))
        grid1.addWidget(FormSatiri("Tarih", self.input_tarih), 2, 1)

        icerik_layout.addLayout(grid1)

        # ── Ürün Formu ──
        icerik_layout.addWidget(BolumBasligi("Ürün Formu"))

        form_layout = QHBoxLayout()
        form_layout.setSpacing(8)

        formlar = [
            (UrunFormu.TABLET.value, "Tablet"),
            (UrunFormu.FILM_TABLET.value, "Film Tablet"),
            (UrunFormu.KAPSUL.value, "Kapsül"),
            (UrunFormu.KAPSUL_FILM_TABLET.value, "Kapsül + Film Tablet"),
        ]
        self._form_degerler = [f[0] for f in formlar]

        for deger, metin in formlar:
            btn = UrunFormuKarti(metin)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(self._form_secildi)
            form_layout.addWidget(btn)
            self._form_butonlari.append(btn)

        self._form_butonlari[1].setChecked(True)  # Film Tablet varsayılan
        icerik_layout.addLayout(form_layout)

        # Tablet yapısı (tek/çift katman)
        self.katman_frame = QFrame()
        katman_layout = QHBoxLayout(self.katman_frame)
        katman_layout.setContentsMargins(0, 4, 0, 0)
        katman_layout.setSpacing(8)

        katman_lbl = QLabel("Tablet Yapısı:")
        katman_lbl.setStyleSheet(f"font-size: 11px; color: {RENK_YAZI_IKINCIL};")
        katman_layout.addWidget(katman_lbl)

        self.btn_tek_katman = QPushButton("Tek Katman")
        self.btn_tek_katman.setCheckable(True)
        self.btn_cift_katman = QPushButton("Çift Katman")
        self.btn_cift_katman.setCheckable(True)
        self.btn_tek_katman.setChecked(True)

        for btn in [self.btn_tek_katman, self.btn_cift_katman]:
            btn.setFixedHeight(30)
            btn.setMinimumWidth(110)
            btn.setStyleSheet(f"""
                QPushButton {{
                    border: 1px solid {RENK_KENARLIK};
                    border-radius: 6px;
                    padding: 4px 12px;
                    background-color: {RENK_BG_BIRINCIL};
                    color: {RENK_YAZI_IKINCIL};
                    font-size: 11px;
                }}
                QPushButton:checked {{
                    background-color: {RENK_PRIMARY_ACIK};
                    border-color: {RENK_PRIMARY};
                    color: {RENK_PRIMARY_KOYU};
                    font-weight: bold;
                }}
                QPushButton:hover:!checked {{
                    background-color: {RENK_BG_IKINCIL};
                }}
            """)
            katman_layout.addWidget(btn)

        self.btn_tek_katman.clicked.connect(
            lambda: self._katman_secildi(TabletYapisi.TEK_KATMAN)
        )
        self.btn_cift_katman.clicked.connect(
            lambda: self._katman_secildi(TabletYapisi.CIFT_KATMAN)
        )

        katman_layout.addStretch()
        icerik_layout.addWidget(self.katman_frame)

        # ── Etken Maddeler ──
        icerik_layout.addWidget(BolumBasligi("Etken Maddeler"))

        self.etken_container = QWidget()
        self.etken_layout = QVBoxLayout(self.etken_container)
        self.etken_layout.setContentsMargins(0, 0, 0, 0)
        self.etken_layout.setSpacing(4)
        icerik_layout.addWidget(self.etken_container)

        btn_ekle = QPushButton("+ Etken Madde Ekle")
        btn_ekle.setStyleSheet(f"""
            QPushButton {{
                border: 1px dashed {RENK_PRIMARY};
                border-radius: 6px;
                padding: 5px 12px;
                background: transparent;
                color: {RENK_PRIMARY};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {RENK_PRIMARY_ACIK};
            }}
        """)
        btn_ekle.clicked.connect(self._etken_ekle)
        icerik_layout.addWidget(btn_ekle)

        # Varsayılan 1 etken madde ekle
        self._etken_ekle()

        # ── Seri Bilgileri ──
        icerik_layout.addWidget(BolumBasligi("Seri Bilgileri"))

        seri_layout = QGridLayout()
        seri_layout.setHorizontalSpacing(12)
        seri_layout.setVerticalSpacing(8)

        self.input_seri1 = QLineEdit()
        self.input_seri1.setPlaceholderText("YYY-P01")
        seri_layout.addWidget(FormSatiri("Seri 1 No", self.input_seri1), 0, 0)

        self.input_seri2 = QLineEdit()
        self.input_seri2.setPlaceholderText("YYY-P02")
        seri_layout.addWidget(FormSatiri("Seri 2 No", self.input_seri2), 0, 1)

        self.input_seri3 = QLineEdit()
        self.input_seri3.setPlaceholderText("YYY-P03")
        seri_layout.addWidget(FormSatiri("Seri 3 No", self.input_seri3), 0, 2)

        self.input_seri_boyutu = QLineEdit()
        self.input_seri_boyutu.setPlaceholderText("150.000 ftb")
        seri_layout.addWidget(FormSatiri("Seri Boyutu", self.input_seri_boyutu), 0, 3)

        icerik_layout.addLayout(seri_layout)
        icerik_layout.addStretch()

        scroll.setWidget(icerik)
        ana_layout.addWidget(scroll, 1)

        # Alt buton çubuğu
        alt_frame = QFrame()
        alt_frame.setStyleSheet(f"""
            background-color: {RENK_BG_IKINCIL};
            border-top: 1px solid {RENK_KENARLIK};
        """)
        alt_layout = QHBoxLayout(alt_frame)
        alt_layout.setContentsMargins(20, 12, 20, 12)
        alt_layout.setSpacing(8)

        btn_ac = QPushButton("📂 Mevcut Proje Aç")
        btn_ac.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                color: {RENK_PRIMARY};
                font-size: 11px;
                padding: 5px 8px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        btn_ac.clicked.connect(self.reject)
        alt_layout.addWidget(btn_ac)

        alt_layout.addStretch()

        btn_iptal = QPushButton("İptal")
        btn_iptal.setFixedHeight(32)
        btn_iptal.setMinimumWidth(80)
        btn_iptal.clicked.connect(self.reject)
        alt_layout.addWidget(btn_iptal)

        btn_olustur = QPushButton("✓ Proje Oluştur")
        btn_olustur.setFixedHeight(34)
        btn_olustur.setMinimumWidth(140)
        btn_olustur.setStyleSheet(f"""
            QPushButton {{
                background-color: {RENK_PRIMARY};
                border: none;
                border-radius: 6px;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: bold;
                font-family: {FONT_AILESI};
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {RENK_PRIMARY_KOYU};
            }}
        """)
        btn_olustur.clicked.connect(self._olustur)
        alt_layout.addWidget(btn_olustur)

        ana_layout.addWidget(alt_frame)

        # Başlangıç durumu
        self._katman_secildi(TabletYapisi.TEK_KATMAN)

    def _form_secildi(self):
        """Ürün formu seçildiğinde diğer butonları kaldır."""
        gonderen = self.sender()
        for btn in self._form_butonlari:
            if btn is not gonderen:
                btn.setChecked(False)
        if not gonderen.isChecked():
            gonderen.setChecked(True)

        # Film Tablet ve Kapsül+Film Tablet için katman seçimi göster
        secili_form = self._get_secili_form()
        tablet_formlar = [
            UrunFormu.TABLET.value,
            UrunFormu.FILM_TABLET.value,
            UrunFormu.KAPSUL_FILM_TABLET.value,
        ]
        self.katman_frame.setVisible(secili_form in tablet_formlar)

    def _katman_secildi(self, katman: TabletYapisi):
        """Katman seçimi butonlarını günceller."""
        if katman == TabletYapisi.TEK_KATMAN:
            self.btn_tek_katman.setChecked(True)
            self.btn_cift_katman.setChecked(False)
        else:
            self.btn_tek_katman.setChecked(False)
            self.btn_cift_katman.setChecked(True)
        # Etken madde satırlarındaki katman dropdown'larını güncelle
        cift = (katman == TabletYapisi.CIFT_KATMAN)
        for satir in self._etken_maddeler:
            satir.katman_gorunum_guncelle(cift)

    def _etken_ekle(self, ad: str = ""):
        no = len(self._etken_maddeler) + 1
        satir = EtkenMaddeSatiri(no, self.etken_container)
        if ad:
            satir.set_ad(ad)
        # Mevcut katman durumunu yeni satıra uygula
        cift = self.btn_cift_katman.isChecked()
        satir.katman_gorunum_guncelle(cift)
        satir.silindi.connect(self._etken_sil)
        self._etken_maddeler.append(satir)
        self.etken_layout.addWidget(satir)

    def _etken_sil(self, satir: EtkenMaddeSatiri):
        if len(self._etken_maddeler) <= 1:
            return  # En az 1 etken madde olmalı
        self._etken_maddeler.remove(satir)
        satir.deleteLater()
        # Numaraları güncelle
        for i, s in enumerate(self._etken_maddeler):
            s.numara_guncelle(i + 1)

    def _get_secili_form(self) -> str:
        for btn, deger in zip(self._form_butonlari, self._form_degerler):
            if btn.isChecked():
                return deger
        return UrunFormu.FILM_TABLET.value

    def _get_secili_katman(self) -> str:
        if self.btn_cift_katman.isChecked():
            return TabletYapisi.CIFT_KATMAN.value
        return TabletYapisi.TEK_KATMAN.value

    def _dogrula(self) -> tuple[bool, str]:
        """Form doğrulaması. (geçerli mi, hata mesajı) döner."""
        if not self.input_urun.text().strip():
            return False, "Ürün adı zorunludur."
        if not self.input_firma.text().strip():
            return False, "Firma adı zorunludur."
        if not self.input_pvp_no.text().strip():
            return False, "PVP doküman numarası zorunludur."
        if not self.input_pvr_no.text().strip():
            return False, "PVR doküman numarası zorunludur."
        for satir in self._etken_maddeler:
            if not satir.get_ad():
                return False, f"Etken Madde {satir.no} adı zorunludur."
        return True, ""

    def _olustur(self):
        gecerli, hata = self._dogrula()
        if not gecerli:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Eksik Bilgi", hata)
            return

        proje = ProjeVerisi()
        proje.firma_adi = self.input_firma.text().strip()
        proje.urun_adi = self.input_urun.text().strip()
        proje.pvp_dokuman_no = self.input_pvp_no.text().strip()
        proje.pvr_dokuman_no = self.input_pvr_no.text().strip()
        proje.revizyon_no = self.input_revizyon.text().strip() or "00"
        proje.tarih = self.input_tarih.text().strip()
        proje.urun_formu = self._get_secili_form()
        proje.tablet_yapisi = self._get_secili_katman()
        proje.seri_1_no = self.input_seri1.text().strip()
        proje.seri_2_no = self.input_seri2.text().strip()
        proje.seri_3_no = self.input_seri3.text().strip()
        proje.seri_boyutu = self.input_seri_boyutu.text().strip()

        for satir in self._etken_maddeler:
            em = EtkenMaddeSpek()
            em.ad = satir.get_ad()
            proje.etken_maddeler.append(em)

        # Çift katmanlı ürünlerde bulk katman ataması
        if proje.tablet_yapisi == TabletYapisi.CIFT_KATMAN.value:
            from core.models import BulkKatmanSpek
            k1 = BulkKatmanSpek(katman_adi="Katman I Bulk")
            k2 = BulkKatmanSpek(katman_adi="Katman II Bulk")
            for i, satir in enumerate(self._etken_maddeler):
                if satir.get_katman() == 0:
                    k1.etken_indeksler.append(i)
                else:
                    k2.etken_indeksler.append(i)
            # Boş katman kalmışsa varsayılan ata
            if not k1.etken_indeksler:
                k1.etken_indeksler = [0] if proje.etken_maddeler else []
            if not k2.etken_indeksler:
                n = len(proje.etken_maddeler)
                k2.etken_indeksler = [n-1] if n > 0 else []
            proje.bulk_katmanlar = [k1, k2]

        self.proje_olusturuldu.emit(proje)
        self.accept()

    def doldur(self, proje: ProjeVerisi):
        """Mevcut proje verisiyle formu doldurur (düzenleme için)."""
        self.input_firma.setText(proje.firma_adi)
        self.input_urun.setText(proje.urun_adi)
        self.input_pvp_no.setText(proje.pvp_dokuman_no)
        self.input_pvr_no.setText(proje.pvr_dokuman_no)
        self.input_revizyon.setText(proje.revizyon_no)
        self.input_tarih.setText(proje.tarih)
        self.input_seri1.setText(proje.seri_1_no)
        self.input_seri2.setText(proje.seri_2_no)
        self.input_seri3.setText(proje.seri_3_no)
        self.input_seri_boyutu.setText(proje.seri_boyutu)

        # Ürün formu
        try:
            idx = self._form_degerler.index(proje.urun_formu)
            for i, btn in enumerate(self._form_butonlari):
                btn.setChecked(i == idx)
        except ValueError:
            pass

        # Tablet yapısı
        if proje.tablet_yapisi == TabletYapisi.CIFT_KATMAN.value:
            self._katman_secildi(TabletYapisi.CIFT_KATMAN)
        else:
            self._katman_secildi(TabletYapisi.TEK_KATMAN)

        # Etken maddeler — mevcut satırları temizle
        for s in self._etken_maddeler[:]:
            s.deleteLater()
        self._etken_maddeler.clear()

        for em in proje.etken_maddeler:
            self._etken_ekle(em.ad)

        if not self._etken_maddeler:
            self._etken_ekle()
