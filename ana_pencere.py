"""
PV-DOC — Ana Pencere
Sol navigasyon paneli + sağda modül içerik alanı.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QFileDialog,
    QMessageBox, QSizePolicy, QStackedWidget, QScrollArea,
    QStatusBar, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QCloseEvent

from core.models import ProjeVerisi
from ui.stiller import (
    ANA_STIL, RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    FONT_AILESI
)
from ui.spec_karti import SpecKartiWidget
from ui.yeni_proje_dialog import YeniProjeDialog
from ui.birim_formul import BirimFormulWidget

import os


class NavItem(QPushButton):
    """Sol panel navigasyon butonu."""

    def __init__(self, metin: str, ikon: str = "", parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self._metin = metin
        self._ikon = ikon
        self.setText(f"  {ikon}  {metin}" if ikon else metin)
        self.setFixedHeight(32)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._guncelle_stil(False)
        self.toggled.connect(self._guncelle_stil)

    def _guncelle_stil(self, secili: bool):
        if secili:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {RENK_PRIMARY_ACIK};
                    color: {RENK_PRIMARY_KOYU};
                    border: none;
                    border-left: 2px solid {RENK_PRIMARY};
                    text-align: left;
                    padding-left: 12px;
                    font-size: 12px;
                    font-weight: bold;
                    font-family: {FONT_AILESI};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {RENK_YAZI_IKINCIL};
                    border: none;
                    border-left: 2px solid transparent;
                    text-align: left;
                    padding-left: 12px;
                    font-size: 12px;
                    font-family: {FONT_AILESI};
                }}
                QPushButton:hover {{
                    background-color: {RENK_BG_IKINCIL};
                    color: {RENK_YAZI_BIRINCIL};
                }}
            """)


class NavBaslik(QLabel):
    """Sol panel bölüm başlığı."""

    def __init__(self, metin: str, parent=None):
        super().__init__(metin.upper(), parent)
        self.setStyleSheet(f"""
            font-size: 9px;
            font-weight: bold;
            color: {RENK_YAZI_UCUNCUL};
            letter-spacing: 0.5px;
            padding: 10px 14px 2px 14px;
            background: transparent;
        """)


class ProjeInfoPanel(QFrame):
    """Sol üstte aktif proje bilgisini gösteren panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            background-color: {RENK_BG_IKINCIL};
            border-bottom: 1px solid {RENK_KENARLIK};
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        self.lbl_etiket = QLabel("Aktif Proje")
        self.lbl_etiket.setStyleSheet(f"""
            font-size: 9px;
            font-weight: bold;
            color: {RENK_YAZI_UCUNCUL};
            text-transform: uppercase;
            letter-spacing: 0.4px;
        """)
        layout.addWidget(self.lbl_etiket)

        self.lbl_urun = QLabel("Proje yok")
        self.lbl_urun.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {RENK_YAZI_BIRINCIL};
        """)
        self.lbl_urun.setWordWrap(True)
        layout.addWidget(self.lbl_urun)

        self.lbl_form = QLabel("")
        self.lbl_form.setStyleSheet(f"""
            font-size: 10px;
            color: {RENK_YAZI_UCUNCUL};
        """)
        layout.addWidget(self.lbl_form)

    def guncelle(self, proje: ProjeVerisi = None):
        if proje:
            self.lbl_urun.setText(proje.urun_adi or "—")
            bilgi = proje.urun_formu
            if proje.etken_maddeler:
                bilgi += f"  ·  {len(proje.etken_maddeler)} EM"
            self.lbl_form.setText(bilgi)
        else:
            self.lbl_urun.setText("Proje yok")
            self.lbl_form.setText("")


class BosPlaket(QWidget):
    """Proje açılmadan önce gösterilen karşılama ekranı."""

    yeni_proje_istendi = None
    proje_ac_istendi = None

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        ikon = QLabel("📋")
        ikon.setStyleSheet("font-size: 48px;")
        ikon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ikon)

        baslik = QLabel("PV-DOC")
        baslik.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {RENK_YAZI_BIRINCIL};
        """)
        baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(baslik)

        alt = QLabel("Proses Validasyon Doküman Sistemi")
        alt.setStyleSheet(f"font-size: 13px; color: {RENK_YAZI_IKINCIL};")
        alt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(alt)

        layout.addSpacing(24)

        self.btn_yeni = QPushButton("+ Yeni Proje Oluştur")
        self.btn_yeni.setObjectName("btnPrimary")
        self.btn_yeni.setFixedHeight(44)
        self.btn_yeni.setFixedWidth(240)
        self.btn_yeni.setStyleSheet(f"""
            QPushButton {{
                background-color: {RENK_PRIMARY};
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 13px;
                font-weight: bold;
                font-family: {FONT_AILESI};
            }}
            QPushButton:hover {{
                background-color: {RENK_PRIMARY_KOYU};
            }}
        """)
        layout.addWidget(self.btn_yeni, 0, Qt.AlignmentFlag.AlignCenter)

        self.btn_ac = QPushButton("📂 Mevcut Proje Aç")
        self.btn_ac.setFixedHeight(40)
        self.btn_ac.setFixedWidth(220)
        layout.addWidget(self.btn_ac, 0, Qt.AlignmentFlag.AlignCenter)

        versiyon = QLabel("v1.0 — Geliştirme Aşaması")
        versiyon.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_UCUNCUL};")
        versiyon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(versiyon)


class AnaPencere(QMainWindow):
    """
    PV-DOC Ana Pencere.
    Sol: navigasyon paneli | Sağ: stacked modül içerik alanı
    """

    def __init__(self):
        super().__init__()
        self._proje: ProjeVerisi = None
        self._proje_dosyasi: str = None
        self._kayit_gerekli = False

        self.setWindowTitle("PV-DOC — Proses Validasyon Doküman Sistemi")
        self.resize(1280, 820)
        self.setMinimumSize(1024, 700)
        self.setStyleSheet(ANA_STIL)

        self._setup_ui()
        self._show_bos_ekran()

    def _setup_ui(self):
        merkez = QWidget()
        self.setCentralWidget(merkez)
        ana_layout = QHBoxLayout(merkez)
        ana_layout.setContentsMargins(0, 0, 0, 0)
        ana_layout.setSpacing(0)

        # ── Sol Panel ──
        self.sol_panel = QFrame()
        self.sol_panel.setFixedWidth(200)
        self.sol_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {RENK_BG_BIRINCIL};
                border-right: 1px solid {RENK_KENARLIK};
            }}
        """)
        sol_layout = QVBoxLayout(self.sol_panel)
        sol_layout.setContentsMargins(0, 0, 0, 0)
        sol_layout.setSpacing(0)

        # Logo
        logo_frame = QFrame()
        logo_frame.setStyleSheet(f"""
            background-color: {RENK_BG_BIRINCIL};
            border-bottom: 1px solid {RENK_KENARLIK};
        """)
        logo_frame.setFixedHeight(52)
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(14, 0, 14, 0)
        logo_ikon = QLabel("📋")
        logo_ikon.setStyleSheet("font-size: 16px; background: transparent;")
        logo_layout.addWidget(logo_ikon)
        logo_metin_layout = QVBoxLayout()
        logo_metin_layout.setSpacing(0)
        logo_t = QLabel("PV-DOC")
        logo_t.setStyleSheet(f"""
            font-size: 13px;
            font-weight: bold;
            color: {RENK_YAZI_BIRINCIL};
            background: transparent;
        """)
        logo_s = QLabel("Validasyon Sistemi")
        logo_s.setStyleSheet(f"""
            font-size: 9px;
            color: {RENK_YAZI_UCUNCUL};
            background: transparent;
        """)
        logo_metin_layout.addWidget(logo_t)
        logo_metin_layout.addWidget(logo_s)
        logo_layout.addLayout(logo_metin_layout)
        logo_layout.addStretch()
        sol_layout.addWidget(logo_frame)

        # Proje bilgisi
        self.proje_info = ProjeInfoPanel()
        sol_layout.addWidget(self.proje_info)

        # Navigasyon
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setStyleSheet("background: transparent;")
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        nav_icerik = QWidget()
        nav_icerik.setStyleSheet("background: transparent;")
        self._nav_layout = QVBoxLayout(nav_icerik)
        self._nav_layout.setContentsMargins(0, 4, 0, 4)
        self._nav_layout.setSpacing(0)

        self._nav_butonlari: list[tuple[str, NavItem]] = []
        self._nav_modulleri = [
            ("dokuman", [
                ("proje_ozeti", "🏠", "Proje Özeti"),
                ("spec_karti", "📊", "Spec Kartı"),
                ("birim_formul", "🧪", "Birim Formül"),
            ]),
            ("pvp", [
                ("proses_akis", "🔀", "Proses & Akış"),
                ("risk_analizi", "⚠️", "Risk Analizi"),
                ("ekipmanlar", "🔧", "Ekipmanlar"),
            ]),
            ("pvr", [
                ("sonuc_tablolari", "📋", "Sonuç Tabloları"),
                ("degerlendirme", "✅", "Değerlendirme"),
            ]),
        ]

        baslik_metinleri = {
            "dokuman": "Doküman",
            "pvp": "Protokol (PVP)",
            "pvr": "Rapor (PVR)",
        }

        for bolum_key, maddeler in self._nav_modulleri:
            self._nav_layout.addWidget(NavBaslik(baslik_metinleri[bolum_key]))
            for mod_key, ikon, metin in maddeler:
                btn = NavItem(metin, ikon)
                btn.clicked.connect(lambda c, k=mod_key: self._nav_sec(k))
                self._nav_layout.addWidget(btn)
                self._nav_butonlari.append((mod_key, btn))

        self._nav_layout.addStretch()

        # Alt butonlar
        alt_frame = QFrame()
        alt_frame.setStyleSheet(f"""
            border-top: 1px solid {RENK_KENARLIK};
            background: {RENK_BG_BIRINCIL};
            padding: 8px;
        """)
        alt_layout = QVBoxLayout(alt_frame)
        alt_layout.setContentsMargins(8, 8, 8, 8)
        alt_layout.setSpacing(4)

        self.btn_word = QPushButton("📄 Word Çıktısı")
        self.btn_word.setFixedHeight(30)
        self.btn_word.setEnabled(False)
        alt_layout.addWidget(self.btn_word)

        self.btn_pdf = QPushButton("📑 PDF Çıktısı")
        self.btn_pdf.setFixedHeight(30)
        self.btn_pdf.setEnabled(False)
        alt_layout.addWidget(self.btn_pdf)

        nav_scroll.setWidget(nav_icerik)
        sol_layout.addWidget(nav_scroll, 1)
        sol_layout.addWidget(alt_frame)

        ana_layout.addWidget(self.sol_panel)

        # ── Sağ Alan (Stacked Widget) ──
        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet(f"background-color: {RENK_BG_BIRINCIL};")
        ana_layout.addWidget(self.stacked, 1)

        # Boş ekran
        self.bos_ekran = BosPlaket()
        self.bos_ekran.btn_yeni.clicked.connect(self._yeni_proje)
        self.bos_ekran.btn_ac.clicked.connect(self._proje_ac)
        self.stacked.addWidget(self.bos_ekran)

        # Placeholder widget'lar (modüller ilerleyen aşamalarda gelecek)
        self._placeholder_widgets = {}
        modul_adlari = [
            "proje_ozeti", "spec_karti", "birim_formul",
            "proses_akis", "risk_analizi", "ekipmanlar",
            "sonuc_tablolari", "degerlendirme"
        ]
        for key in modul_adlari:
            if key == "spec_karti":
                w = QWidget()  # SpecKarti sonradan eklenecek
                w.setProperty("modkey", key)
            else:
                w = self._placeholder_olustur(key)
            self._placeholder_widgets[key] = w
            self.stacked.addWidget(w)

        # Menü çubuğu
        self._menubar_kur()

        # Durum çubuğu
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background-color: {RENK_BG_BIRINCIL};
                border-top: 1px solid {RENK_KENARLIK};
                font-size: 10px;
                color: {RENK_YAZI_UCUNCUL};
            }}
        """)
        self.statusBar().showMessage("Hazır — Yeni proje oluşturun veya mevcut projeyi açın.")

    def _placeholder_olustur(self, key: str) -> QWidget:
        """Henüz geliştirilmemiş modüller için placeholder."""
        modül_adlari = {
            "proje_ozeti": "Proje Özeti",
            "birim_formul": "Birim Formül ve Ürün Bilgileri",
            "proses_akis": "Proses Akış Diyagramı",
            "risk_analizi": "Risk Analizi ve Parametreler",
            "ekipmanlar": "Ekipman Listesi",
            "sonuc_tablolari": "PVR Sonuç Tabloları",
            "degerlendirme": "Genel Değerlendirme",
        }
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(f"⚙️  {modül_adlari.get(key, key)}")
        lbl.setStyleSheet(f"""
            font-size: 16px;
            color: {RENK_YAZI_IKINCIL};
        """)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        lbl2 = QLabel("Bu modül geliştirme aşamasındadır.")
        lbl2.setStyleSheet(f"font-size: 12px; color: {RENK_YAZI_UCUNCUL};")
        lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl2)

        return w

    def _menubar_kur(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {RENK_BG_BIRINCIL};
                color: {RENK_YAZI_BIRINCIL};
                border-bottom: 1px solid {RENK_KENARLIK};
                font-size: 12px;
            }}
            QMenuBar::item:selected {{
                background-color: {RENK_PRIMARY_ACIK};
                color: {RENK_PRIMARY_KOYU};
            }}
            QMenu {{
                background-color: {RENK_BG_BIRINCIL};
                border: 1px solid {RENK_KENARLIK};
                border-radius: 6px;
            }}
            QMenu::item {{
                padding: 5px 20px;
                font-size: 12px;
            }}
            QMenu::item:selected {{
                background-color: {RENK_PRIMARY_ACIK};
                color: {RENK_PRIMARY_KOYU};
            }}
            QMenu::separator {{
                height: 1px;
                background: {RENK_KENARLIK};
                margin: 4px 0;
            }}
        """)

        # Dosya menüsü
        dosya_menu = menubar.addMenu("Dosya")

        eylem_yeni = dosya_menu.addAction("Yeni Proje")
        eylem_yeni.setShortcut("Ctrl+N")
        eylem_yeni.triggered.connect(self._yeni_proje)

        eylem_ac = dosya_menu.addAction("Proje Aç")
        eylem_ac.setShortcut("Ctrl+O")
        eylem_ac.triggered.connect(self._proje_ac)

        dosya_menu.addSeparator()

        self.eylem_kaydet = dosya_menu.addAction("Kaydet")
        self.eylem_kaydet.setShortcut("Ctrl+S")
        self.eylem_kaydet.triggered.connect(self._kaydet)
        self.eylem_kaydet.setEnabled(False)

        self.eylem_farkli_kaydet = dosya_menu.addAction("Farklı Kaydet")
        self.eylem_farkli_kaydet.setShortcut("Ctrl+Shift+S")
        self.eylem_farkli_kaydet.triggered.connect(self._farkli_kaydet)
        self.eylem_farkli_kaydet.setEnabled(False)

        dosya_menu.addSeparator()

        eylem_cikis = dosya_menu.addAction("Çıkış")
        eylem_cikis.setShortcut("Ctrl+Q")
        eylem_cikis.triggered.connect(self.close)

    def _show_bos_ekran(self):
        self.stacked.setCurrentWidget(self.bos_ekran)
        self._nav_tumu_deaktif()

    def _nav_tumu_deaktif(self):
        for _, btn in self._nav_butonlari:
            btn.setEnabled(False)
            btn.setChecked(False)

    def _nav_tumu_aktif(self):
        for _, btn in self._nav_butonlari:
            btn.setEnabled(True)

    def _nav_sec(self, key: str):
        """Navigasyon butonuna basıldığında ilgili widget'ı gösterir."""
        for k, btn in self._nav_butonlari:
            btn.setChecked(k == key)

        if key in self._placeholder_widgets:
            w = self._placeholder_widgets[key]
            self.stacked.setCurrentWidget(w)

    def _yeni_proje(self):
        """Yeni proje oluşturma diyaloğunu açar."""
        if self._kayit_gerekli:
            cevap = QMessageBox.question(
                self,
                "Kaydedilmemiş Değişiklikler",
                "Kaydedilmemiş değişiklikler var. Devam etmek istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if cevap == QMessageBox.StandardButton.No:
                return

        dialog = YeniProjeDialog(self)
        dialog.proje_olusturuldu.connect(self._proje_yuklendi)
        dialog.exec()

    def _proje_ac(self):
        """Mevcut proje dosyasını açar."""
        if self._kayit_gerekli:
            cevap = QMessageBox.question(
                self,
                "Kaydedilmemiş Değişiklikler",
                "Kaydedilmemiş değişiklikler var. Devam etmek istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if cevap == QMessageBox.StandardButton.No:
                return

        dosya, _ = QFileDialog.getOpenFileName(
            self, "Proje Aç", "",
            "PV-DOC Proje Dosyaları (*.pvproj *.json)"
        )
        if not dosya:
            return

        try:
            proje = ProjeVerisi.load(dosya)
            self._proje_dosyasi = dosya
            self._proje_yuklendi(proje)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Proje açılamadı:\n{str(e)}")

    def _proje_yuklendi(self, proje: ProjeVerisi):
        """Proje yüklendiğinde arayüzü günceller."""
        self._proje = proje
        self._kayit_gerekli = False

        self.proje_info.guncelle(proje)
        self.setWindowTitle(f"PV-DOC — {proje.urun_adi or 'Yeni Proje'}")
        self._nav_tumu_aktif()
        self.eylem_kaydet.setEnabled(True)
        self.eylem_farkli_kaydet.setEnabled(True)
        self.btn_word.setEnabled(True)
        self.btn_pdf.setEnabled(True)

        # Spec kartı widget'ını oluştur veya güncelle
        if isinstance(self._placeholder_widgets.get("spec_karti"), SpecKartiWidget):
            self._placeholder_widgets["spec_karti"].proje_guncelle(proje)
        else:
            eski = self._placeholder_widgets["spec_karti"]
            self.stacked.removeWidget(eski)
            eski.deleteLater()
            spec_w = SpecKartiWidget(proje)
            spec_w.kaydedildi.connect(lambda: self.statusBar().showMessage("Spec kartı kaydedildi."))
            spec_w.degisti.connect(lambda: self._kayit_isaretle())
            self._placeholder_widgets["spec_karti"] = spec_w
            self.stacked.addWidget(spec_w)

        # Birim formül widget'ını oluştur veya güncelle
        if isinstance(self._placeholder_widgets.get("birim_formul"), BirimFormulWidget):
            self._placeholder_widgets["birim_formul"].proje_guncelle(proje)
        else:
            eski = self._placeholder_widgets["birim_formul"]
            self.stacked.removeWidget(eski)
            eski.deleteLater()
            bf_w = BirimFormulWidget(proje)
            bf_w.kaydedildi.connect(lambda: self.statusBar().showMessage("Birim formül kaydedildi."))
            bf_w.degisti.connect(lambda: self._kayit_isaretle())
            self._placeholder_widgets["birim_formul"] = bf_w
            self.stacked.addWidget(bf_w)

        self._nav_sec("spec_karti")
        self.statusBar().showMessage(f"Proje yüklendi: {proje.urun_adi}")

    def _kayit_isaretle(self):
        self._kayit_gerekli = True
        baslik = self.windowTitle()
        if not baslik.startswith("● "):
            self.setWindowTitle("● " + baslik)

    def _kaydet(self):
        """Projeyi mevcut konuma kaydeder."""
        if not self._proje:
            return

        # Spec kartını kaydet
        spec_w = self._placeholder_widgets.get("spec_karti")
        if isinstance(spec_w, SpecKartiWidget):
            spec_w._kaydet()

        # Birim formülü kaydet
        bf_w = self._placeholder_widgets.get("birim_formul")
        if isinstance(bf_w, BirimFormulWidget):
            bf_w._kaydet()

        if not self._proje_dosyasi:
            self._farkli_kaydet()
            return

        try:
            self._proje.save(self._proje_dosyasi)
            self._kayit_gerekli = False
            baslik = self.windowTitle().lstrip("● ")
            self.setWindowTitle(baslik)
            self.statusBar().showMessage(
                f"Kaydedildi: {os.path.basename(self._proje_dosyasi)}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Kayıt Hatası", f"Dosya kaydedilemedi:\n{str(e)}")

    def _farkli_kaydet(self):
        """Projeyi yeni bir konuma kaydeder."""
        if not self._proje:
            return

        dosya, _ = QFileDialog.getSaveFileName(
            self,
            "Farklı Kaydet",
            f"{self._proje.urun_adi or 'proje'}.pvproj",
            "PV-DOC Proje Dosyaları (*.pvproj);;JSON Dosyaları (*.json)"
        )
        if not dosya:
            return

        self._proje_dosyasi = dosya
        self._kaydet()

    def closeEvent(self, event: QCloseEvent):
        """Kapanmadan önce kaydedilmemiş değişiklik kontrolü."""
        if self._kayit_gerekli:
            cevap = QMessageBox.question(
                self,
                "Çıkış",
                "Kaydedilmemiş değişiklikler var. Çıkmak istiyor musunuz?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if cevap == QMessageBox.StandardButton.Save:
                self._kaydet()
                event.accept()
            elif cevap == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
