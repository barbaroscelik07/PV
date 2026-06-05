"""
PV-DOC — Spec Kartı Widget (Modül 2)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QLineEdit, QCheckBox, QPushButton, QScrollArea,
    QTabWidget, QComboBox, QSizePolicy, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QKeyEvent

from core.models import (
    ProjeVerisi, EtkenMaddeSpek, EtkenMaddeAnalitikSpek,
    ImpuriteSpek, CekirdekTabletSpek, FilmTabletSpek,
    BulkKatmanSpek, UrunFormu, TabletYapisi
)
from ui.stiller import (
    RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    RENK_YESIL, RENK_YESIL_BG, FONT_AILESI
)


# ─── Yardımcı ────────────────────────────────────────────────────────────────

def _sek_baslik(metin: str) -> QFrame:
    f = QFrame()
    f.setStyleSheet(f"background:{RENK_PRIMARY_ACIK};border-radius:4px;")
    l = QHBoxLayout(f); l.setContentsMargins(10,4,10,4)
    lbl = QLabel(metin)
    lbl.setStyleSheet(f"font-size:11px;font-weight:bold;color:{RENK_PRIMARY_KOYU};")
    l.addWidget(lbl)
    return f


def _cb_stil() -> str:
    return f"""
        QCheckBox::indicator {{
            width:14px;height:14px;
            border:1px solid {RENK_KENARLIK};border-radius:3px;
            background:{RENK_BG_BIRINCIL};
        }}
        QCheckBox::indicator:checked {{
            background:{RENK_PRIMARY};border-color:{RENK_PRIMARY};
        }}
    """


class NoScrollComboBox(QComboBox):
    """Mouse tekerleğiyle değişmeyen ComboBox."""
    def wheelEvent(self, e):
        e.ignore()


# ─── TestSatiri ──────────────────────────────────────────────────────────────

class TestSatiri(QFrame):
    degisti = pyqtSignal()

    def __init__(self, test_adi, spek_widget, yildiz=True,
                 sb=False, ipk=False, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"border-bottom:1px solid {RENK_KENARLIK};background:transparent;")
        l = QHBoxLayout(self)
        l.setContentsMargins(8,3,8,3); l.setSpacing(8)

        lbl = QLabel(test_adi)
        lbl.setStyleSheet(f"font-size:11px;color:{RENK_YAZI_BIRINCIL};")
        lbl.setFixedWidth(180)
        l.addWidget(lbl)
        l.addWidget(spek_widget, 1)

        self.cb_yildiz = self.cb_sb = self.cb_ipk = None

        if yildiz:
            self.cb_yildiz = QCheckBox()
            self.cb_yildiz.setToolTip("* = Sadece proses validasyonunda yapılır")
            self.cb_yildiz.setStyleSheet(_cb_stil())
            self.cb_yildiz.stateChanged.connect(self.degisti)
            c = QWidget(); c.setFixedWidth(44)
            cl = QHBoxLayout(c); cl.setContentsMargins(0,0,0,0)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(self.cb_yildiz); l.addWidget(c)

        if sb:
            self.cb_sb = QCheckBox()
            self.cb_sb.setToolTip("Serbest Bırakma spesifikasyonuna dahil et")
            self.cb_sb.setStyleSheet(_cb_stil())
            self.cb_sb.stateChanged.connect(self.degisti)
            c = QWidget(); c.setFixedWidth(44)
            cl = QHBoxLayout(c); cl.setContentsMargins(0,0,0,0)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(self.cb_sb); l.addWidget(c)

        if ipk:
            self.cb_ipk = QCheckBox()
            self.cb_ipk.setToolTip("IPK testi kapsamına al")
            self.cb_ipk.setStyleSheet(_cb_stil())
            self.cb_ipk.stateChanged.connect(self.degisti)
            c = QWidget(); c.setFixedWidth(44)
            cl = QHBoxLayout(c); cl.setContentsMargins(0,0,0,0)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(self.cb_ipk); l.addWidget(c)


def _baslik_satiri(yildiz=True, sb=False, ipk=False) -> QFrame:
    f = QFrame()
    f.setStyleSheet(
        f"background:{RENK_BG_IKINCIL};border-bottom:1px solid {RENK_KENARLIK};")
    l = QHBoxLayout(f); l.setContentsMargins(8,4,8,4)

    lbl = QLabel("Test"); lbl.setFixedWidth(180)
    lbl.setStyleSheet(f"font-size:9px;font-weight:bold;color:{RENK_YAZI_IKINCIL};")
    l.addWidget(lbl)
    lbl2 = QLabel("Spesifikasyon")
    lbl2.setStyleSheet(f"font-size:9px;font-weight:bold;color:{RENK_YAZI_IKINCIL};")
    l.addWidget(lbl2, 1)

    for goster, txt, tt in [
        (yildiz, "*", "Sadece validasyonda"),
        (sb, "SB", "Serbest Bırakma"),
        (ipk, "IPK", "IPK testi"),
    ]:
        if goster:
            lb = QLabel(txt); lb.setFixedWidth(44)
            lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lb.setStyleSheet(f"font-size:9px;font-weight:bold;color:{RENK_PRIMARY};")
            lb.setToolTip(tt); l.addWidget(lb)
    return f


# ─── Ortak Widget'lar ─────────────────────────────────────────────────────────

class HesapEtiket(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            font-size:10px;color:{RENK_PRIMARY};
            background:{RENK_PRIMARY_ACIK};
            border-radius:3px;padding:1px 6px;
        """)


class AgirlikSatiri(QFrame):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(4)
        self.input_hedef = QLineEdit()
        self.input_hedef.setPlaceholderText("Hedef (mg)")
        self.input_hedef.setFixedWidth(90)
        l.addWidget(self.input_hedef)
        l.addWidget(QLabel("mg  ±"))
        self.input_tol = QLineEdit("5.0"); self.input_tol.setFixedWidth(44)
        l.addWidget(self.input_tol)
        l.addWidget(QLabel("%"))
        self.lbl = HesapEtiket("→ limit hesapla"); l.addWidget(self.lbl)
        l.addStretch()
        self.input_hedef.textChanged.connect(self._hesapla)
        self.input_tol.textChanged.connect(self._hesapla)
        self.input_hedef.textChanged.connect(self.degisti)
        self.input_tol.textChanged.connect(self.degisti)

    def _hesapla(self):
        try:
            h = float(self.input_hedef.text()); t = float(self.input_tol.text())
            self.lbl.setText(
                f"→ {round(h*(1-t/100),2)} – {round(h*(1+t/100),2)} mg")
        except ValueError:
            self.lbl.setText("→ limit hesapla")


class AgirlikTekduzeligiWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(6)
        for lbl_txt, a1, a2 in [("L1:", "l1_alt", "l1_ust"),
                                  ("L2:", "l2_alt", "l2_ust")]:
            lbl = QLabel(lbl_txt)
            lbl.setStyleSheet(
                f"font-size:10px;color:{RENK_YAZI_IKINCIL};font-weight:bold;")
            l.addWidget(lbl)
            i1 = QLineEdit(); i1.setPlaceholderText("Alt (mg)"); i1.setFixedWidth(72)
            i2 = QLineEdit(); i2.setPlaceholderText("Üst (mg)"); i2.setFixedWidth(72)
            l.addWidget(i1); l.addWidget(QLabel("–")); l.addWidget(i2)
            setattr(self, a1, i1); setattr(self, a2, i2)
            i1.textChanged.connect(self.degisti); i2.textChanged.connect(self.degisti)
            if a1 == "l1_alt":
                sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet(f"color:{RENK_KENARLIK};"); l.addWidget(sep)
        l.addStretch()


class KalinlikWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(4)
        l.addWidget(QLabel("Hedef:"))
        self.hedef = QLineEdit(); self.hedef.setPlaceholderText("mm"); self.hedef.setFixedWidth(60)
        l.addWidget(self.hedef)
        l.addWidget(QLabel("Alt:"))
        self.alt = QLineEdit(); self.alt.setPlaceholderText("mm"); self.alt.setFixedWidth(60)
        l.addWidget(self.alt)
        l.addWidget(QLabel("Üst:"))
        self.ust = QLineEdit(); self.ust.setPlaceholderText("mm"); self.ust.setFixedWidth(60)
        l.addWidget(self.ust)
        self.lbl = QLabel("(±0.5 oto.)")
        self.lbl.setStyleSheet(f"font-size:9px;color:{RENK_YAZI_UCUNCUL};")
        l.addWidget(self.lbl); l.addStretch()
        self.hedef.textChanged.connect(self._hesapla)
        self.alt.textChanged.connect(self.degisti); self.ust.textChanged.connect(self.degisti)

    def _hesapla(self, m):
        self.degisti.emit()
        try:
            h = float(m.replace(",", "."))
            self.alt.blockSignals(True); self.ust.blockSignals(True)
            self.alt.setText(str(round(h-0.5,2))); self.ust.setText(str(round(h+0.5,2)))
            self.alt.blockSignals(False); self.ust.blockSignals(False)
            self.lbl.setStyleSheet(f"font-size:9px;color:{RENK_PRIMARY};font-weight:bold;")
        except ValueError:
            self.lbl.setStyleSheet(f"font-size:9px;color:{RENK_YAZI_UCUNCUL};")


class CapWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(4)
        l.addWidget(QLabel("Hedef:"))
        self.hedef = QLineEdit(); self.hedef.setPlaceholderText("mm"); self.hedef.setFixedWidth(60)
        l.addWidget(self.hedef)
        l.addWidget(QLabel("Alt:"))
        self.alt = QLineEdit(); self.alt.setPlaceholderText("mm"); self.alt.setFixedWidth(60)
        l.addWidget(self.alt)
        l.addWidget(QLabel("Üst:"))
        self.ust = QLineEdit(); self.ust.setPlaceholderText("mm"); self.ust.setFixedWidth(60)
        l.addWidget(self.ust)
        self.lbl = QLabel("(±0.3 oto.)")
        self.lbl.setStyleSheet(f"font-size:9px;color:{RENK_YAZI_UCUNCUL};")
        l.addWidget(self.lbl); l.addStretch()
        self.hedef.textChanged.connect(self._hesapla)
        self.alt.textChanged.connect(self.degisti); self.ust.textChanged.connect(self.degisti)

    def _hesapla(self, m):
        self.degisti.emit()
        try:
            h = float(m.replace(",", "."))
            self.alt.blockSignals(True); self.ust.blockSignals(True)
            self.alt.setText(str(round(h-0.3,2))); self.ust.setText(str(round(h+0.3,2)))
            self.alt.blockSignals(False); self.ust.blockSignals(False)
            self.lbl.setStyleSheet(f"font-size:9px;color:{RENK_PRIMARY};font-weight:bold;")
        except ValueError:
            self.lbl.setStyleSheet(f"font-size:9px;color:{RENK_YAZI_UCUNCUL};")


class SertlikWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(4)
        l.addWidget(QLabel("Min."))
        self.input_min = QLineEdit(); self.input_min.setPlaceholderText("kP"); self.input_min.setFixedWidth(70)
        l.addWidget(self.input_min)
        l.addWidget(QLabel("Maks."))
        self.input_max = QLineEdit(); self.input_max.setPlaceholderText("kP (opsiyonel)"); self.input_max.setFixedWidth(100)
        l.addWidget(self.input_max); l.addStretch()
        self.input_min.textChanged.connect(self.degisti)
        self.input_max.textChanged.connect(self.degisti)


class MiktarWidget(QWidget):
    """Miktar Tayini — birim sadece mg, tolerans %."""
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(4)
        self.input_hedef = QLineEdit(); self.input_hedef.setPlaceholderText("Hedef"); self.input_hedef.setFixedWidth(80)
        l.addWidget(self.input_hedef)
        l.addWidget(QLabel("mg  ±"))
        self.input_tol = QLineEdit("5.0"); self.input_tol.setFixedWidth(40); l.addWidget(self.input_tol)
        l.addWidget(QLabel("%"))
        self.lbl = HesapEtiket("→ limit hesapla"); l.addWidget(self.lbl)
        lbl_raf = QLabel("(Raf: ±%10 oto.)")
        lbl_raf.setStyleSheet(f"font-size:9px;color:{RENK_YAZI_UCUNCUL};")
        l.addWidget(lbl_raf); l.addStretch()
        self.input_hedef.textChanged.connect(self._hesapla)
        self.input_tol.textChanged.connect(self._hesapla)
        self.input_hedef.textChanged.connect(self.degisti)
        self.input_tol.textChanged.connect(self.degisti)

    def _hesapla(self):
        try:
            h = float(self.input_hedef.text()); t = float(self.input_tol.text())
            self.lbl.setText(f"→ {round(h*(1-t/100),3)} – {round(h*(1+t/100),3)} mg")
        except ValueError:
            self.lbl.setText("→ limit hesapla")


class ImpuriteSatiri(QFrame):
    """İmpürite satırı — sadece Maks. değer, combo kaldırıldı."""
    silindi = pyqtSignal(object)
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self); l.setContentsMargins(4,2,4,2); l.setSpacing(6)
        self.input_ad = QLineEdit(); self.input_ad.setPlaceholderText("İmpürite adı"); self.input_ad.setFixedWidth(180)
        l.addWidget(self.input_ad)
        l.addWidget(QLabel("Maks."))
        self.input_deger = QLineEdit(); self.input_deger.setPlaceholderText("Değer"); self.input_deger.setFixedWidth(70)
        l.addWidget(self.input_deger)
        l.addWidget(QLabel("%")); l.addStretch()
        btn = QPushButton("✕"); btn.setFixedSize(22,22)
        btn.setToolTip("Bu impüriteyi sil")
        btn.setStyleSheet(f"""
            QPushButton{{
                border:1px solid {RENK_KENARLIK};
                background:{RENK_BG_IKINCIL};
                color:#A32D2D;font-size:11px;font-weight:bold;
                border-radius:3px;
            }}
            QPushButton:hover{{
                color:#A32D2D;background:#FCEBEB;
                border:1px solid #F09595;
            }}
        """)
        btn.clicked.connect(lambda: self.silindi.emit(self)); l.addWidget(btn)
        self.input_ad.textChanged.connect(self.degisti)
        self.input_deger.textChanged.connect(self.degisti)

        # Tab sırası
        QWidget.setTabOrder(self.input_ad, self.input_deger)

    def to_model(self) -> ImpuriteSpek:
        return ImpuriteSpek(
            ad=self.input_ad.text().strip(),
            limit_tipi="Maks. %",
            deger=self.input_deger.text().strip()
        )

    def from_model(self, m: ImpuriteSpek):
        self.input_ad.setText(m.ad)
        self.input_deger.setText(m.deger)


class DissolusyonWidget(QWidget):
    """Dissolüsyon — Q opsiyonel checkbox ile."""
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(4)
        l.addWidget(QLabel("Min."))
        self.input_q = QLineEdit("80.0"); self.input_q.setPlaceholderText("Min. (%)"); self.input_q.setFixedWidth(65)
        l.addWidget(self.input_q)
        l.addWidget(QLabel("%"))
        self.cb_q = QCheckBox("(Q)")
        self.cb_q.setChecked(True)
        self.cb_q.setToolTip("Q değeri kullan")
        self.cb_q.setStyleSheet(_cb_stil())
        l.addWidget(self.cb_q)
        l.addWidget(QLabel("—"))
        self.input_sure = QLineEdit("45"); self.input_sure.setPlaceholderText("Süre (dk)"); self.input_sure.setFixedWidth(55)
        l.addWidget(self.input_sure)
        l.addWidget(QLabel("dk")); l.addStretch()
        self.input_q.textChanged.connect(self.degisti)
        self.input_sure.textChanged.connect(self.degisti)
        self.cb_q.stateChanged.connect(self.degisti)

        QWidget.setTabOrder(self.input_q, self.input_sure)


# ─── Etken Madde Analitik Panel ───────────────────────────────────────────────

class EtkenAnalitikPanel(QWidget):
    degisti = pyqtSignal()

    def __init__(self, em_adi: str, dissolusyon_goster: bool = True,
                 kt_goster: bool = False, sb_goster: bool = False,
                 parent=None):
        super().__init__(parent)
        self._dissolusyon_goster = dissolusyon_goster
        self._kt_goster = kt_goster
        self._imp_satirlari: list[ImpuriteSatiri] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        layout.addWidget(_baslik_satiri(yildiz=True, sb=sb_goster, ipk=False))

        # Teşhis
        teshis_lbl = QLabel("Sabit: 'Standart ve numune alıkonma zamanı aynı olmalıdır.'")
        teshis_lbl.setStyleSheet(f"font-size:10px;color:{RENK_YAZI_UCUNCUL};font-style:italic;")
        self.row_teshis = TestSatiri("Teşhis", teshis_lbl,
                                     yildiz=True, sb=sb_goster, ipk=False)
        if self.row_teshis.cb_sb:
            self.row_teshis.cb_sb.setChecked(True)
        self.row_teshis.degisti.connect(self.degisti)
        layout.addWidget(self.row_teshis)

        # Miktar Tayini
        self.miktar_w = MiktarWidget()
        self.miktar_w.degisti.connect(self.degisti)
        self.row_miktar = TestSatiri("Miktar Tayini", self.miktar_w,
                                     yildiz=True, sb=sb_goster, ipk=False)
        if self.row_miktar.cb_sb:
            self.row_miktar.cb_sb.setChecked(True)
        self.row_miktar.degisti.connect(self.degisti)
        layout.addWidget(self.row_miktar)

        # Karışım Tekdüzeliği (bulk'ta)
        if kt_goster:
            kt_w = QWidget()
            kt_l = QHBoxLayout(kt_w); kt_l.setContentsMargins(0,0,0,0); kt_l.setSpacing(4)
            kt_l.addWidget(QLabel("%"))
            self.kt_alt = QLineEdit("85.0"); self.kt_alt.setFixedWidth(60)
            kt_l.addWidget(self.kt_alt)
            kt_l.addWidget(QLabel("–"))
            self.kt_ust = QLineEdit("115.0"); self.kt_ust.setFixedWidth(60)
            kt_l.addWidget(self.kt_ust); kt_l.addStretch()
            self.kt_alt.textChanged.connect(self.degisti)
            self.kt_ust.textChanged.connect(self.degisti)
            self.row_kt = TestSatiri("Karışım Tekdüzeliği", kt_w,
                                     yildiz=True, sb=False, ipk=False)
            self.row_kt.degisti.connect(self.degisti)
            layout.addWidget(self.row_kt)
            QWidget.setTabOrder(self.kt_alt, self.kt_ust)

        # Dissolüsyon (çekirdek/film'de)
        if dissolusyon_goster:
            self.dis_w = DissolusyonWidget()
            self.dis_w.degisti.connect(self.degisti)
            self.row_dis = TestSatiri("Dissolüsyon", self.dis_w,
                                      yildiz=True, sb=sb_goster, ipk=False)
            if self.row_dis.cb_sb:
                self.row_dis.cb_sb.setChecked(True)
            self.row_dis.degisti.connect(self.degisti)
            layout.addWidget(self.row_dis)

        # İlgili Bileşikler başlık
        imp_hdr = QFrame()
        imp_hdr.setStyleSheet(f"background:{RENK_PRIMARY_ACIK};border-radius:4px;")
        imp_hl = QHBoxLayout(imp_hdr); imp_hl.setContentsMargins(8,3,8,3)
        imp_hl.addWidget(QLabel("İlgili Bileşikler (İmpüriteler)"))
        self.cb_imp_yildiz = QCheckBox("*"); self.cb_imp_yildiz.setStyleSheet(_cb_stil())
        self.cb_imp_yildiz.stateChanged.connect(self.degisti)
        imp_hl.addWidget(self.cb_imp_yildiz)
        self.cb_imp_sb = None
        if sb_goster:
            self.cb_imp_sb = QCheckBox("SB"); self.cb_imp_sb.setStyleSheet(_cb_stil())
            self.cb_imp_sb.setChecked(True); self.cb_imp_sb.stateChanged.connect(self.degisti)
            imp_hl.addWidget(self.cb_imp_sb)
        # IPK analitik testlerde yok
        imp_hl.addStretch(); layout.addWidget(imp_hdr)

        self._imp_container = QWidget()
        self._imp_layout = QVBoxLayout(self._imp_container)
        self._imp_layout.setContentsMargins(8,2,0,2); self._imp_layout.setSpacing(2)
        layout.addWidget(self._imp_container)

        # Küçük impürite ekle butonu
        btn_imp = QPushButton("+ İmpürite Ekle")
        btn_imp.setFixedHeight(22)
        btn_imp.setMaximumWidth(130)
        btn_imp.setStyleSheet(f"""
            QPushButton{{
                border:1px dashed {RENK_PRIMARY};border-radius:4px;
                background:transparent;color:{RENK_PRIMARY};font-size:10px;
                padding:1px 8px;margin:2px 8px;
            }}
            QPushButton:hover{{background:{RENK_PRIMARY_ACIK};}}
        """)
        btn_imp.clicked.connect(lambda: self._imp_ekle())
        layout.addWidget(btn_imp)

    def _imp_ekle(self, model: ImpuriteSpek = None):
        s = ImpuriteSatiri(self._imp_container)
        if model:
            s.from_model(model)
        s.silindi.connect(self._imp_sil)
        s.degisti.connect(self.degisti)
        self._imp_satirlari.append(s)
        self._imp_layout.addWidget(s)
        self.degisti.emit()

    def _imp_sil(self, s):
        self._imp_satirlari.remove(s)
        s.deleteLater()
        self.degisti.emit()

    def to_model(self, spek: EtkenMaddeAnalitikSpek):
        spek.miktar_hedef = self.miktar_w.input_hedef.text().strip()
        spek.miktar_birim = "mg"
        spek.miktar_tolerans = self.miktar_w.input_tol.text().strip()
        spek.miktar_yildiz = self.row_miktar.cb_yildiz.isChecked() if self.row_miktar.cb_yildiz else False
        spek.miktar_sb = self.row_miktar.cb_sb.isChecked() if self.row_miktar.cb_sb else False
        spek.miktar_ipk = False
        spek.teshis_yildiz = self.row_teshis.cb_yildiz.isChecked() if self.row_teshis.cb_yildiz else False
        spek.teshis_sb = self.row_teshis.cb_sb.isChecked() if self.row_teshis.cb_sb else False
        if self._kt_goster and hasattr(self, 'kt_alt'):
            spek.kt_alt = self.kt_alt.text().strip()
            spek.kt_ust = self.kt_ust.text().strip()
            spek.kt_yildiz = self.row_kt.cb_yildiz.isChecked() if self.row_kt.cb_yildiz else False
        if self._dissolusyon_goster and hasattr(self, 'dis_w'):
            spek.dis_min_q = self.dis_w.input_q.text().strip()
            spek.dis_q_kullan = self.dis_w.cb_q.isChecked()
            spek.dis_sure_dk = self.dis_w.input_sure.text().strip()
            spek.dis_yildiz = self.row_dis.cb_yildiz.isChecked() if self.row_dis.cb_yildiz else False
            spek.dis_sb = self.row_dis.cb_sb.isChecked() if self.row_dis.cb_sb else False
        spek.impuriteler = [s.to_model() for s in self._imp_satirlari]
        spek.imp_yildiz = self.cb_imp_yildiz.isChecked()
        spek.imp_sb = self.cb_imp_sb.isChecked() if self.cb_imp_sb else False
        spek.imp_ipk = False

    def from_model(self, spek: EtkenMaddeAnalitikSpek):
        self.miktar_w.input_hedef.setText(spek.miktar_hedef)
        self.miktar_w.input_tol.setText(spek.miktar_tolerans)
        if self.row_miktar.cb_yildiz:
            self.row_miktar.cb_yildiz.setChecked(getattr(spek, 'miktar_yildiz', False))
        # SB checkbox'ları: modelde True ise True, modelde değer yoksa varsayılan True bırak
        if self.row_miktar.cb_sb:
            self.row_miktar.cb_sb.setChecked(getattr(spek, 'miktar_sb', True))
        if self.row_teshis.cb_yildiz:
            self.row_teshis.cb_yildiz.setChecked(getattr(spek, 'teshis_yildiz', False))
        if self.row_teshis.cb_sb:
            self.row_teshis.cb_sb.setChecked(getattr(spek, 'teshis_sb', True))
        if self._kt_goster and hasattr(self, 'kt_alt'):
            self.kt_alt.setText(getattr(spek, 'kt_alt', '85.0'))
            self.kt_ust.setText(getattr(spek, 'kt_ust', '115.0'))
        if self._dissolusyon_goster and hasattr(self, 'dis_w'):
            self.dis_w.input_q.setText(spek.dis_min_q)
            self.dis_w.cb_q.setChecked(getattr(spek, 'dis_q_kullan', True))
            self.dis_w.input_sure.setText(spek.dis_sure_dk)
            if self.row_dis.cb_sb:
                self.row_dis.cb_sb.setChecked(getattr(spek, 'dis_sb', True))
        for s in self._imp_satirlari[:]:
            s.deleteLater()
        self._imp_satirlari.clear()
        for imp in spek.impuriteler:
            self._imp_ekle(imp)
        self.cb_imp_yildiz.setChecked(getattr(spek, 'imp_yildiz', False))
        if self.cb_imp_sb:
            self.cb_imp_sb.setChecked(getattr(spek, 'imp_sb', True))

    def impuriteleri_aktar(self, hedef: 'EtkenAnalitikPanel'):
        """Bulk'tan çekirdek/film'e impürite ve miktar aktarımı."""
        hedef.miktar_w.input_hedef.setText(self.miktar_w.input_hedef.text())
        hedef.miktar_w.input_tol.setText(self.miktar_w.input_tol.text())
        # İmpüriteler
        for s in hedef._imp_satirlari[:]:
            s.deleteLater()
        hedef._imp_satirlari.clear()
        for s in self._imp_satirlari:
            m = s.to_model()
            hedef._imp_ekle(m)
        hedef.cb_imp_yildiz.setChecked(self.cb_imp_yildiz.isChecked())


# ─── Mikrobiyolojik Panel ─────────────────────────────────────────────────────

class MikrobiyolojikPanel(QFrame):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        l = QHBoxLayout(self); l.setContentsMargins(8,4,8,4); l.setSpacing(8)
        lbl = QLabel("Mikrobiyolojik Kontrol"); lbl.setFixedWidth(180)
        lbl.setStyleSheet(f"font-size:11px;color:{RENK_YAZI_BIRINCIL};")
        l.addWidget(lbl)
        sabit = QLabel("Sabit: Aerobik ≤10³, Küf-Maya ≤10², E.coli 0 cfu/g")
        sabit.setStyleSheet(f"font-size:10px;color:{RENK_YAZI_UCUNCUL};font-style:italic;")
        l.addWidget(sabit, 1)
        self.cb_yildiz = QCheckBox()
        self.cb_yildiz.setToolTip("* = Sadece validasyonda")
        self.cb_yildiz.setStyleSheet(_cb_stil())
        self.cb_yildiz.stateChanged.connect(self.degisti)
        c = QWidget(); c.setFixedWidth(44)
        cl = QHBoxLayout(c); cl.setContentsMargins(0,0,0,0)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(self.cb_yildiz); l.addWidget(c)


# ─── Fiziksel Testler ─────────────────────────────────────────────────────────

class FizikselTestlerWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, film_mi: bool = False, sb_goster: bool = False,
                 parent=None):
        super().__init__(parent)
        self._film_mi = film_mi
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        layout.addWidget(_baslik_satiri(yildiz=True, sb=sb_goster, ipk=False))

        # Görünüş
        self.input_gorunus = QLineEdit()
        self.input_gorunus.setPlaceholderText(
            "Film kaplı tablet görünüşü" if film_mi else "Tablet görünüşü")
        self.input_gorunus.textChanged.connect(self.degisti)
        self.row_gorunus = TestSatiri("Görünüş", self.input_gorunus,
                                      yildiz=True, sb=sb_goster)
        self.row_gorunus.degisti.connect(self.degisti)
        layout.addWidget(self.row_gorunus)

        # Ortalama Ağırlık
        self.agirlik_w = AgirlikSatiri()
        self.agirlik_w.degisti.connect(self.degisti)
        self.row_agirlik = TestSatiri("Ortalama Ağırlık", self.agirlik_w,
                                      yildiz=True, sb=sb_goster)
        self.row_agirlik.degisti.connect(self.degisti)
        layout.addWidget(self.row_agirlik)

        # Ağırlık Tekdüzeliği
        self.at_w = AgirlikTekduzeligiWidget()
        self.at_w.degisti.connect(self.degisti)
        self.row_at = TestSatiri("Ağırlık Tekdüzeliği", self.at_w,
                                 yildiz=True, sb=sb_goster)
        self.row_at.degisti.connect(self.degisti)
        layout.addWidget(self.row_at)

        if not film_mi:
            # Kalınlık
            self.kalinlik_w = KalinlikWidget()
            self.kalinlik_w.degisti.connect(self.degisti)
            self.row_kalinlik = TestSatiri("Kalınlık", self.kalinlik_w,
                                           yildiz=True, sb=sb_goster)
            self.row_kalinlik.degisti.connect(self.degisti)
            layout.addWidget(self.row_kalinlik)

            # Çap
            self.cap_w = CapWidget()
            self.cap_w.degisti.connect(self.degisti)
            self.row_cap = TestSatiri("Çap", self.cap_w,
                                      yildiz=True, sb=sb_goster)
            self.row_cap.degisti.connect(self.degisti)
            layout.addWidget(self.row_cap)

            # Sertlik
            self.sertlik_w = SertlikWidget()
            self.sertlik_w.degisti.connect(self.degisti)
            self.row_sertlik = TestSatiri("Sertlik", self.sertlik_w,
                                          yildiz=True, sb=sb_goster)
            self.row_sertlik.degisti.connect(self.degisti)
            layout.addWidget(self.row_sertlik)

            # Aşınma
            asinma_w = QWidget()
            al = QHBoxLayout(asinma_w); al.setContentsMargins(0,0,0,0); al.setSpacing(4)
            al.addWidget(QLabel("Maks."))
            self.input_asinma = QLineEdit("1.0"); self.input_asinma.setFixedWidth(70)
            self.input_asinma.textChanged.connect(self.degisti)
            al.addWidget(self.input_asinma); al.addWidget(QLabel("%")); al.addStretch()
            self.row_asinma = TestSatiri("Aşınma", asinma_w,
                                         yildiz=True, sb=sb_goster)
            self.row_asinma.degisti.connect(self.degisti)
            layout.addWidget(self.row_asinma)

        # Dağılma
        sure = "30" if film_mi else "15"
        dagılma_lbl = QLabel(
            f"Maksimum {sure} dakika  ({'Film Kaplama' if film_mi else 'Tablet Baskı'} — sabit)")
        dagılma_lbl.setStyleSheet(f"font-size:11px;color:{RENK_YAZI_IKINCIL};")
        self.row_dagılma = TestSatiri("Dağılma", dagılma_lbl,
                                      yildiz=True, sb=sb_goster)
        self.row_dagılma.degisti.connect(self.degisti)
        layout.addWidget(self.row_dagılma)


# ─── Çekirdek Tablet Sekmesi ──────────────────────────────────────────────────

class CekirdekTabletSekmesi(QScrollArea):
    degisti = pyqtSignal()

    def __init__(self, proje: ProjeVerisi, sb_goster: bool = False, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True); self.setFrameShape(QFrame.Shape.NoFrame)
        self._proje = proje
        self._em_paneller: list[EtkenAnalitikPanel] = []

        w = QWidget()
        self._layout = QVBoxLayout(w)
        self._layout.setContentsMargins(12,8,12,8); self._layout.setSpacing(8)

        self._layout.addWidget(_sek_baslik("Fiziksel Testler — Tablet Baskı"))
        self.fiziksel = FizikselTestlerWidget(film_mi=False, sb_goster=sb_goster)
        self.fiziksel.degisti.connect(self.degisti)
        self._layout.addWidget(self.fiziksel)

        self._layout.addWidget(_sek_baslik("Mikrobiyolojik Kontrol"))
        self.mikro = MikrobiyolojikPanel()
        self.mikro.degisti.connect(self.degisti)
        self._layout.addWidget(self.mikro)

        self._em_container = QWidget()
        self._em_layout = QVBoxLayout(self._em_container)
        self._em_layout.setContentsMargins(0,0,0,0); self._em_layout.setSpacing(8)
        self._layout.addWidget(self._em_container)
        self._layout.addStretch()
        self.setWidget(w)
        self._em_panelleri_olustur(sb_goster)

    def _em_panelleri_olustur(self, sb_goster=False):
        for p in self._em_paneller: p.deleteLater()
        self._em_paneller.clear()
        for em in self._proje.etken_maddeler:
            self._em_layout.addWidget(_sek_baslik(f"{em.ad} — Analitik Testler"))
            panel = EtkenAnalitikPanel(em.ad, dissolusyon_goster=True,
                                       kt_goster=False, sb_goster=sb_goster)
            panel.degisti.connect(self.degisti)
            self._em_paneller.append(panel)
            self._em_layout.addWidget(panel)

    def bulk_verisi_aktar(self, bulk_paneller: list['EtkenAnalitikPanel'],
                          em_indeksler: list[int]):
        """Bulk'tan miktar ve impürite verilerini aktar."""
        for bulk_panel, idx in zip(bulk_paneller, em_indeksler):
            if idx < len(self._em_paneller):
                bulk_panel.impuriteleri_aktar(self._em_paneller[idx])

    def dis_aktar(self, kaynak_panel: 'EtkenAnalitikPanel', hedef_idx: int):
        """Çekirdek dissolüsyonunu film'e aktarmak için dışa açık."""
        pass  # Film sekmesi kendi from_model'inde kullanır

    def to_model(self, spek: CekirdekTabletSpek, analitik: list):
        f = self.fiziksel
        spek.gorunus = f.input_gorunus.text().strip()
        spek.gorunus_yildiz = f.row_gorunus.cb_yildiz.isChecked() if f.row_gorunus.cb_yildiz else False
        spek.ort_agirlik_hedef_mg = f.agirlik_w.input_hedef.text().strip()
        spek.ort_agirlik_tolerans = f.agirlik_w.input_tol.text().strip()
        spek.at_l1_alt = f.at_w.l1_alt.text().strip()
        spek.at_l1_ust = f.at_w.l1_ust.text().strip()
        spek.at_l2_alt = f.at_w.l2_alt.text().strip()
        spek.at_l2_ust = f.at_w.l2_ust.text().strip()
        spek.kalinlik_hedef = f.kalinlik_w.hedef.text().strip()
        spek.kalinlik_alt = f.kalinlik_w.alt.text().strip()
        spek.kalinlik_ust = f.kalinlik_w.ust.text().strip()
        spek.cap_hedef = f.cap_w.hedef.text().strip()
        spek.cap_alt = f.cap_w.alt.text().strip()
        spek.cap_ust = f.cap_w.ust.text().strip()
        spek.sertlik_min = f.sertlik_w.input_min.text().strip()
        spek.sertlik_max = f.sertlik_w.input_max.text().strip()
        spek.asinma_max = f.input_asinma.text().strip()
        spek.mikro_yildiz = self.mikro.cb_yildiz.isChecked()
        for i, panel in enumerate(self._em_paneller):
            if i < len(analitik): panel.to_model(analitik[i])

    def from_model(self, spek: CekirdekTabletSpek, analitik: list):
        f = self.fiziksel
        f.input_gorunus.setText(spek.gorunus)
        f.agirlik_w.input_hedef.setText(spek.ort_agirlik_hedef_mg)
        f.agirlik_w.input_tol.setText(spek.ort_agirlik_tolerans)
        f.at_w.l1_alt.setText(spek.at_l1_alt); f.at_w.l1_ust.setText(spek.at_l1_ust)
        f.at_w.l2_alt.setText(spek.at_l2_alt); f.at_w.l2_ust.setText(spek.at_l2_ust)
        for inp, val in [(f.kalinlik_w.hedef, spek.kalinlik_hedef),
                         (f.kalinlik_w.alt, spek.kalinlik_alt),
                         (f.kalinlik_w.ust, spek.kalinlik_ust),
                         (f.cap_w.hedef, spek.cap_hedef),
                         (f.cap_w.alt, spek.cap_alt),
                         (f.cap_w.ust, spek.cap_ust)]:
            inp.blockSignals(True); inp.setText(val); inp.blockSignals(False)
        f.sertlik_w.input_min.setText(spek.sertlik_min)
        f.sertlik_w.input_max.setText(getattr(spek, 'sertlik_max', ''))
        f.input_asinma.setText(spek.asinma_max)
        self.mikro.cb_yildiz.setChecked(getattr(spek, 'mikro_yildiz', False))
        for i, panel in enumerate(self._em_paneller):
            if i < len(analitik): panel.from_model(analitik[i])


# ─── Film Tablet Sekmesi ──────────────────────────────────────────────────────

class FilmTabletSekmesi(QScrollArea):
    degisti = pyqtSignal()

    def __init__(self, proje: ProjeVerisi, sb_goster: bool = True, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True); self.setFrameShape(QFrame.Shape.NoFrame)
        self._proje = proje
        self._em_paneller: list[EtkenAnalitikPanel] = []

        w = QWidget()
        self._layout = QVBoxLayout(w)
        self._layout.setContentsMargins(12,8,12,8); self._layout.setSpacing(8)

        self._layout.addWidget(_sek_baslik("Fiziksel Testler — Film Kaplama"))
        self.fiziksel = FizikselTestlerWidget(film_mi=True, sb_goster=sb_goster)
        self.fiziksel.degisti.connect(self.degisti)

        # Film ağırlık uyarısı
        self.fiziksel.agirlik_w.input_hedef.textChanged.connect(self._agirlik_kontrol)
        self.lbl_agirlik_uyari = QLabel("")
        self.lbl_agirlik_uyari.setStyleSheet(f"""
            font-size:10px;color:#A32D2D;
            background:#FCEBEB;border-radius:4px;padding:2px 8px;
        """)
        self.lbl_agirlik_uyari.setVisible(False)

        self._layout.addWidget(self.fiziksel)
        self._layout.addWidget(self.lbl_agirlik_uyari)

        self._layout.addWidget(_sek_baslik("Mikrobiyolojik Kontrol"))
        self.mikro = MikrobiyolojikPanel()
        self.mikro.degisti.connect(self.degisti)
        self._layout.addWidget(self.mikro)

        self._em_container = QWidget()
        self._em_layout = QVBoxLayout(self._em_container)
        self._em_layout.setContentsMargins(0,0,0,0); self._em_layout.setSpacing(8)
        self._layout.addWidget(self._em_container)
        self._layout.addStretch()
        self.setWidget(w)
        self._em_panelleri_olustur(sb_goster)

        # Çekirdek tablet referansı (ağırlık karşılaştırma için)
        self._cekirdek_spek: CekirdekTabletSpek = None

    def set_cekirdek_spek(self, spek: CekirdekTabletSpek):
        self._cekirdek_spek = spek

    def _agirlik_kontrol(self, metin: str):
        """Film ağırlığı çekirdek ağırlığından büyük olmalı."""
        if not self._cekirdek_spek:
            return
        try:
            film_ag = float(metin.replace(",", "."))
            cekirdek_ag = float(self._cekirdek_spek.ort_agirlik_hedef_mg or "0")
            if cekirdek_ag > 0 and film_ag <= cekirdek_ag:
                self.lbl_agirlik_uyari.setText(
                    f"⚠ Film tablet ağırlığı ({film_ag} mg) çekirdek ağırlığından "
                    f"({cekirdek_ag} mg) büyük olmalıdır!")
                self.lbl_agirlik_uyari.setVisible(True)
            else:
                self.lbl_agirlik_uyari.setVisible(False)
        except ValueError:
            self.lbl_agirlik_uyari.setVisible(False)

    def _em_panelleri_olustur(self, sb_goster=True):
        for p in self._em_paneller: p.deleteLater()
        self._em_paneller.clear()
        for em in self._proje.etken_maddeler:
            self._em_layout.addWidget(_sek_baslik(f"{em.ad} — Analitik Testler"))
            panel = EtkenAnalitikPanel(em.ad, dissolusyon_goster=True,
                                       kt_goster=False, sb_goster=sb_goster)
            panel.degisti.connect(self.degisti)
            self._em_paneller.append(panel)
            self._em_layout.addWidget(panel)

    def bulk_verisi_aktar(self, bulk_paneller: list[EtkenAnalitikPanel],
                          em_indeksler: list[int]):
        """Bulk'tan miktar ve impürite verilerini aktar."""
        for bulk_panel, idx in zip(bulk_paneller, em_indeksler):
            if idx < len(self._em_paneller):
                bulk_panel.impuriteleri_aktar(self._em_paneller[idx])

    def cekirdek_dis_aktar(self, cekirdek_paneller: list[EtkenAnalitikPanel]):
        """Çekirdek dissolüsyon speklerini film sekmesine aktar."""
        for i, (film_panel, cekirdek_panel) in enumerate(
                zip(self._em_paneller, cekirdek_paneller)):
            if hasattr(cekirdek_panel, 'dis_w') and hasattr(film_panel, 'dis_w'):
                film_panel.dis_w.input_q.setText(cekirdek_panel.dis_w.input_q.text())
                film_panel.dis_w.cb_q.setChecked(cekirdek_panel.dis_w.cb_q.isChecked())
                film_panel.dis_w.input_sure.setText(cekirdek_panel.dis_w.input_sure.text())

    def to_model(self, spek: FilmTabletSpek, analitik: list):
        f = self.fiziksel
        spek.gorunus = f.input_gorunus.text().strip()
        spek.ort_agirlik_hedef_mg = f.agirlik_w.input_hedef.text().strip()
        spek.ort_agirlik_tolerans = f.agirlik_w.input_tol.text().strip()
        spek.at_l1_alt = f.at_w.l1_alt.text().strip()
        spek.at_l1_ust = f.at_w.l1_ust.text().strip()
        spek.at_l2_alt = f.at_w.l2_alt.text().strip()
        spek.at_l2_ust = f.at_w.l2_ust.text().strip()
        spek.mikro_yildiz = self.mikro.cb_yildiz.isChecked()
        for i, panel in enumerate(self._em_paneller):
            if i < len(analitik): panel.to_model(analitik[i])

    def from_model(self, spek: FilmTabletSpek, analitik: list):
        f = self.fiziksel
        f.input_gorunus.setText(spek.gorunus)
        f.agirlik_w.input_hedef.setText(spek.ort_agirlik_hedef_mg)
        f.agirlik_w.input_tol.setText(spek.ort_agirlik_tolerans)
        f.at_w.l1_alt.setText(spek.at_l1_alt); f.at_w.l1_ust.setText(spek.at_l1_ust)
        f.at_w.l2_alt.setText(spek.at_l2_alt); f.at_w.l2_ust.setText(spek.at_l2_ust)
        self.mikro.cb_yildiz.setChecked(getattr(spek, 'mikro_yildiz', False))
        for i, panel in enumerate(self._em_paneller):
            if i < len(analitik): panel.from_model(analitik[i])


# ─── Bulk Katman Sekmesi ──────────────────────────────────────────────────────

class BulkKatmanSekmesi(QScrollArea):
    degisti = pyqtSignal()

    def __init__(self, katman_spek: BulkKatmanSpek,
                 proje: ProjeVerisi, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True); self.setFrameShape(QFrame.Shape.NoFrame)
        self._katman_spek = katman_spek
        self._proje = proje
        self._em_paneller: list[EtkenAnalitikPanel] = []

        w = QWidget()
        self._layout = QVBoxLayout(w)
        self._layout.setContentsMargins(12,8,12,8); self._layout.setSpacing(8)

        self._layout.addWidget(_sek_baslik("Genel — Katman Testleri"))
        self._layout.addWidget(_baslik_satiri(yildiz=True, sb=False, ipk=False))

        # Görünüş
        self.input_gorunus = QLineEdit()
        self.input_gorunus.setPlaceholderText("Örn: Beyaz renkli toz")
        self.input_gorunus.textChanged.connect(self.degisti)
        self.row_gorunus = TestSatiri("Görünüş", self.input_gorunus,
                                      yildiz=True, sb=False, ipk=False)
        self.row_gorunus.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_gorunus)

        for attr, ad in [("row_elek","Elek Testi"),
                          ("row_bulk","Bulk Dansite"),
                          ("row_tap","Tap Dansite")]:
            lbl = QLabel("Bilgi amaçlıdır.")
            lbl.setStyleSheet(f"font-size:10px;color:{RENK_YAZI_UCUNCUL};font-style:italic;")
            row = TestSatiri(ad, lbl, yildiz=True, sb=False, ipk=False)
            row.degisti.connect(self.degisti)
            setattr(self, attr, row)
            self._layout.addWidget(row)

        self._layout.addWidget(_sek_baslik("Mikrobiyolojik Kontrol — Katman"))
        self.mikro = MikrobiyolojikPanel()
        self.mikro.degisti.connect(self.degisti)
        self._layout.addWidget(self.mikro)

        self._em_container = QWidget()
        self._em_layout = QVBoxLayout(self._em_container)
        self._em_layout.setContentsMargins(0,0,0,0); self._em_layout.setSpacing(8)
        self._layout.addWidget(self._em_container)
        self._layout.addStretch()
        self.setWidget(w)
        self._em_panelleri_olustur()

    def _em_panelleri_olustur(self):
        for p in self._em_paneller: p.deleteLater()
        self._em_paneller.clear()
        for idx in self._katman_spek.etken_indeksler:
            if idx < len(self._proje.etken_maddeler):
                em = self._proje.etken_maddeler[idx]
                self._em_layout.addWidget(
                    _sek_baslik(f"{em.ad} — Analitik Testler (Bulk)"))
                panel = EtkenAnalitikPanel(em.ad, dissolusyon_goster=False,
                                           kt_goster=True, sb_goster=False)
                panel.degisti.connect(self.degisti)
                self._em_paneller.append(panel)
                self._em_layout.addWidget(panel)

    def to_model(self, analitik: list):
        self._katman_spek.gorunus = self.input_gorunus.text().strip()
        self._katman_spek.gorunus_yildiz = self.row_gorunus.cb_yildiz.isChecked() if self.row_gorunus.cb_yildiz else False
        self._katman_spek.elek_yildiz = self.row_elek.cb_yildiz.isChecked() if self.row_elek.cb_yildiz else False
        self._katman_spek.bulk_yildiz = self.row_bulk.cb_yildiz.isChecked() if self.row_bulk.cb_yildiz else False
        self._katman_spek.tap_yildiz = self.row_tap.cb_yildiz.isChecked() if self.row_tap.cb_yildiz else False
        self._katman_spek.mikro_yildiz = self.mikro.cb_yildiz.isChecked()
        for panel, idx in zip(self._em_paneller, self._katman_spek.etken_indeksler):
            if idx < len(analitik): panel.to_model(analitik[idx])

    def from_model(self, analitik: list):
        self.input_gorunus.setText(self._katman_spek.gorunus)
        if self.row_gorunus.cb_yildiz:
            self.row_gorunus.cb_yildiz.setChecked(getattr(self._katman_spek,'gorunus_yildiz',False))
        if self.row_elek.cb_yildiz:
            self.row_elek.cb_yildiz.setChecked(getattr(self._katman_spek,'elek_yildiz',False))
        if self.row_bulk.cb_yildiz:
            self.row_bulk.cb_yildiz.setChecked(getattr(self._katman_spek,'bulk_yildiz',False))
        if self.row_tap.cb_yildiz:
            self.row_tap.cb_yildiz.setChecked(getattr(self._katman_spek,'tap_yildiz',False))
        self.mikro.cb_yildiz.setChecked(getattr(self._katman_spek,'mikro_yildiz',False))
        for panel, idx in zip(self._em_paneller, self._katman_spek.etken_indeksler):
            if idx < len(analitik): panel.from_model(analitik[idx])

    def set_aktar_callback(self, callback):
        """SpecKartiWidget anlık aktarım callback'i."""
        self._aktar_callback = callback

    def _anlik_aktar(self):
        """Bulk'ta değişiklik olunca anlık aktarım tetikle."""
        if hasattr(self, '_aktar_callback') and self._aktar_callback:
            self._aktar_callback(self)


# ─── Ana Spec Kartı Widget ────────────────────────────────────────────────────

class SpecKartiWidget(QWidget):
    kaydedildi = pyqtSignal()
    degisti = pyqtSignal()

    def __init__(self, proje: ProjeVerisi, parent=None):
        super().__init__(parent)
        self._proje = proje
        self._degisiklik_var = False
        self._sekme_cekirdek: CekirdekTabletSekmesi = None
        self._sekme_film: FilmTabletSekmesi = None
        self._bulk_sekmeleri: list[BulkKatmanSekmesi] = []
        self._setup_ui()
        self._yukle()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)

        toolbar = QFrame()
        toolbar.setStyleSheet(
            f"background:{RENK_BG_BIRINCIL};border-bottom:1px solid {RENK_KENARLIK};")
        toolbar.setFixedHeight(46)
        tb = QHBoxLayout(toolbar); tb.setContentsMargins(16,0,16,0); tb.setSpacing(8)

        lbl = QLabel("Spec Kartı")
        lbl.setStyleSheet(f"font-size:13px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        tb.addWidget(lbl)
        sep = QLabel("/"); sep.setStyleSheet(f"color:{RENK_KENARLIK};"); tb.addWidget(sep)
        alt = QLabel("Spesifikasyon tanımları")
        alt.setStyleSheet(f"font-size:12px;color:{RENK_YAZI_IKINCIL};"); tb.addWidget(alt)
        tb.addStretch()

        self.lbl_degisiklik = QLabel("")
        self.lbl_degisiklik.setVisible(False)
        self.lbl_degisiklik.setStyleSheet(f"""
            font-size:11px;color:{RENK_PRIMARY_KOYU};
            background:{RENK_PRIMARY_ACIK};border-radius:4px;padding:2px 8px;
        """)
        tb.addWidget(self.lbl_degisiklik)

        btn_kaydet = QPushButton("💾  Kaydet")
        btn_kaydet.setFixedHeight(30); btn_kaydet.setMinimumWidth(90)
        btn_kaydet.setStyleSheet(f"""
            QPushButton{{background:{RENK_PRIMARY};color:#FFFFFF;border:none;
            border-radius:6px;font-size:12px;font-weight:bold;
            font-family:{FONT_AILESI};padding:0 14px;}}
            QPushButton:hover{{background:{RENK_PRIMARY_KOYU};}}
        """)
        btn_kaydet.clicked.connect(self._kaydet); tb.addWidget(btn_kaydet)
        layout.addWidget(toolbar)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane{{border:none;background:{RENK_BG_BIRINCIL};}}
            QTabBar::tab{{border:1px solid {RENK_KENARLIK};border-bottom:none;
            border-radius:6px 6px 0 0;padding:6px 14px;font-size:11px;
            color:{RENK_YAZI_IKINCIL};background:{RENK_BG_IKINCIL};margin-right:2px;}}
            QTabBar::tab:selected{{background:{RENK_BG_BIRINCIL};
            color:{RENK_PRIMARY};font-weight:bold;}}
        """)
        layout.addWidget(self.tabs, 1)

    def _yukle(self):
        self.tabs.clear()
        self._sekme_cekirdek = None
        self._sekme_film = None
        self._bulk_sekmeleri.clear()

        self._proje.bulk_katmanlari_olustur()

        urun = self._proje.urun_formu
        film_formlar = [UrunFormu.FILM_TABLET.value, UrunFormu.KAPSUL_FILM_TABLET.value]
        tablet_formlar = [UrunFormu.TABLET.value]

        # ── ÖNCE BULK ──
        for katman_spek in self._proje.bulk_katmanlar:
            sekme = BulkKatmanSekmesi(katman_spek, self._proje)
            sekme.degisti.connect(self._on_degisti)
            sekme.from_model(self._proje.etken_analitik_spekler)
            sekme.set_aktar_callback(self._bulk_anlik_aktar)
            self._bulk_sekmeleri.append(sekme)
            self.tabs.addTab(sekme, katman_spek.katman_adi)

        # ── SONRA ÇEKİRDEK TABLET ──
        if urun != UrunFormu.KAPSUL.value:
            sb = urun in tablet_formlar
            self._sekme_cekirdek = CekirdekTabletSekmesi(self._proje, sb_goster=sb)
            self._sekme_cekirdek.degisti.connect(self._on_degisti)
            self._sekme_cekirdek.from_model(
                self._proje.cekirdek_spek, self._proje.etken_analitik_spekler)
            # from_model sonrası dissolüsyon sinyallerini bağla
            for panel in self._sekme_cekirdek._em_paneller:
                if hasattr(panel, 'dis_w'):
                    panel.dis_w.degisti.connect(self._cekirdek_dis_anlik_aktar)
                panel.miktar_w.degisti.connect(self._cekirdek_anlik_aktar)
                panel.degisti.connect(self._cekirdek_anlik_aktar)
            self.tabs.addTab(self._sekme_cekirdek, "Çekirdek Tablet")

        # ── SONRA FİLM TABLET ──
        if urun in film_formlar:
            self._sekme_film = FilmTabletSekmesi(self._proje, sb_goster=True)
            self._sekme_film.degisti.connect(self._on_degisti)
            if self._sekme_cekirdek:
                self._sekme_film.set_cekirdek_spek(self._proje.cekirdek_spek)
            self._sekme_film.from_model(
                self._proje.film_spek, self._proje.etken_analitik_spekler)
            self.tabs.addTab(self._sekme_film, "Film Tablet")

        self._degisiklik_var = False
        self.lbl_degisiklik.setVisible(False)

    def _on_degisti(self):
        self._degisiklik_var = True
        self.lbl_degisiklik.setText("● Kaydedilmemiş değişiklik")
        self.lbl_degisiklik.setStyleSheet(f"""
            font-size:11px;color:{RENK_PRIMARY_KOYU};
            background:{RENK_PRIMARY_ACIK};border-radius:4px;padding:2px 8px;
        """)
        self.lbl_degisiklik.setVisible(True)
        self.degisti.emit()

    def _bulk_anlik_aktar(self, bulk_sekme: BulkKatmanSekmesi):
        """Bulk'ta değişiklik olunca çekirdek ve film'e anlık aktar."""
        indeksler = bulk_sekme._katman_spek.etken_indeksler
        if self._sekme_cekirdek:
            self._sekme_cekirdek.bulk_verisi_aktar(
                bulk_sekme._em_paneller, indeksler)
        if self._sekme_film:
            self._sekme_film.bulk_verisi_aktar(
                bulk_sekme._em_paneller, indeksler)

    def _cekirdek_anlik_aktar(self):
        """Çekirdek'te miktar/impürite değişince film'e anlık aktar."""
        if self._sekme_cekirdek and self._sekme_film:
            indeksler = list(range(len(self._sekme_cekirdek._em_paneller)))
            self._sekme_film.bulk_verisi_aktar(
                self._sekme_cekirdek._em_paneller, indeksler)

    def _cekirdek_dis_anlik_aktar(self):
        """Çekirdek dissolüsyon değişince film'e anlık aktar."""
        if self._sekme_cekirdek and self._sekme_film:
            self._sekme_film.cekirdek_dis_aktar(
                self._sekme_cekirdek._em_paneller)

    def _kaydet(self):
        n = len(self._proje.etken_maddeler)
        while len(self._proje.etken_analitik_spekler) < n:
            em = self._proje.etken_maddeler[len(self._proje.etken_analitik_spekler)]
            self._proje.etken_analitik_spekler.append(EtkenMaddeAnalitikSpek(ad=em.ad))

        # Bulk kaydet
        for sekme in self._bulk_sekmeleri:
            sekme.to_model(self._proje.etken_analitik_spekler)

        # Çekirdek kaydet
        if self._sekme_cekirdek:
            self._sekme_cekirdek.to_model(
                self._proje.cekirdek_spek, self._proje.etken_analitik_spekler)

        # Film kaydet
        if self._sekme_film:
            self._sekme_film.to_model(
                self._proje.film_spek, self._proje.etken_analitik_spekler)

        # ── Bulk → Çekirdek ve Film otomatik aktarım ──
        for bulk_sekme in self._bulk_sekmeleri:
            indeksler = bulk_sekme._katman_spek.etken_indeksler
            if self._sekme_cekirdek:
                self._sekme_cekirdek.bulk_verisi_aktar(
                    bulk_sekme._em_paneller, indeksler)
                # Kaydet tekrar (aktarım sonrası)
                self._sekme_cekirdek.to_model(
                    self._proje.cekirdek_spek, self._proje.etken_analitik_spekler)
            if self._sekme_film:
                self._sekme_film.bulk_verisi_aktar(
                    bulk_sekme._em_paneller, indeksler)

        # ── Çekirdek Dissolüsyon → Film otomatik aktarım ──
        if self._sekme_cekirdek and self._sekme_film:
            self._sekme_film.cekirdek_dis_aktar(self._sekme_cekirdek._em_paneller)
            self._sekme_film.to_model(
                self._proje.film_spek, self._proje.etken_analitik_spekler)

        self._degisiklik_var = False
        self.lbl_degisiklik.setText("✓ Kaydedildi")
        self.lbl_degisiklik.setStyleSheet(f"""
            font-size:11px;color:{RENK_YESIL};
            background:{RENK_YESIL_BG};border-radius:4px;padding:2px 8px;
        """)
        self.lbl_degisiklik.setVisible(True)
        self.kaydedildi.emit()

    def proje_guncelle(self, proje: ProjeVerisi):
        self._proje = proje
        self._yukle()

    def degisiklik_var_mi(self) -> bool:
        return self._degisiklik_var
