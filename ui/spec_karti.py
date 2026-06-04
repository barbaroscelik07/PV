"""
PV-DOC — Spec Kartı Widget (Modül 2)
Kullanıcı tüm spesifikasyonları bu ekranda girer.
Sekmeler: Çekirdek Tablet | Film Tablet | Etken Madde 1..N
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QFrame,
    QScrollArea, QTabWidget, QGroupBox, QComboBox,
    QSizePolicy, QFileDialog, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.models import (
    ProjeVerisi, EtkenMaddeSpek, ImpuriteSpek,
    CekirdekTabletSpek, FilmTabletSpek, UrunFormu
)
from ui.stiller import (
    RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    RENK_YESIL, RENK_YESIL_BG
)


class HesapEtiket(QLabel):
    """Otomatik hesaplanan değeri gösteren etiket."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            font-size: 11px;
            color: {RENK_PRIMARY};
            background-color: {RENK_PRIMARY_ACIK};
            border-radius: 4px;
            padding: 1px 7px;
        """)


class TestSatiri(QFrame):
    """
    Tek bir test için satır düzeni:
    [Test Adı] [Spesifikasyon giriş alanları] [IPK cb] [* cb]
    """

    degisti = pyqtSignal()

    def __init__(
        self,
        test_adi: str,
        spek_widget: QWidget,
        ipk_goster: bool = True,
        sb_goster: bool = True,
        raf_goster: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.setStyleSheet(f"background: transparent; border-bottom: 1px solid {RENK_KENARLIK};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        lbl = QLabel(test_adi)
        lbl.setStyleSheet(f"font-size: 11px; color: {RENK_YAZI_BIRINCIL};")
        lbl.setFixedWidth(170)
        layout.addWidget(lbl)

        layout.addWidget(spek_widget, 1)

        # Checkbox'lar
        self.cb_ipk = None
        self.cb_sb = None
        self.cb_raf = None

        for goster, attr, genislik, renk in [
            (ipk_goster, "cb_ipk", 52, RENK_PRIMARY),
            (sb_goster, "cb_sb", 68, RENK_PRIMARY),
            (raf_goster, "cb_raf", 68, RENK_PRIMARY),
        ]:
            cb = QCheckBox()
            cb.setStyleSheet(f"""
                QCheckBox::indicator {{
                    width: 14px; height: 14px;
                    border: 1px solid {RENK_KENARLIK};
                    border-radius: 3px;
                    background: {RENK_BG_BIRINCIL};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {renk};
                    border-color: {renk};
                }}
            """)
            cb.stateChanged.connect(self.degisti)

            container = QWidget()
            container.setFixedWidth(genislik)
            cl = QHBoxLayout(container)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(cb)

            if not goster:
                container.setVisible(False)
            setattr(self, attr, cb)
            layout.addWidget(container)


class AgirlikSatiri(QFrame):
    """Ortalama ağırlık için özel giriş — hedef ve tolerans, limitler otomatik."""

    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.input_hedef = QLineEdit()
        self.input_hedef.setPlaceholderText("Hedef (mg)")
        self.input_hedef.setFixedWidth(90)
        layout.addWidget(self.input_hedef)

        layout.addWidget(QLabel("mg  ±"))
        self.input_tol = QLineEdit("5.0")
        self.input_tol.setFixedWidth(44)
        layout.addWidget(self.input_tol)
        layout.addWidget(QLabel("%"))

        self.lbl_hesap = HesapEtiket("→ limit hesapla")
        layout.addWidget(self.lbl_hesap)
        layout.addStretch()

        self.input_hedef.textChanged.connect(self._hesapla)
        self.input_tol.textChanged.connect(self._hesapla)
        self.input_hedef.textChanged.connect(self.degisti)
        self.input_tol.textChanged.connect(self.degisti)

    def _hesapla(self):
        try:
            h = float(self.input_hedef.text())
            t = float(self.input_tol.text())
            alt = round(h * (1 - t / 100), 2)
            ust = round(h * (1 + t / 100), 2)
            self.lbl_hesap.setText(f"→ {alt} – {ust} mg")
        except (ValueError, ZeroDivisionError):
            self.lbl_hesap.setText("→ limit hesapla")


class MiktarSatiri(QFrame):
    """Miktar tayini giriş satırı."""

    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.input_hedef = QLineEdit()
        self.input_hedef.setPlaceholderText("Hedef")
        self.input_hedef.setFixedWidth(70)
        layout.addWidget(self.input_hedef)

        self.combo_birim = QComboBox()
        self.combo_birim.addItems(["mg/ftb", "mg/tb", "mg/kap", "%"])
        self.combo_birim.setFixedWidth(70)
        layout.addWidget(self.combo_birim)

        layout.addWidget(QLabel("±"))
        self.input_tol = QLineEdit("5.0")
        self.input_tol.setFixedWidth(40)
        layout.addWidget(self.input_tol)
        layout.addWidget(QLabel("%"))

        self.lbl_hesap = HesapEtiket("→ limit hesapla")
        layout.addWidget(self.lbl_hesap)

        lbl_raf = QLabel("(Raf ömrü: ±%10 otomatik)")
        lbl_raf.setStyleSheet(f"font-size: 9px; color: {RENK_YAZI_UCUNCUL};")
        layout.addWidget(lbl_raf)
        layout.addStretch()

        self.input_hedef.textChanged.connect(self._hesapla)
        self.input_tol.textChanged.connect(self._hesapla)
        self.input_hedef.textChanged.connect(self.degisti)
        self.input_tol.textChanged.connect(self.degisti)
        self.combo_birim.currentIndexChanged.connect(self.degisti)

    def _hesapla(self):
        try:
            h = float(self.input_hedef.text())
            t = float(self.input_tol.text())
            alt = round(h * (1 - t / 100), 3)
            ust = round(h * (1 + t / 100), 3)
            self.lbl_hesap.setText(f"→ {alt} – {ust}")
        except (ValueError, ZeroDivisionError):
            self.lbl_hesap.setText("→ limit hesapla")


class ImpuriteSatiri(QFrame):
    """Tek bir impürite için giriş satırı."""

    silindi = pyqtSignal(object)
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        self.input_ad = QLineEdit()
        self.input_ad.setPlaceholderText("İmpürite adı")
        self.input_ad.setFixedWidth(150)
        layout.addWidget(self.input_ad)

        self.combo_tip = QComboBox()
        self.combo_tip.addItems(["Maks. %", "Min. %"])
        self.combo_tip.setFixedWidth(80)
        layout.addWidget(self.combo_tip)

        self.input_deger = QLineEdit()
        self.input_deger.setPlaceholderText("Değer")
        self.input_deger.setFixedWidth(60)
        layout.addWidget(self.input_deger)
        layout.addWidget(QLabel("%"))

        layout.addStretch()

        lbl_cb = QLabel("IPK")
        lbl_cb.setStyleSheet(f"font-size: 9px; color: {RENK_YAZI_UCUNCUL};")
        layout.addWidget(lbl_cb)
        self.cb_ipk = QCheckBox()
        layout.addWidget(self.cb_ipk)

        lbl_sb = QLabel("SB")
        lbl_sb.setStyleSheet(f"font-size: 9px; color: {RENK_YAZI_UCUNCUL};")
        layout.addWidget(lbl_sb)
        self.cb_sb = QCheckBox()
        self.cb_sb.setChecked(True)
        layout.addWidget(self.cb_sb)

        lbl_raf = QLabel("Raf")
        lbl_raf.setStyleSheet(f"font-size: 9px; color: {RENK_YAZI_UCUNCUL};")
        layout.addWidget(lbl_raf)
        self.cb_raf = QCheckBox()
        self.cb_raf.setChecked(True)
        layout.addWidget(self.cb_raf)

        btn_sil = QPushButton("✕")
        btn_sil.setFixedSize(22, 22)
        btn_sil.setStyleSheet(f"""
            QPushButton {{
                border: none; background: transparent;
                color: {RENK_YAZI_UCUNCUL}; font-size: 11px;
            }}
            QPushButton:hover {{ color: #A32D2D; background: #FCEBEB; border-radius: 3px; }}
        """)
        btn_sil.clicked.connect(lambda: self.silindi.emit(self))
        layout.addWidget(btn_sil)

        for w in [self.input_ad, self.input_deger, self.combo_tip,
                  self.cb_ipk, self.cb_sb, self.cb_raf]:
            if hasattr(w, 'textChanged'):
                w.textChanged.connect(self.degisti)
            elif hasattr(w, 'stateChanged'):
                w.stateChanged.connect(self.degisti)
            elif hasattr(w, 'currentIndexChanged'):
                w.currentIndexChanged.connect(self.degisti)

    def to_model(self) -> ImpuriteSpek:
        return ImpuriteSpek(
            ad=self.input_ad.text().strip(),
            limit_tipi=self.combo_tip.currentText(),
            deger=self.input_deger.text().strip(),
            ipk=self.cb_ipk.isChecked(),
            serbest_birakma=self.cb_sb.isChecked(),
            raf_omru=self.cb_raf.isChecked(),
        )

    def from_model(self, m: ImpuriteSpek):
        self.input_ad.setText(m.ad)
        idx = self.combo_tip.findText(m.limit_tipi)
        if idx >= 0:
            self.combo_tip.setCurrentIndex(idx)
        self.input_deger.setText(m.deger)
        self.cb_ipk.setChecked(m.ipk)
        self.cb_sb.setChecked(m.serbest_birakma)
        self.cb_raf.setChecked(m.raf_omru)


class CekirdekTabletSekmesi(QScrollArea):
    """Çekirdek tablet fiziksel spesifikasyon sekmesi."""

    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)

        icerik = QWidget()
        layout = QVBoxLayout(icerik)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Sütun başlıkları
        layout.addWidget(self._baslik_satiri())

        # Test satırları
        # Ortalama Ağırlık
        self.agirlik_w = AgirlikSatiri()
        self.agirlik_w.degisti.connect(self.degisti)
        self.row_agirlik = TestSatiri("Ortalama Ağırlık", self.agirlik_w)
        self.row_agirlik.degisti.connect(self.degisti)
        self.row_agirlik.cb_ipk.setChecked(True)
        self.row_agirlik.cb_sb.setChecked(True)
        self.row_agirlik.cb_raf.setChecked(True)
        layout.addWidget(self.row_agirlik)

        # Ağırlık Tekdüzeliği (otomatik)
        at_lbl = QLabel("Ağırlık Tekdüzeliği limitleri ort. ağırlıktan otomatik hesaplanır")
        at_lbl.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_UCUNCUL}; font-style: italic;")
        self.row_at = TestSatiri("Ağırlık Tekdüzeliği", at_lbl)
        self.row_at.degisti.connect(self.degisti)
        self.row_at.cb_ipk.setChecked(True)
        self.row_at.cb_sb.setChecked(True)
        self.row_at.cb_raf.setChecked(True)
        layout.addWidget(self.row_at)

        # Kalınlık
        self.kalinlik_w = self._aralik_widget("Hedef mm", "Alt", "Üst")
        self.row_kalinlik = TestSatiri("Kalınlık", self.kalinlik_w)
        self.row_kalinlik.degisti.connect(self.degisti)
        self.row_kalinlik.cb_ipk.setChecked(True)
        self.row_kalinlik.cb_sb.setChecked(True)
        layout.addWidget(self.row_kalinlik)

        # Çap
        self.cap_w = self._aralik_widget("Hedef mm", "Alt", "Üst")
        self.row_cap = TestSatiri("Çap", self.cap_w)
        self.row_cap.degisti.connect(self.degisti)
        self.row_cap.cb_ipk.setChecked(True)
        self.row_cap.cb_sb.setChecked(True)
        layout.addWidget(self.row_cap)

        # Sertlik
        self.sertlik_w = self._min_widget("Min. kP")
        self.row_sertlik = TestSatiri("Sertlik", self.sertlik_w)
        self.row_sertlik.degisti.connect(self.degisti)
        self.row_sertlik.cb_ipk.setChecked(True)
        self.row_sertlik.cb_sb.setChecked(True)
        layout.addWidget(self.row_sertlik)

        # Aşınma
        self.asinma_w = self._max_widget("Maks. %")
        self.row_asinma = TestSatiri("Aşınma (Friabilite)", self.asinma_w)
        self.row_asinma.degisti.connect(self.degisti)
        self.row_asinma.cb_ipk.setChecked(True)
        self.row_asinma.cb_sb.setChecked(True)
        layout.addWidget(self.row_asinma)

        # Dağılma (sabit 15 dk)
        dagılma_lbl = QLabel("Maksimum 15 dakika  (Tablet Baskı — sabit)")
        dagılma_lbl.setStyleSheet(f"font-size: 11px; color: {RENK_YAZI_IKINCIL};")
        self.row_dagılma = TestSatiri("Dağılma", dagılma_lbl)
        self.row_dagılma.degisti.connect(self.degisti)
        self.row_dagılma.cb_ipk.setChecked(True)
        self.row_dagılma.cb_sb.setChecked(True)
        layout.addWidget(self.row_dagılma)

        layout.addStretch()
        self.setWidget(icerik)

    def _baslik_satiri(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {RENK_BG_IKINCIL};
            border-bottom: 1px solid {RENK_KENARLIK};
            border-radius: 0;
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)

        lbl_test = QLabel("Test")
        lbl_test.setFixedWidth(170)
        lbl_test.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {RENK_YAZI_IKINCIL};")
        layout.addWidget(lbl_test)

        lbl_spek = QLabel("Spesifikasyon")
        lbl_spek.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {RENK_YAZI_IKINCIL};")
        layout.addWidget(lbl_spek, 1)

        for lbl_metin, genislik in [("IPK", 52), ("Serbest B.", 68), ("Raf Ömrü", 68)]:
            lbl = QLabel(lbl_metin)
            lbl.setFixedWidth(genislik)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {RENK_YAZI_IKINCIL};")
            layout.addWidget(lbl)

        return frame

    def _aralik_widget(self, ph1, ph2, ph3) -> QWidget:
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        for ph in [ph1, ph2, ph3]:
            inp = QLineEdit()
            inp.setPlaceholderText(ph)
            inp.setFixedWidth(70)
            l.addWidget(inp)
        l.addStretch()
        return w

    def _min_widget(self, ph) -> QWidget:
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        l.addWidget(QLabel("Min."))
        inp = QLineEdit()
        inp.setPlaceholderText(ph)
        inp.setFixedWidth(80)
        l.addWidget(inp)
        l.addStretch()
        return w

    def _max_widget(self, ph) -> QWidget:
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        l.addWidget(QLabel("Maks."))
        inp = QLineEdit()
        inp.setPlaceholderText(ph)
        inp.setFixedWidth(80)
        l.addWidget(inp)
        l.addStretch()
        return w

    def to_model(self) -> CekirdekTabletSpek:
        m = CekirdekTabletSpek()
        m.ort_agirlik_hedef_mg = self.agirlik_w.input_hedef.text().strip()
        m.ort_agirlik_tolerans = self.agirlik_w.input_tol.text().strip()
        m.ort_agirlik_ipk = self.row_agirlik.cb_ipk.isChecked()
        m.ort_agirlik_sb = self.row_agirlik.cb_sb.isChecked()
        m.ort_agirlik_raf = self.row_agirlik.cb_raf.isChecked()
        m.at_ipk = self.row_at.cb_ipk.isChecked()
        m.at_sb = self.row_at.cb_sb.isChecked()
        m.at_raf = self.row_at.cb_raf.isChecked()

        kal_inputs = self._get_inputs(self.kalinlik_w)
        if len(kal_inputs) >= 3:
            m.kalinlik_hedef = kal_inputs[0].text().strip()
            m.kalinlik_alt = kal_inputs[1].text().strip()
            m.kalinlik_ust = kal_inputs[2].text().strip()
        m.kalinlik_ipk = self.row_kalinlik.cb_ipk.isChecked()
        m.kalinlik_sb = self.row_kalinlik.cb_sb.isChecked()
        m.kalinlik_raf = self.row_kalinlik.cb_raf.isChecked()

        cap_inputs = self._get_inputs(self.cap_w)
        if len(cap_inputs) >= 3:
            m.cap_hedef = cap_inputs[0].text().strip()
            m.cap_alt = cap_inputs[1].text().strip()
            m.cap_ust = cap_inputs[2].text().strip()
        m.cap_ipk = self.row_cap.cb_ipk.isChecked()
        m.cap_sb = self.row_cap.cb_sb.isChecked()
        m.cap_raf = self.row_cap.cb_raf.isChecked()

        sert_inputs = self._get_inputs(self.sertlik_w)
        if sert_inputs:
            m.sertlik_min = sert_inputs[0].text().strip()
        m.sertlik_ipk = self.row_sertlik.cb_ipk.isChecked()
        m.sertlik_sb = self.row_sertlik.cb_sb.isChecked()

        asin_inputs = self._get_inputs(self.asinma_w)
        if asin_inputs:
            m.asinma_max = asin_inputs[0].text().strip()
        m.asinma_ipk = self.row_asinma.cb_ipk.isChecked()
        m.asinma_sb = self.row_asinma.cb_sb.isChecked()

        m.dagılma_ipk = self.row_dagılma.cb_ipk.isChecked()
        m.dagılma_sb = self.row_dagılma.cb_sb.isChecked()
        m.dagılma_raf = self.row_dagılma.cb_raf.isChecked()
        return m

    def from_model(self, m: CekirdekTabletSpek):
        self.agirlik_w.input_hedef.setText(m.ort_agirlik_hedef_mg)
        self.agirlik_w.input_tol.setText(m.ort_agirlik_tolerans)
        self.row_agirlik.cb_ipk.setChecked(m.ort_agirlik_ipk)
        self.row_agirlik.cb_sb.setChecked(m.ort_agirlik_sb)
        self.row_agirlik.cb_raf.setChecked(m.ort_agirlik_raf)
        self.row_at.cb_ipk.setChecked(m.at_ipk)
        self.row_at.cb_sb.setChecked(m.at_sb)
        self.row_at.cb_raf.setChecked(m.at_raf)

        kal_inputs = self._get_inputs(self.kalinlik_w)
        if len(kal_inputs) >= 3:
            kal_inputs[0].setText(m.kalinlik_hedef)
            kal_inputs[1].setText(m.kalinlik_alt)
            kal_inputs[2].setText(m.kalinlik_ust)
        self.row_kalinlik.cb_ipk.setChecked(m.kalinlik_ipk)
        self.row_kalinlik.cb_sb.setChecked(m.kalinlik_sb)
        self.row_kalinlik.cb_raf.setChecked(m.kalinlik_raf)

        cap_inputs = self._get_inputs(self.cap_w)
        if len(cap_inputs) >= 3:
            cap_inputs[0].setText(m.cap_hedef)
            cap_inputs[1].setText(m.cap_alt)
            cap_inputs[2].setText(m.cap_ust)
        self.row_cap.cb_ipk.setChecked(m.cap_ipk)
        self.row_cap.cb_sb.setChecked(m.cap_sb)
        self.row_cap.cb_raf.setChecked(m.cap_raf)

        sert_inputs = self._get_inputs(self.sertlik_w)
        if sert_inputs:
            sert_inputs[0].setText(m.sertlik_min)
        self.row_sertlik.cb_ipk.setChecked(m.sertlik_ipk)
        self.row_sertlik.cb_sb.setChecked(m.sertlik_sb)

        asin_inputs = self._get_inputs(self.asinma_w)
        if asin_inputs:
            asin_inputs[0].setText(m.asinma_max)
        self.row_asinma.cb_ipk.setChecked(m.asinma_ipk)
        self.row_asinma.cb_sb.setChecked(m.asinma_sb)

        self.row_dagılma.cb_ipk.setChecked(m.dagılma_ipk)
        self.row_dagılma.cb_sb.setChecked(m.dagılma_sb)
        self.row_dagılma.cb_raf.setChecked(m.dagılma_raf)

    def _get_inputs(self, widget: QWidget) -> list:
        return [c for c in widget.findChildren(QLineEdit)]


class FilmTabletSekmesi(QScrollArea):
    """Film tablet fiziksel spesifikasyon sekmesi."""

    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)

        icerik = QWidget()
        layout = QVBoxLayout(icerik)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(self._baslik_satiri())

        # Görünüş
        self.input_gorunus = QLineEdit()
        self.input_gorunus.setPlaceholderText("Örn: Pembe, oblong, bikonveks film kaplı tabletler")
        self.row_gorunus = TestSatiri("Görünüş", self.input_gorunus, ipk_goster=True, sb_goster=True, raf_goster=True)
        self.row_gorunus.cb_ipk.setChecked(True)
        self.row_gorunus.cb_sb.setChecked(True)
        self.row_gorunus.cb_raf.setChecked(True)
        layout.addWidget(self.row_gorunus)

        # Ortalama Ağırlık
        self.agirlik_w = AgirlikSatiri()
        self.agirlik_w.degisti.connect(self.degisti)
        self.row_agirlik = TestSatiri("Ortalama Ağırlık", self.agirlik_w)
        self.row_agirlik.cb_ipk.setChecked(True)
        self.row_agirlik.cb_sb.setChecked(True)
        self.row_agirlik.cb_raf.setChecked(True)
        layout.addWidget(self.row_agirlik)

        # Ağırlık Tekdüzeliği
        at_lbl = QLabel("Film tablet ağırlığından otomatik hesaplanır")
        at_lbl.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_UCUNCUL}; font-style: italic;")
        self.row_at = TestSatiri("Ağırlık Tekdüzeliği", at_lbl)
        self.row_at.cb_ipk.setChecked(True)
        self.row_at.cb_sb.setChecked(True)
        self.row_at.cb_raf.setChecked(True)
        layout.addWidget(self.row_at)

        # Dağılma (sabit 30 dk)
        dagılma_lbl = QLabel("Maksimum 30 dakika  (Film Kaplama — sabit)")
        dagılma_lbl.setStyleSheet(f"font-size: 11px; color: {RENK_YAZI_IKINCIL};")
        self.row_dagılma = TestSatiri("Dağılma", dagılma_lbl)
        self.row_dagılma.cb_ipk.setChecked(True)
        self.row_dagılma.cb_sb.setChecked(True)
        layout.addWidget(self.row_dagılma)

        layout.addStretch()
        self.setWidget(icerik)

    def _baslik_satiri(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"background: {RENK_BG_IKINCIL}; border-bottom: 1px solid {RENK_KENARLIK};")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        lbl = QLabel("Test")
        lbl.setFixedWidth(170)
        lbl.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {RENK_YAZI_IKINCIL};")
        layout.addWidget(lbl)
        lbl2 = QLabel("Spesifikasyon")
        lbl2.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {RENK_YAZI_IKINCIL};")
        layout.addWidget(lbl2, 1)
        for txt, w in [("IPK", 52), ("Serbest B.", 68), ("Raf Ömrü", 68)]:
            lb = QLabel(txt)
            lb.setFixedWidth(w)
            lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lb.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {RENK_YAZI_IKINCIL};")
            layout.addWidget(lb)
        return frame

    def to_model(self) -> FilmTabletSpek:
        m = FilmTabletSpek()
        m.gorunus = self.input_gorunus.text().strip()
        m.ort_agirlik_hedef_mg = self.agirlik_w.input_hedef.text().strip()
        m.ort_agirlik_tolerans = self.agirlik_w.input_tol.text().strip()
        m.ort_agirlik_ipk = self.row_agirlik.cb_ipk.isChecked()
        m.ort_agirlik_sb = self.row_agirlik.cb_sb.isChecked()
        m.ort_agirlik_raf = self.row_agirlik.cb_raf.isChecked()
        m.at_ipk = self.row_at.cb_ipk.isChecked()
        m.at_sb = self.row_at.cb_sb.isChecked()
        m.at_raf = self.row_at.cb_raf.isChecked()
        m.dagılma_ipk = self.row_dagılma.cb_ipk.isChecked()
        m.dagılma_sb = self.row_dagılma.cb_sb.isChecked()
        m.dagılma_raf = self.row_dagılma.cb_raf.isChecked()
        return m

    def from_model(self, m: FilmTabletSpek):
        self.input_gorunus.setText(m.gorunus)
        self.agirlik_w.input_hedef.setText(m.ort_agirlik_hedef_mg)
        self.agirlik_w.input_tol.setText(m.ort_agirlik_tolerans)
        self.row_agirlik.cb_ipk.setChecked(m.ort_agirlik_ipk)
        self.row_agirlik.cb_sb.setChecked(m.ort_agirlik_sb)
        self.row_agirlik.cb_raf.setChecked(m.ort_agirlik_raf)
        self.row_at.cb_ipk.setChecked(m.at_ipk)
        self.row_at.cb_sb.setChecked(m.at_sb)
        self.row_at.cb_raf.setChecked(m.at_raf)
        self.row_dagılma.cb_ipk.setChecked(m.dagılma_ipk)
        self.row_dagılma.cb_sb.setChecked(m.dagılma_sb)
        self.row_dagılma.cb_raf.setChecked(m.dagılma_raf)


class EtkenMaddeSekmesi(QScrollArea):
    """Tek bir etken madde için analitik spesifikasyon sekmesi."""

    degisti = pyqtSignal()

    def __init__(self, em_no: int, em_ad: str = "", parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._impurite_satirlari: list[ImpuriteSatiri] = []

        icerik = QWidget()
        self._ana_layout = QVBoxLayout(icerik)
        self._ana_layout.setContentsMargins(12, 12, 12, 12)
        self._ana_layout.setSpacing(8)

        # Görünüş
        self.input_gorunus = QLineEdit()
        self.input_gorunus.setPlaceholderText("Etken madde görünüş tanımı")
        self.input_gorunus.textChanged.connect(self.degisti)
        gorunus_satiri = self._etiket_satiri("Görünüş", self.input_gorunus)
        self._ana_layout.addWidget(gorunus_satiri)

        # Sütun başlığı
        self._ana_layout.addWidget(self._baslik_satiri())

        # Bilgi amaçlı testler — attribute adları açıkça tanımlanır
        for test_adi, attr_adi in [
            ("Elek Testi", "row_elek"),
            ("Bulk Dansite", "row_bulk"),
            ("Tap Dansite", "row_tap"),
        ]:
            lbl = QLabel("Bilgi amaçlıdır.  (PVR'da kullanıcı manuel girer)")
            lbl.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_UCUNCUL}; font-style: italic;")
            row = TestSatiri(test_adi, lbl, ipk_goster=True, sb_goster=False, raf_goster=False)
            row.cb_ipk.setChecked(True)
            row.degisti.connect(self.degisti)
            setattr(self, attr_adi, row)
            self._ana_layout.addWidget(row)

        # Karışım Tekdüzeliği
        self.kt_w = self._aralik_widget("Alt (%)", "Üst (%)")
        self.row_kt = TestSatiri("Karışım Tekdüzeliği", self.kt_w, ipk_goster=True, sb_goster=True, raf_goster=True)
        self.row_kt.degisti.connect(self.degisti)
        self._ana_layout.addWidget(self.row_kt)

        # Miktar Tayini
        self.miktar_w = MiktarSatiri()
        self.miktar_w.degisti.connect(self.degisti)
        miktar_container = QFrame()
        miktar_layout = QHBoxLayout(miktar_container)
        miktar_layout.setContentsMargins(8, 4, 8, 4)
        miktar_layout.setSpacing(8)
        miktar_lbl = QLabel("Miktar Tayini")
        miktar_lbl.setStyleSheet(f"font-size: 11px; color: {RENK_YAZI_BIRINCIL};")
        miktar_lbl.setFixedWidth(170)
        miktar_layout.addWidget(miktar_lbl)
        miktar_layout.addWidget(self.miktar_w, 1)

        self.cb_miktar_sb = QCheckBox()
        self.cb_miktar_sb.setChecked(True)
        self.cb_miktar_raf = QCheckBox()
        self.cb_miktar_raf.setChecked(True)
        ipk_note = QLabel("—")
        ipk_note.setFixedWidth(52)
        ipk_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ipk_note.setStyleSheet(f"color: {RENK_YAZI_UCUNCUL}; font-size: 10px;")
        miktar_layout.addWidget(ipk_note)

        for cb, w in [(self.cb_miktar_sb, 68), (self.cb_miktar_raf, 68)]:
            c = QWidget()
            c.setFixedWidth(w)
            cl = QHBoxLayout(c)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(cb)
            miktar_layout.addWidget(c)

        miktar_container.setStyleSheet(f"border-bottom: 1px solid {RENK_KENARLIK};")
        self._ana_layout.addWidget(miktar_container)

        # Dissolüsyon
        self.dis_w = self._dis_widget()
        self.row_dis = TestSatiri("Dissolüsyon (Q)", self.dis_w, ipk_goster=False, sb_goster=True, raf_goster=True)
        self.row_dis.cb_sb.setChecked(True)
        self.row_dis.cb_raf.setChecked(True)
        self.row_dis.degisti.connect(self.degisti)
        self._ana_layout.addWidget(self.row_dis)

        # İmpüriteler grubu
        imp_baslik = QFrame()
        imp_baslik.setStyleSheet(f"""
            background-color: {RENK_PRIMARY_ACIK};
            border-radius: 6px;
            padding: 2px;
        """)
        imp_baslik_l = QHBoxLayout(imp_baslik)
        imp_baslik_l.setContentsMargins(8, 4, 8, 4)
        imp_baslik_lbl = QLabel("İlgili Bileşikler (İmpüriteler)")
        imp_baslik_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {RENK_PRIMARY_KOYU};")
        imp_baslik_l.addWidget(imp_baslik_lbl)
        imp_baslik_l.addStretch()
        self._ana_layout.addWidget(imp_baslik)

        # İmpürite başlık satırı
        imp_hdr = QFrame()
        imp_hdr_l = QHBoxLayout(imp_hdr)
        imp_hdr_l.setContentsMargins(4, 2, 4, 2)
        for txt, w in [("İmpürite Adı", 150), ("Tip", 80), ("Değer", 70),
                        ("", 10), ("IPK", 30), ("SB", 30), ("Raf", 30), ("", 30)]:
            lb = QLabel(txt)
            lb.setFixedWidth(w)
            lb.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {RENK_YAZI_UCUNCUL};")
            imp_hdr_l.addWidget(lb)
        imp_hdr_l.addStretch()
        self._ana_layout.addWidget(imp_hdr)

        # İmpürite satırları container
        self._imp_container = QWidget()
        self._imp_layout = QVBoxLayout(self._imp_container)
        self._imp_layout.setContentsMargins(0, 0, 0, 0)
        self._imp_layout.setSpacing(2)
        self._ana_layout.addWidget(self._imp_container)

        btn_imp_ekle = QPushButton("+ İmpürite Ekle")
        btn_imp_ekle.setStyleSheet(f"""
            QPushButton {{
                border: 1px dashed {RENK_PRIMARY};
                border-radius: 6px;
                padding: 4px 10px;
                background: transparent;
                color: {RENK_PRIMARY};
                font-size: 11px;
            }}
            QPushButton:hover {{ background: {RENK_PRIMARY_ACIK}; }}
        """)
        btn_imp_ekle.clicked.connect(self._imp_ekle)
        self._ana_layout.addWidget(btn_imp_ekle)

        # Mikrobiyolojik
        mikro_lbl = QLabel("Sabit değerler: Aerobik ≤10³, Küf-Maya ≤10², E.coli 0 cfu/g")
        mikro_lbl.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_UCUNCUL}; font-style: italic;")
        self.row_mikro = TestSatiri("Mikrobiyolojik Kontrol", mikro_lbl, ipk_goster=False, sb_goster=True, raf_goster=True)
        self.row_mikro.cb_sb.setChecked(True)
        self.row_mikro.cb_raf.setChecked(True)
        self._ana_layout.addWidget(self.row_mikro)

        self._ana_layout.addStretch()
        self.setWidget(icerik)

    def _baslik_satiri(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"background: {RENK_BG_IKINCIL}; border-bottom: 1px solid {RENK_KENARLIK};")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        for txt, w, stretch in [("Test", 170, False), ("Spesifikasyon", 0, True),
                                  ("IPK", 52, False), ("Serbest B.", 68, False), ("Raf Ömrü", 68, False)]:
            lb = QLabel(txt)
            lb.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {RENK_YAZI_IKINCIL};")
            if w:
                lb.setFixedWidth(w)
            lb.setAlignment(Qt.AlignmentFlag.AlignCenter if not stretch else Qt.AlignmentFlag.AlignLeft)
            if stretch:
                layout.addWidget(lb, 1)
            else:
                layout.addWidget(lb)
        return frame

    def _etiket_satiri(self, etiket: str, widget: QWidget) -> QFrame:
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        lbl = QLabel(etiket)
        lbl.setFixedWidth(170)
        lbl.setStyleSheet(f"font-size: 11px; color: {RENK_YAZI_BIRINCIL};")
        layout.addWidget(lbl)
        layout.addWidget(widget, 1)
        return frame

    def _aralik_widget(self, ph1: str, ph2: str) -> QWidget:
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        l.addWidget(QLabel("% "))
        for ph in [ph1, ph2]:
            inp = QLineEdit()
            inp.setPlaceholderText(ph)
            inp.setFixedWidth(70)
            inp.textChanged.connect(self.degisti)
            l.addWidget(inp)
        l.addStretch()
        return w

    def _dis_widget(self) -> QWidget:
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        l.addWidget(QLabel("Min."))
        self.dis_q = QLineEdit()
        self.dis_q.setPlaceholderText("Min. Q (%)")
        self.dis_q.setFixedWidth(80)
        self.dis_q.textChanged.connect(self.degisti)
        l.addWidget(self.dis_q)
        l.addWidget(QLabel("(Q) —"))
        self.dis_sure = QLineEdit()
        self.dis_sure.setPlaceholderText("Süre (dk)")
        self.dis_sure.setFixedWidth(70)
        self.dis_sure.textChanged.connect(self.degisti)
        l.addWidget(self.dis_sure)
        l.addWidget(QLabel("dk"))
        l.addStretch()
        return w

    def _imp_ekle(self, model: ImpuriteSpek = None):
        satir = ImpuriteSatiri(self._imp_container)
        if model:
            satir.from_model(model)
        satir.silindi.connect(self._imp_sil)
        satir.degisti.connect(self.degisti)
        self._impurite_satirlari.append(satir)
        self._imp_layout.addWidget(satir)
        self.degisti.emit()

    def _imp_sil(self, satir: ImpuriteSatiri):
        self._impurite_satirlari.remove(satir)
        satir.deleteLater()
        self.degisti.emit()

    def to_model(self) -> EtkenMaddeSpek:
        m = EtkenMaddeSpek()
        m.gorunus = self.input_gorunus.text().strip()

        # Bilgi amaçlı testler IPK değerleri
        m.elek_ipk = self.row_elek.cb_ipk.isChecked()
        m.bulk_ipk = self.row_bulk.cb_ipk.isChecked()
        m.tap_ipk = self.row_tap.cb_ipk.isChecked()

        kt_inputs = self.kt_w.findChildren(QLineEdit)
        if len(kt_inputs) >= 2:
            m.kt_alt = kt_inputs[0].text().strip()
            m.kt_ust = kt_inputs[1].text().strip()
        m.kt_ipk = self.row_kt.cb_ipk.isChecked()
        m.kt_serbest_birakma = self.row_kt.cb_sb.isChecked()
        m.kt_raf_omru = self.row_kt.cb_raf.isChecked()

        m.miktar_hedef_mg = self.miktar_w.input_hedef.text().strip()
        m.miktar_birim = self.miktar_w.combo_birim.currentText()
        m.miktar_tolerans = self.miktar_w.input_tol.text().strip()
        m.miktar_serbest_birakma = self.cb_miktar_sb.isChecked()
        m.miktar_raf_omru = self.cb_miktar_raf.isChecked()

        m.dis_min_q = self.dis_q.text().strip()
        m.dis_sure_dk = self.dis_sure.text().strip()
        m.dis_serbest_birakma = self.row_dis.cb_sb.isChecked()
        m.dis_raf_omru = self.row_dis.cb_raf.isChecked()

        m.impuriteler = [s.to_model() for s in self._impurite_satirlari]
        m.mikrobiyolojik_dahil = self.row_mikro.cb_sb.isChecked()
        return m

    def from_model(self, m: EtkenMaddeSpek):
        self.input_gorunus.setText(m.gorunus)

        # Bilgi amaçlı testler IPK değerleri
        self.row_elek.cb_ipk.setChecked(m.elek_ipk)
        self.row_bulk.cb_ipk.setChecked(m.bulk_ipk)
        self.row_tap.cb_ipk.setChecked(m.tap_ipk)

        kt_inputs = self.kt_w.findChildren(QLineEdit)
        if len(kt_inputs) >= 2:
            kt_inputs[0].setText(m.kt_alt)
            kt_inputs[1].setText(m.kt_ust)
        self.row_kt.cb_ipk.setChecked(m.kt_ipk)
        self.row_kt.cb_sb.setChecked(m.kt_serbest_birakma)
        self.row_kt.cb_raf.setChecked(m.kt_raf_omru)

        self.miktar_w.input_hedef.setText(m.miktar_hedef_mg)
        idx = self.miktar_w.combo_birim.findText(m.miktar_birim)
        if idx >= 0:
            self.miktar_w.combo_birim.setCurrentIndex(idx)
        self.miktar_w.input_tol.setText(m.miktar_tolerans)
        self.cb_miktar_sb.setChecked(m.miktar_serbest_birakma)
        self.cb_miktar_raf.setChecked(m.miktar_raf_omru)

        self.dis_q.setText(m.dis_min_q)
        self.dis_sure.setText(m.dis_sure_dk)
        self.row_dis.cb_sb.setChecked(m.dis_serbest_birakma)
        self.row_dis.cb_raf.setChecked(m.dis_raf_omru)

        for s in self._impurite_satirlari[:]:
            s.deleteLater()
        self._impurite_satirlari.clear()
        for imp in m.impuriteler:
            self._imp_ekle(imp)

        self.row_mikro.cb_sb.setChecked(m.mikrobiyolojik_dahil)


class SpecKartiWidget(QWidget):
    """
    Ana spec kartı widget — tüm sekmeleri içerir.
    Kaydedilmemiş değişiklik varsa kullanıcıya uyarı verilir.
    """

    kaydedildi = pyqtSignal()
    degisti = pyqtSignal()

    def __init__(self, proje: ProjeVerisi, parent=None):
        super().__init__(parent)
        self._proje = proje
        self._degisiklik_var = False
        self._em_sekmeleri: list[EtkenMaddeSekmesi] = []
        self._setup_ui()
        self._yukle()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Üst araç çubuğu
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            background-color: {RENK_BG_BIRINCIL};
            border-bottom: 1px solid {RENK_KENARLIK};
        """)
        toolbar.setFixedHeight(46)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(16, 0, 16, 0)
        tb_layout.setSpacing(8)

        lbl = QLabel("Spec Kartı")
        lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {RENK_YAZI_BIRINCIL};")
        tb_layout.addWidget(lbl)

        sep = QLabel("/")
        sep.setStyleSheet(f"color: {RENK_KENARLIK};")
        tb_layout.addWidget(sep)

        self.lbl_alt = QLabel("Spesifikasyon tanımları")
        self.lbl_alt.setStyleSheet(f"font-size: 12px; color: {RENK_YAZI_IKINCIL};")
        tb_layout.addWidget(self.lbl_alt)

        tb_layout.addStretch()

        self.lbl_degisiklik = QLabel("")
        self.lbl_degisiklik.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_UCUNCUL};")
        tb_layout.addWidget(self.lbl_degisiklik)

        btn_sablon_yukle = QPushButton("Şablon Yükle")
        btn_sablon_yukle.setFixedHeight(30)
        btn_sablon_yukle.clicked.connect(self._sablon_yukle)
        tb_layout.addWidget(btn_sablon_yukle)

        btn_sablon_kaydet = QPushButton("Şablon Kaydet")
        btn_sablon_kaydet.setFixedHeight(30)
        btn_sablon_kaydet.clicked.connect(self._sablon_kaydet)
        tb_layout.addWidget(btn_sablon_kaydet)

        self.btn_kaydet = QPushButton("Kaydet")
        self.btn_kaydet.setObjectName("btnPrimary")
        self.btn_kaydet.setFixedHeight(30)
        self.btn_kaydet.setMinimumWidth(80)
        self.btn_kaydet.clicked.connect(self._kaydet)
        tb_layout.addWidget(self.btn_kaydet)

        layout.addWidget(toolbar)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {RENK_BG_BIRINCIL};
            }}
            QTabBar::tab {{
                border: 1px solid {RENK_KENARLIK};
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 6px 14px;
                font-size: 11px;
                color: {RENK_YAZI_IKINCIL};
                background: {RENK_BG_IKINCIL};
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {RENK_BG_BIRINCIL};
                color: {RENK_PRIMARY};
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background: {RENK_BG_BIRINCIL};
            }}
        """)
        layout.addWidget(self.tabs, 1)

    def _yukle(self):
        """Proje verisiyle tüm sekmeleri doldurur."""
        self.tabs.clear()
        self._em_sekmeleri.clear()

        # Çekirdek tablet sekmesi
        self.sekme_cekirdek = CekirdekTabletSekmesi()
        self.sekme_cekirdek.degisti.connect(self._on_degisti)
        self.sekme_cekirdek.from_model(self._proje.cekirdek_spek)

        # Film tablet sekmesi (sadece Film Tablet ve Kapsül+Film Tablet için)
        urun_formu = self._proje.urun_formu
        film_goster = urun_formu in [
            UrunFormu.FILM_TABLET.value,
            UrunFormu.KAPSUL_FILM_TABLET.value,
        ]

        if urun_formu != UrunFormu.KAPSUL.value:
            self.tabs.addTab(self.sekme_cekirdek, "Çekirdek Tablet")

        if film_goster:
            self.sekme_film = FilmTabletSekmesi()
            self.sekme_film.degisti.connect(self._on_degisti)
            self.sekme_film.from_model(self._proje.film_spek)
            self.tabs.addTab(self.sekme_film, "Film Tablet")

        # Etken madde sekmeleri
        for i, em in enumerate(self._proje.etken_maddeler):
            sekme = EtkenMaddeSekmesi(i + 1, em.ad)
            sekme.degisti.connect(self._on_degisti)
            sekme.from_model(em)
            self._em_sekmeleri.append(sekme)
            self.tabs.addTab(sekme, f"Etken Madde {i + 1}")

        if not self._proje.etken_maddeler:
            sekme = EtkenMaddeSekmesi(1)
            sekme.degisti.connect(self._on_degisti)
            self._em_sekmeleri.append(sekme)
            self.tabs.addTab(sekme, "Etken Madde 1")

        self._degisiklik_var = False
        self.lbl_degisiklik.setText("")

    def _on_degisti(self):
        self._degisiklik_var = True
        self.lbl_degisiklik.setText("● Kaydedilmemiş değişiklikler var")
        self.lbl_degisiklik.setStyleSheet(f"font-size: 10px; color: {RENK_PRIMARY};")
        self.degisti.emit()

    def _kaydet(self):
        """Spec kartı verilerini proje modeline yazar."""
        # Çekirdek tablet
        if self._proje.urun_formu != UrunFormu.KAPSUL.value:
            self._proje.cekirdek_spek = self.sekme_cekirdek.to_model()

        # Film tablet
        if hasattr(self, 'sekme_film'):
            self._proje.film_spek = self.sekme_film.to_model()

        # Etken maddeler
        for i, (sekme, em) in enumerate(zip(
            self._em_sekmeleri, self._proje.etken_maddeler
        )):
            model = sekme.to_model()
            model.ad = em.ad  # Adı proje modelinden koru
            self._proje.etken_maddeler[i] = model

        # Eğer yeni eklenmiş sekme varsa
        while len(self._em_sekmeleri) > len(self._proje.etken_maddeler):
            sekme = self._em_sekmeleri[len(self._proje.etken_maddeler)]
            model = sekme.to_model()
            self._proje.etken_maddeler.append(model)

        self._degisiklik_var = False
        self.lbl_degisiklik.setText("✓ Kaydedildi")
        self.lbl_degisiklik.setStyleSheet(f"font-size: 10px; color: {RENK_YESIL};")
        self.kaydedildi.emit()

    def _sablon_kaydet(self):
        """Spec kartını şablon olarak kaydeder."""
        dosya, _ = QFileDialog.getSaveFileName(
            self, "Şablonu Kaydet",
            f"{self._proje.urun_adi}_spec_sablonu.json",
            "JSON Dosyaları (*.json)"
        )
        if not dosya:
            return
        import json
        veri = {
            "cekirdek_spek": self._proje.cekirdek_spek.to_dict(),
            "film_spek": self._proje.film_spek.to_dict(),
            "etken_maddeler": [em.to_dict() for em in self._proje.etken_maddeler],
        }
        with open(dosya, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "Başarılı", "Şablon kaydedildi.")

    def _sablon_yukle(self):
        """Şablon dosyasından spec verisi yükler."""
        dosya, _ = QFileDialog.getOpenFileName(
            self, "Şablon Yükle", "", "JSON Dosyaları (*.json)"
        )
        if not dosya:
            return
        import json
        try:
            with open(dosya, "r", encoding="utf-8") as f:
                veri = json.load(f)
            if "cekirdek_spek" in veri:
                self._proje.cekirdek_spek = CekirdekTabletSpek.from_dict(veri["cekirdek_spek"])
            if "film_spek" in veri:
                self._proje.film_spek = FilmTabletSpek.from_dict(veri["film_spek"])
            self._yukle()
            QMessageBox.information(self, "Başarılı", "Şablon yüklendi.")
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Şablon yüklenemedi:\n{e}")

    def proje_guncelle(self, proje: ProjeVerisi):
        """Proje değiştiğinde sekmeleri yeniler."""
        self._proje = proje
        self._yukle()

    def degisiklik_var_mi(self) -> bool:
        return self._degisiklik_var
