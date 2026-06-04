"""
PV-DOC — Spec Kartı Widget (Modül 2) — Yeniden Yapılandırıldı
Sekmeler:
  Çekirdek Tablet | Film Tablet | Bulk Karışımı / Katman I-II Bulk
Her sekmenin içinde:
  Çekirdek / Film → Fiziksel testler + her etken için analitik
  Bulk → Genel (görünüş/elek/dansite) + her etken için analitik + katman mikrobiyolojik
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QLineEdit, QCheckBox, QPushButton, QScrollArea,
    QTabWidget, QComboBox, QSizePolicy, QMessageBox,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

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


# ─── Ortak Yardımcı Widget'lar ────────────────────────────────────────────────

def _sek_baslik(metin: str) -> QFrame:
    """Bölüm ayırıcı başlık."""
    f = QFrame()
    f.setStyleSheet(f"""
        background: {RENK_PRIMARY_ACIK};
        border-radius: 4px;
    """)
    l = QHBoxLayout(f)
    l.setContentsMargins(10, 4, 10, 4)
    lbl = QLabel(metin)
    lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {RENK_PRIMARY_KOYU};")
    l.addWidget(lbl)
    return f


def _satir_baslik() -> QFrame:
    """Test sütun başlığı satırı."""
    f = QFrame()
    f.setStyleSheet(f"background: {RENK_BG_IKINCIL}; border-bottom: 1px solid {RENK_KENARLIK};")
    l = QHBoxLayout(f)
    l.setContentsMargins(8, 4, 8, 4)
    for metin, genislik, stretch in [
        ("Test", 180, False),
        ("Spesifikasyon", 0, True),
        ("IPK", 50, False),
        ("Serbest B.", 68, False),
        ("Raf Ömrü", 68, False),
    ]:
        lbl = QLabel(metin)
        lbl.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {RENK_YAZI_IKINCIL};")
        if genislik:
            lbl.setFixedWidth(genislik)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter if not stretch else Qt.AlignmentFlag.AlignLeft)
        if stretch:
            l.addWidget(lbl, 1)
        else:
            l.addWidget(lbl)
    return f


class HesapEtiket(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            font-size: 10px; color: {RENK_PRIMARY};
            background: {RENK_PRIMARY_ACIK};
            border-radius: 3px; padding: 1px 6px;
        """)


class TestSatiri(QFrame):
    degisti = pyqtSignal()

    def __init__(self, test_adi, spek_widget, ipk=True, sb=True, raf=True, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"border-bottom: 1px solid {RENK_KENARLIK}; background: transparent;")
        l = QHBoxLayout(self)
        l.setContentsMargins(8, 3, 8, 3)
        l.setSpacing(8)

        lbl = QLabel(test_adi)
        lbl.setStyleSheet(f"font-size: 11px; color: {RENK_YAZI_BIRINCIL};")
        lbl.setFixedWidth(180)
        l.addWidget(lbl)
        l.addWidget(spek_widget, 1)

        self.cb_ipk = self.cb_sb = self.cb_raf = None
        for goster, attr, w in [(ipk, "cb_ipk", 50), (sb, "cb_sb", 68), (raf, "cb_raf", 68)]:
            cb = QCheckBox()
            cb.setStyleSheet(f"""
                QCheckBox::indicator {{
                    width: 14px; height: 14px;
                    border: 1px solid {RENK_KENARLIK}; border-radius: 3px;
                    background: {RENK_BG_BIRINCIL};
                }}
                QCheckBox::indicator:checked {{
                    background: {RENK_PRIMARY}; border-color: {RENK_PRIMARY};
                }}
            """)
            cb.stateChanged.connect(self.degisti)
            c = QWidget()
            c.setFixedWidth(w)
            cl = QHBoxLayout(c)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(cb)
            if not goster:
                c.setVisible(False)
            setattr(self, attr, cb)
            l.addWidget(c)


class AgirlikSatiri(QFrame):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        self.input_hedef = QLineEdit()
        self.input_hedef.setPlaceholderText("Hedef (mg)")
        self.input_hedef.setFixedWidth(90)
        l.addWidget(self.input_hedef)
        l.addWidget(QLabel("mg  ±"))
        self.input_tol = QLineEdit("5.0")
        self.input_tol.setFixedWidth(44)
        l.addWidget(self.input_tol)
        l.addWidget(QLabel("%"))
        self.lbl = HesapEtiket("→ limit hesapla")
        l.addWidget(self.lbl)
        l.addStretch()
        self.input_hedef.textChanged.connect(self._hesapla)
        self.input_tol.textChanged.connect(self._hesapla)
        self.input_hedef.textChanged.connect(self.degisti)
        self.input_tol.textChanged.connect(self.degisti)

    def _hesapla(self):
        try:
            h = float(self.input_hedef.text())
            t = float(self.input_tol.text())
            self.lbl.setText(f"→ {round(h*(1-t/100),2)} – {round(h*(1+t/100),2)} mg")
        except ValueError:
            self.lbl.setText("→ limit hesapla")


class AgirlikTekduzeligiWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        lbl1 = QLabel("L1:")
        lbl1.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_IKINCIL}; font-weight: bold;")
        lbl1.setToolTip("Limit 1: maks. 2/20 tablet sapabilir")
        l.addWidget(lbl1)
        self.l1_alt = QLineEdit()
        self.l1_alt.setPlaceholderText("Alt (mg)")
        self.l1_alt.setFixedWidth(72)
        l.addWidget(self.l1_alt)
        l.addWidget(QLabel("–"))
        self.l1_ust = QLineEdit()
        self.l1_ust.setPlaceholderText("Üst (mg)")
        self.l1_ust.setFixedWidth(72)
        l.addWidget(self.l1_ust)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {RENK_KENARLIK};")
        l.addWidget(sep)
        lbl2 = QLabel("L2:")
        lbl2.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_IKINCIL}; font-weight: bold;")
        lbl2.setToolTip("Limit 2: hiçbiri sapamaz")
        l.addWidget(lbl2)
        self.l2_alt = QLineEdit()
        self.l2_alt.setPlaceholderText("Alt (mg)")
        self.l2_alt.setFixedWidth(72)
        l.addWidget(self.l2_alt)
        l.addWidget(QLabel("–"))
        self.l2_ust = QLineEdit()
        self.l2_ust.setPlaceholderText("Üst (mg)")
        self.l2_ust.setFixedWidth(72)
        l.addWidget(self.l2_ust)
        l.addStretch()
        for inp in [self.l1_alt, self.l1_ust, self.l2_alt, self.l2_ust]:
            inp.textChanged.connect(self.degisti)


class KalinlikWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        l.addWidget(QLabel("Hedef:"))
        self.hedef = QLineEdit()
        self.hedef.setPlaceholderText("mm")
        self.hedef.setFixedWidth(60)
        l.addWidget(self.hedef)
        l.addWidget(QLabel("Alt:"))
        self.alt = QLineEdit()
        self.alt.setPlaceholderText("mm")
        self.alt.setFixedWidth(60)
        l.addWidget(self.alt)
        l.addWidget(QLabel("Üst:"))
        self.ust = QLineEdit()
        self.ust.setPlaceholderText("mm")
        self.ust.setFixedWidth(60)
        l.addWidget(self.ust)
        self.lbl = QLabel("(±0.5 oto.)")
        self.lbl.setStyleSheet(f"font-size: 9px; color: {RENK_YAZI_UCUNCUL};")
        l.addWidget(self.lbl)
        l.addStretch()
        self.hedef.textChanged.connect(self._hesapla)
        self.alt.textChanged.connect(self.degisti)
        self.ust.textChanged.connect(self.degisti)

    def _hesapla(self, metin):
        self.degisti.emit()
        try:
            h = float(metin.replace(",", "."))
            self.alt.blockSignals(True)
            self.ust.blockSignals(True)
            self.alt.setText(str(round(h - 0.5, 2)))
            self.ust.setText(str(round(h + 0.5, 2)))
            self.alt.blockSignals(False)
            self.ust.blockSignals(False)
            self.lbl.setStyleSheet(f"font-size: 9px; color: {RENK_PRIMARY}; font-weight: bold;")
        except ValueError:
            self.lbl.setStyleSheet(f"font-size: 9px; color: {RENK_YAZI_UCUNCUL};")


class CapWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        l.addWidget(QLabel("Hedef:"))
        self.hedef = QLineEdit()
        self.hedef.setPlaceholderText("mm")
        self.hedef.setFixedWidth(60)
        l.addWidget(self.hedef)
        l.addWidget(QLabel("Alt:"))
        self.alt = QLineEdit()
        self.alt.setPlaceholderText("mm")
        self.alt.setFixedWidth(60)
        l.addWidget(self.alt)
        l.addWidget(QLabel("Üst:"))
        self.ust = QLineEdit()
        self.ust.setPlaceholderText("mm")
        self.ust.setFixedWidth(60)
        l.addWidget(self.ust)
        self.lbl = QLabel("(±0.3 oto.)")
        self.lbl.setStyleSheet(f"font-size: 9px; color: {RENK_YAZI_UCUNCUL};")
        l.addWidget(self.lbl)
        l.addStretch()
        self.hedef.textChanged.connect(self._hesapla)
        self.alt.textChanged.connect(self.degisti)
        self.ust.textChanged.connect(self.degisti)

    def _hesapla(self, metin):
        self.degisti.emit()
        try:
            h = float(metin.replace(",", "."))
            self.alt.blockSignals(True)
            self.ust.blockSignals(True)
            self.alt.setText(str(round(h - 0.3, 2)))
            self.ust.setText(str(round(h + 0.3, 2)))
            self.alt.blockSignals(False)
            self.ust.blockSignals(False)
            self.lbl.setStyleSheet(f"font-size: 9px; color: {RENK_PRIMARY}; font-weight: bold;")
        except ValueError:
            self.lbl.setStyleSheet(f"font-size: 9px; color: {RENK_YAZI_UCUNCUL};")


class SertlikWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        l.addWidget(QLabel("Min."))
        self.input_min = QLineEdit()
        self.input_min.setPlaceholderText("kP")
        self.input_min.setFixedWidth(70)
        l.addWidget(self.input_min)
        l.addWidget(QLabel("Maks."))
        self.input_max = QLineEdit()
        self.input_max.setPlaceholderText("kP (opsiyonel)")
        self.input_max.setFixedWidth(100)
        l.addWidget(self.input_max)
        l.addStretch()
        self.input_min.textChanged.connect(self.degisti)
        self.input_max.textChanged.connect(self.degisti)


class MiktarWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, raf_notu=True, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        self.input_hedef = QLineEdit()
        self.input_hedef.setPlaceholderText("Hedef")
        self.input_hedef.setFixedWidth(70)
        l.addWidget(self.input_hedef)
        self.combo_birim = QComboBox()
        self.combo_birim.addItems(["mg/ftb", "mg/tb", "mg/kap", "%"])
        self.combo_birim.setFixedWidth(70)
        l.addWidget(self.combo_birim)
        l.addWidget(QLabel("±"))
        self.input_tol = QLineEdit("5.0")
        self.input_tol.setFixedWidth(40)
        l.addWidget(self.input_tol)
        l.addWidget(QLabel("%"))
        self.lbl = HesapEtiket("→ limit hesapla")
        l.addWidget(self.lbl)
        if raf_notu:
            lbl_raf = QLabel("(Raf: ±%10 oto.)")
            lbl_raf.setStyleSheet(f"font-size: 9px; color: {RENK_YAZI_UCUNCUL};")
            l.addWidget(lbl_raf)
        l.addStretch()
        self.input_hedef.textChanged.connect(self._hesapla)
        self.input_tol.textChanged.connect(self._hesapla)
        self.input_hedef.textChanged.connect(self.degisti)
        self.input_tol.textChanged.connect(self.degisti)
        self.combo_birim.currentIndexChanged.connect(self.degisti)

    def _hesapla(self):
        try:
            h = float(self.input_hedef.text())
            t = float(self.input_tol.text())
            self.lbl.setText(f"→ {round(h*(1-t/100),3)} – {round(h*(1+t/100),3)}")
        except ValueError:
            self.lbl.setText("→ limit hesapla")


class ImpuriteSatiri(QFrame):
    silindi = pyqtSignal(object)
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self)
        l.setContentsMargins(4, 2, 4, 2)
        l.setSpacing(6)
        self.input_ad = QLineEdit()
        self.input_ad.setPlaceholderText("İmpürite adı")
        self.input_ad.setFixedWidth(150)
        l.addWidget(self.input_ad)
        self.combo_tip = QComboBox()
        self.combo_tip.addItems(["Maks. %", "Min. %"])
        self.combo_tip.setFixedWidth(80)
        l.addWidget(self.combo_tip)
        self.input_deger = QLineEdit()
        self.input_deger.setPlaceholderText("Değer")
        self.input_deger.setFixedWidth(60)
        l.addWidget(self.input_deger)
        l.addWidget(QLabel("%"))
        l.addStretch()
        btn_sil = QPushButton("✕")
        btn_sil.setFixedSize(22, 22)
        btn_sil.setStyleSheet(f"""
            QPushButton {{border:none;background:transparent;color:{RENK_YAZI_UCUNCUL};font-size:11px;}}
            QPushButton:hover{{color:#A32D2D;background:#FCEBEB;border-radius:3px;}}
        """)
        btn_sil.clicked.connect(lambda: self.silindi.emit(self))
        l.addWidget(btn_sil)
        for w in [self.input_ad, self.input_deger]:
            w.textChanged.connect(self.degisti)
        self.combo_tip.currentIndexChanged.connect(self.degisti)

    def to_model(self) -> ImpuriteSpek:
        return ImpuriteSpek(
            ad=self.input_ad.text().strip(),
            limit_tipi=self.combo_tip.currentText(),
            deger=self.input_deger.text().strip(),
        )

    def from_model(self, m: ImpuriteSpek):
        self.input_ad.setText(m.ad)
        idx = self.combo_tip.findText(m.limit_tipi)
        if idx >= 0:
            self.combo_tip.setCurrentIndex(idx)
        self.input_deger.setText(m.deger)


# ─── Etken Madde Analitik Panel ───────────────────────────────────────────────

class EtkenAnalitikPanel(QWidget):
    """
    Bir etken maddeye ait analitik testler.
    Bulk'ta: Teşhis, Miktar Tayini, KT, İlgili Bileşikler
    Çekirdek/Film'de: Teşhis, Miktar Tayini, Dissolüsyon, İlgili Bileşikler
    """

    degisti = pyqtSignal()

    def __init__(self, em_adi: str, dissolusyon_goster: bool = True,
                 kt_goster: bool = False, parent=None):
        super().__init__(parent)
        self._imp_satirlari: list[ImpuriteSatiri] = []
        self._dissolusyon_goster = dissolusyon_goster
        self._kt_goster = kt_goster

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(_satir_baslik())

        # Teşhis
        teshis_lbl = QLabel("Sabit: 'Standart ve numune alıkonma zamanı aynı olmalıdır.'")
        teshis_lbl.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_UCUNCUL}; font-style: italic;")
        self.row_teshis = TestSatiri("Teşhis", teshis_lbl)
        self.row_teshis.cb_ipk.setChecked(True)
        self.row_teshis.degisti.connect(self.degisti)
        layout.addWidget(self.row_teshis)

        # Miktar Tayini
        self.miktar_w = MiktarWidget()
        self.miktar_w.degisti.connect(self.degisti)
        self.row_miktar = TestSatiri("Miktar Tayini", self.miktar_w,
                                     ipk=False, sb=True, raf=True)
        self.row_miktar.cb_sb.setChecked(True)
        self.row_miktar.cb_raf.setChecked(True)
        self.row_miktar.degisti.connect(self.degisti)
        layout.addWidget(self.row_miktar)

        # Karışım Tekdüzeliği (sadece bulk'ta)
        if kt_goster:
            kt_w = QWidget()
            kt_l = QHBoxLayout(kt_w)
            kt_l.setContentsMargins(0, 0, 0, 0)
            kt_l.setSpacing(4)
            kt_l.addWidget(QLabel("%"))
            self.kt_alt = QLineEdit("85.0")
            self.kt_alt.setFixedWidth(60)
            kt_l.addWidget(self.kt_alt)
            kt_l.addWidget(QLabel("–"))
            self.kt_ust = QLineEdit("115.0")
            self.kt_ust.setFixedWidth(60)
            kt_l.addWidget(self.kt_ust)
            kt_l.addStretch()
            self.kt_alt.textChanged.connect(self.degisti)
            self.kt_ust.textChanged.connect(self.degisti)
            self.row_kt = TestSatiri("Karışım Tekdüzeliği", kt_w,
                                     ipk=True, sb=True, raf=True)
            self.row_kt.degisti.connect(self.degisti)
            layout.addWidget(self.row_kt)

        # Dissolüsyon (bulk'ta yok)
        if dissolusyon_goster:
            dis_w = QWidget()
            dis_l = QHBoxLayout(dis_w)
            dis_l.setContentsMargins(0, 0, 0, 0)
            dis_l.setSpacing(4)
            dis_l.addWidget(QLabel("Min."))
            self.dis_q = QLineEdit("80.0")
            self.dis_q.setPlaceholderText("Min. Q (%)")
            self.dis_q.setFixedWidth(70)
            dis_l.addWidget(self.dis_q)
            dis_l.addWidget(QLabel("(Q) —"))
            self.dis_sure = QLineEdit("45")
            self.dis_sure.setPlaceholderText("Süre (dk)")
            self.dis_sure.setFixedWidth(60)
            dis_l.addWidget(self.dis_sure)
            dis_l.addWidget(QLabel("dk"))
            dis_l.addStretch()
            self.dis_q.textChanged.connect(self.degisti)
            self.dis_sure.textChanged.connect(self.degisti)
            self.row_dis = TestSatiri("Dissolüsyon (Q)", dis_w,
                                      ipk=False, sb=True, raf=True)
            self.row_dis.cb_sb.setChecked(True)
            self.row_dis.cb_raf.setChecked(True)
            self.row_dis.degisti.connect(self.degisti)
            layout.addWidget(self.row_dis)

        # İlgili Bileşikler
        imp_baslik = QFrame()
        imp_baslik.setStyleSheet(f"background: {RENK_PRIMARY_ACIK}; border-radius: 4px;")
        imp_bl = QHBoxLayout(imp_baslik)
        imp_bl.setContentsMargins(8, 3, 8, 3)
        imp_bl.addWidget(QLabel("İlgili Bileşikler (İmpüriteler)"))
        self.cb_imp_ipk = QCheckBox("IPK")
        self.cb_imp_sb = QCheckBox("SB")
        self.cb_imp_sb.setChecked(True)
        self.cb_imp_raf = QCheckBox("Raf")
        self.cb_imp_raf.setChecked(True)
        for cb in [self.cb_imp_ipk, self.cb_imp_sb, self.cb_imp_raf]:
            cb.setStyleSheet(f"font-size: 10px; color: {RENK_PRIMARY_KOYU};")
            cb.stateChanged.connect(self.degisti)
            imp_bl.addWidget(cb)
        imp_bl.addStretch()
        layout.addWidget(imp_baslik)

        self._imp_container = QWidget()
        self._imp_layout = QVBoxLayout(self._imp_container)
        self._imp_layout.setContentsMargins(4, 0, 0, 0)
        self._imp_layout.setSpacing(2)
        layout.addWidget(self._imp_container)

        btn_imp = QPushButton("+ İmpürite Ekle")
        btn_imp.setStyleSheet(f"""
            QPushButton {{
                border: 1px dashed {RENK_PRIMARY}; border-radius: 5px;
                background: transparent; color: {RENK_PRIMARY};
                font-size: 11px; padding: 3px 10px; margin: 2px 4px;
            }}
            QPushButton:hover {{ background: {RENK_PRIMARY_ACIK}; }}
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
        spek.miktar_birim = self.miktar_w.combo_birim.currentText()
        spek.miktar_tolerans = self.miktar_w.input_tol.text().strip()
        spek.miktar_sb = self.row_miktar.cb_sb.isChecked()
        spek.miktar_raf = self.row_miktar.cb_raf.isChecked()
        spek.teshis_ipk_bulk = self.row_teshis.cb_ipk.isChecked() if not self._dissolusyon_goster else False
        spek.teshis_ipk_cekirdek = self.row_teshis.cb_ipk.isChecked() if self._dissolusyon_goster and not self._kt_goster else getattr(spek, 'teshis_ipk_cekirdek', False)
        spek.teshis_ipk_film = self.row_teshis.cb_ipk.isChecked() if self._dissolusyon_goster and not self._kt_goster else getattr(spek, 'teshis_ipk_film', False)
        if self._kt_goster:
            spek.kt_alt = self.kt_alt.text().strip()
            spek.kt_ust = self.kt_ust.text().strip()
            spek.kt_sb = self.row_kt.cb_sb.isChecked()
            spek.kt_raf = self.row_kt.cb_raf.isChecked()
        if self._dissolusyon_goster:
            spek.dis_min_q = self.dis_q.text().strip()
            spek.dis_sure_dk = self.dis_sure.text().strip()
            spek.dis_sb = self.row_dis.cb_sb.isChecked()
            spek.dis_raf = self.row_dis.cb_raf.isChecked()
        spek.impuriteler = [s.to_model() for s in self._imp_satirlari]
        spek.imp_ipk = self.cb_imp_ipk.isChecked()
        spek.imp_sb = self.cb_imp_sb.isChecked()
        spek.imp_raf = self.cb_imp_raf.isChecked()

    def from_model(self, spek: EtkenMaddeAnalitikSpek):
        self.miktar_w.input_hedef.setText(spek.miktar_hedef)
        idx = self.miktar_w.combo_birim.findText(spek.miktar_birim)
        if idx >= 0:
            self.miktar_w.combo_birim.setCurrentIndex(idx)
        self.miktar_w.input_tol.setText(spek.miktar_tolerans)
        self.row_miktar.cb_sb.setChecked(spek.miktar_sb)
        self.row_miktar.cb_raf.setChecked(spek.miktar_raf)
        if self._kt_goster and hasattr(self, 'kt_alt'):
            self.kt_alt.setText(getattr(spek, 'kt_alt', '85.0'))
            self.kt_ust.setText(getattr(spek, 'kt_ust', '115.0'))
        if self._dissolusyon_goster and hasattr(self, 'dis_q'):
            self.dis_q.setText(spek.dis_min_q)
            self.dis_sure.setText(spek.dis_sure_dk)
        for s in self._imp_satirlari[:]:
            s.deleteLater()
        self._imp_satirlari.clear()
        for imp in spek.impuriteler:
            self._imp_ekle(imp)
        self.cb_imp_ipk.setChecked(spek.imp_ipk)
        self.cb_imp_sb.setChecked(spek.imp_sb)
        self.cb_imp_raf.setChecked(spek.imp_raf)


# ─── Mikrobiyolojik Panel ─────────────────────────────────────────────────────

class MikrobiyolojikPanel(QFrame):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: transparent;")
        l = QHBoxLayout(self)
        l.setContentsMargins(8, 4, 8, 4)
        l.setSpacing(8)
        lbl = QLabel("Mikrobiyolojik Kontrol")
        lbl.setFixedWidth(180)
        lbl.setStyleSheet(f"font-size: 11px; color: {RENK_YAZI_BIRINCIL};")
        l.addWidget(lbl)
        sabit_lbl = QLabel("Sabit: Aerobik ≤10³, Küf-Maya ≤10², E.coli 0 cfu/g")
        sabit_lbl.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_UCUNCUL}; font-style: italic;")
        l.addWidget(sabit_lbl, 1)
        self.cb_ipk = QCheckBox()
        self.cb_sb = QCheckBox()
        self.cb_raf = QCheckBox()
        for cb, w in [(self.cb_ipk, 50), (self.cb_sb, 68), (self.cb_raf, 68)]:
            cb.setStyleSheet(f"""
                QCheckBox::indicator {{
                    width: 14px; height: 14px;
                    border: 1px solid {RENK_KENARLIK}; border-radius: 3px;
                    background: {RENK_BG_BIRINCIL};
                }}
                QCheckBox::indicator:checked {{
                    background: {RENK_PRIMARY}; border-color: {RENK_PRIMARY};
                }}
            """)
            cb.stateChanged.connect(self.degisti)
            c = QWidget()
            c.setFixedWidth(w)
            cl = QHBoxLayout(c)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(cb)
            l.addWidget(c)


# ─── Çekirdek Tablet Sekmesi ──────────────────────────────────────────────────

class CekirdekTabletSekmesi(QScrollArea):
    degisti = pyqtSignal()

    def __init__(self, proje: ProjeVerisi, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._proje = proje
        self._em_paneller: list[EtkenAnalitikPanel] = []

        w = QWidget()
        self._layout = QVBoxLayout(w)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._layout.setSpacing(8)

        self._layout.addWidget(_sek_baslik("Fiziksel Testler"))
        self._layout.addWidget(_satir_baslik())

        # Görünüş
        self.input_gorunus = QLineEdit()
        self.input_gorunus.setPlaceholderText("Örn: Beyaz, yuvarlak, bikonveks tabletler")
        self.input_gorunus.textChanged.connect(self.degisti)
        self.row_gorunus = TestSatiri("Görünüş", self.input_gorunus)
        self.row_gorunus.cb_ipk.setChecked(True)
        self.row_gorunus.cb_sb.setChecked(True)
        self.row_gorunus.cb_raf.setChecked(True)
        self.row_gorunus.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_gorunus)

        # Ortalama Ağırlık
        self.agirlik_w = AgirlikSatiri()
        self.agirlik_w.degisti.connect(self.degisti)
        self.row_agirlik = TestSatiri("Ortalama Ağırlık", self.agirlik_w)
        self.row_agirlik.cb_ipk.setChecked(True)
        self.row_agirlik.cb_sb.setChecked(True)
        self.row_agirlik.cb_raf.setChecked(True)
        self.row_agirlik.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_agirlik)

        # Ağırlık Tekdüzeliği
        self.at_w = AgirlikTekduzeligiWidget()
        self.at_w.degisti.connect(self.degisti)
        self.row_at = TestSatiri("Ağırlık Tekdüzeliği", self.at_w)
        self.row_at.cb_ipk.setChecked(True)
        self.row_at.cb_sb.setChecked(True)
        self.row_at.cb_raf.setChecked(True)
        self.row_at.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_at)

        # Kalınlık
        self.kalinlik_w = KalinlikWidget()
        self.kalinlik_w.degisti.connect(self.degisti)
        self.row_kalinlik = TestSatiri("Kalınlık", self.kalinlik_w)
        self.row_kalinlik.cb_ipk.setChecked(True)
        self.row_kalinlik.cb_sb.setChecked(True)
        self.row_kalinlik.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_kalinlik)

        # Çap
        self.cap_w = CapWidget()
        self.cap_w.degisti.connect(self.degisti)
        self.row_cap = TestSatiri("Çap", self.cap_w)
        self.row_cap.cb_ipk.setChecked(True)
        self.row_cap.cb_sb.setChecked(True)
        self.row_cap.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_cap)

        # Sertlik
        self.sertlik_w = SertlikWidget()
        self.sertlik_w.degisti.connect(self.degisti)
        self.row_sertlik = TestSatiri("Sertlik", self.sertlik_w)
        self.row_sertlik.cb_ipk.setChecked(True)
        self.row_sertlik.cb_sb.setChecked(True)
        self.row_sertlik.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_sertlik)

        # Aşınma
        asinma_w = QWidget()
        al = QHBoxLayout(asinma_w)
        al.setContentsMargins(0, 0, 0, 0)
        al.setSpacing(4)
        al.addWidget(QLabel("Maks."))
        self.input_asinma = QLineEdit("1.0")
        self.input_asinma.setFixedWidth(70)
        self.input_asinma.textChanged.connect(self.degisti)
        al.addWidget(self.input_asinma)
        al.addWidget(QLabel("%"))
        al.addStretch()
        self.row_asinma = TestSatiri("Aşınma", asinma_w)
        self.row_asinma.cb_ipk.setChecked(True)
        self.row_asinma.cb_sb.setChecked(True)
        self.row_asinma.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_asinma)

        # Dağılma (15 dk sabit)
        dagılma_lbl = QLabel("Maksimum 15 dakika  (Tablet Baskı — sabit)")
        dagılma_lbl.setStyleSheet(f"font-size: 11px; color: {RENK_YAZI_IKINCIL};")
        self.row_dagılma = TestSatiri("Dağılma", dagılma_lbl)
        self.row_dagılma.cb_ipk.setChecked(True)
        self.row_dagılma.cb_sb.setChecked(True)
        self.row_dagılma.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_dagılma)

        # Mikrobiyolojik
        self.mikro = MikrobiyolojikPanel()
        self.mikro.degisti.connect(self.degisti)
        self._layout.addWidget(self.mikro)

        # Etken madde analitik paneller
        self._em_container = QWidget()
        self._em_layout = QVBoxLayout(self._em_container)
        self._em_layout.setContentsMargins(0, 0, 0, 0)
        self._em_layout.setSpacing(8)
        self._layout.addWidget(self._em_container)

        self._layout.addStretch()
        self.setWidget(w)
        self._em_panelleri_olustur()

    def _em_panelleri_olustur(self):
        for p in self._em_paneller:
            p.deleteLater()
        self._em_paneller.clear()
        for em in self._proje.etken_maddeler:
            baslik = _sek_baslik(f"{em.ad} — Analitik Testler")
            self._em_layout.addWidget(baslik)
            panel = EtkenAnalitikPanel(em.ad, dissolusyon_goster=True, kt_goster=False)
            panel.degisti.connect(self.degisti)
            self._em_paneller.append(panel)
            self._em_layout.addWidget(panel)

    def to_model(self, spek: CekirdekTabletSpek, analitik_spekler: list):
        spek.gorunus = self.input_gorunus.text().strip()
        spek.gorunus_ipk = self.row_gorunus.cb_ipk.isChecked()
        spek.gorunus_sb = self.row_gorunus.cb_sb.isChecked()
        spek.gorunus_raf = self.row_gorunus.cb_raf.isChecked()
        spek.ort_agirlik_hedef_mg = self.agirlik_w.input_hedef.text().strip()
        spek.ort_agirlik_tolerans = self.agirlik_w.input_tol.text().strip()
        spek.ort_agirlik_ipk = self.row_agirlik.cb_ipk.isChecked()
        spek.ort_agirlik_sb = self.row_agirlik.cb_sb.isChecked()
        spek.ort_agirlik_raf = self.row_agirlik.cb_raf.isChecked()
        spek.at_l1_alt = self.at_w.l1_alt.text().strip()
        spek.at_l1_ust = self.at_w.l1_ust.text().strip()
        spek.at_l2_alt = self.at_w.l2_alt.text().strip()
        spek.at_l2_ust = self.at_w.l2_ust.text().strip()
        spek.at_ipk = self.row_at.cb_ipk.isChecked()
        spek.at_sb = self.row_at.cb_sb.isChecked()
        spek.at_raf = self.row_at.cb_raf.isChecked()
        spek.kalinlik_hedef = self.kalinlik_w.hedef.text().strip()
        spek.kalinlik_alt = self.kalinlik_w.alt.text().strip()
        spek.kalinlik_ust = self.kalinlik_w.ust.text().strip()
        spek.kalinlik_ipk = self.row_kalinlik.cb_ipk.isChecked()
        spek.kalinlik_sb = self.row_kalinlik.cb_sb.isChecked()
        spek.cap_hedef = self.cap_w.hedef.text().strip()
        spek.cap_alt = self.cap_w.alt.text().strip()
        spek.cap_ust = self.cap_w.ust.text().strip()
        spek.cap_ipk = self.row_cap.cb_ipk.isChecked()
        spek.cap_sb = self.row_cap.cb_sb.isChecked()
        spek.sertlik_min = self.sertlik_w.input_min.text().strip()
        spek.sertlik_max = self.sertlik_w.input_max.text().strip()
        spek.sertlik_ipk = self.row_sertlik.cb_ipk.isChecked()
        spek.sertlik_sb = self.row_sertlik.cb_sb.isChecked()
        spek.asinma_max = self.input_asinma.text().strip()
        spek.asinma_ipk = self.row_asinma.cb_ipk.isChecked()
        spek.asinma_sb = self.row_asinma.cb_sb.isChecked()
        spek.dagılma_ipk = self.row_dagılma.cb_ipk.isChecked()
        spek.dagılma_sb = self.row_dagılma.cb_sb.isChecked()
        spek.mikro_ipk = self.mikro.cb_ipk.isChecked()
        spek.mikro_sb = self.mikro.cb_sb.isChecked()
        spek.mikro_raf = self.mikro.cb_raf.isChecked()
        for i, panel in enumerate(self._em_paneller):
            if i < len(analitik_spekler):
                panel.to_model(analitik_spekler[i])

    def from_model(self, spek: CekirdekTabletSpek, analitik_spekler: list):
        self.input_gorunus.setText(spek.gorunus)
        self.row_gorunus.cb_ipk.setChecked(spek.gorunus_ipk)
        self.row_gorunus.cb_sb.setChecked(spek.gorunus_sb)
        self.row_gorunus.cb_raf.setChecked(spek.gorunus_raf)
        self.agirlik_w.input_hedef.setText(spek.ort_agirlik_hedef_mg)
        self.agirlik_w.input_tol.setText(spek.ort_agirlik_tolerans)
        self.row_agirlik.cb_ipk.setChecked(spek.ort_agirlik_ipk)
        self.row_agirlik.cb_sb.setChecked(spek.ort_agirlik_sb)
        self.row_agirlik.cb_raf.setChecked(spek.ort_agirlik_raf)
        self.at_w.l1_alt.setText(spek.at_l1_alt)
        self.at_w.l1_ust.setText(spek.at_l1_ust)
        self.at_w.l2_alt.setText(spek.at_l2_alt)
        self.at_w.l2_ust.setText(spek.at_l2_ust)
        self.row_at.cb_ipk.setChecked(spek.at_ipk)
        self.row_at.cb_sb.setChecked(spek.at_sb)
        self.row_at.cb_raf.setChecked(spek.at_raf)
        for inp, val in [(self.kalinlik_w.hedef, spek.kalinlik_hedef),
                         (self.kalinlik_w.alt, spek.kalinlik_alt),
                         (self.kalinlik_w.ust, spek.kalinlik_ust)]:
            inp.blockSignals(True)
            inp.setText(val)
            inp.blockSignals(False)
        self.row_kalinlik.cb_ipk.setChecked(spek.kalinlik_ipk)
        self.row_kalinlik.cb_sb.setChecked(spek.kalinlik_sb)
        for inp, val in [(self.cap_w.hedef, spek.cap_hedef),
                         (self.cap_w.alt, spek.cap_alt),
                         (self.cap_w.ust, spek.cap_ust)]:
            inp.blockSignals(True)
            inp.setText(val)
            inp.blockSignals(False)
        self.row_cap.cb_ipk.setChecked(spek.cap_ipk)
        self.row_cap.cb_sb.setChecked(spek.cap_sb)
        self.sertlik_w.input_min.setText(spek.sertlik_min)
        self.sertlik_w.input_max.setText(getattr(spek, 'sertlik_max', ''))
        self.row_sertlik.cb_ipk.setChecked(spek.sertlik_ipk)
        self.row_sertlik.cb_sb.setChecked(spek.sertlik_sb)
        self.input_asinma.setText(spek.asinma_max)
        self.row_asinma.cb_ipk.setChecked(spek.asinma_ipk)
        self.row_asinma.cb_sb.setChecked(spek.asinma_sb)
        self.row_dagılma.cb_ipk.setChecked(spek.dagılma_ipk)
        self.row_dagılma.cb_sb.setChecked(spek.dagılma_sb)
        self.mikro.cb_ipk.setChecked(spek.mikro_ipk)
        self.mikro.cb_sb.setChecked(spek.mikro_sb)
        self.mikro.cb_raf.setChecked(spek.mikro_raf)
        for i, panel in enumerate(self._em_paneller):
            if i < len(analitik_spekler):
                panel.from_model(analitik_spekler[i])


# ─── Film Tablet Sekmesi ──────────────────────────────────────────────────────

class FilmTabletSekmesi(QScrollArea):
    degisti = pyqtSignal()

    def __init__(self, proje: ProjeVerisi, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._proje = proje
        self._em_paneller: list[EtkenAnalitikPanel] = []

        w = QWidget()
        self._layout = QVBoxLayout(w)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._layout.setSpacing(8)

        self._layout.addWidget(_sek_baslik("Fiziksel Testler"))
        self._layout.addWidget(_satir_baslik())

        # Görünüş
        self.input_gorunus = QLineEdit()
        self.input_gorunus.setPlaceholderText("Örn: Pembe, oblong, bikonveks film kaplı tabletler")
        self.input_gorunus.textChanged.connect(self.degisti)
        self.row_gorunus = TestSatiri("Görünüş", self.input_gorunus)
        self.row_gorunus.cb_ipk.setChecked(True)
        self.row_gorunus.cb_sb.setChecked(True)
        self.row_gorunus.cb_raf.setChecked(True)
        self.row_gorunus.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_gorunus)

        # Ortalama Ağırlık
        self.agirlik_w = AgirlikSatiri()
        self.agirlik_w.degisti.connect(self.degisti)
        self.row_agirlik = TestSatiri("Ortalama Ağırlık", self.agirlik_w)
        self.row_agirlik.cb_ipk.setChecked(True)
        self.row_agirlik.cb_sb.setChecked(True)
        self.row_agirlik.cb_raf.setChecked(True)
        self.row_agirlik.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_agirlik)

        # Ağırlık Tekdüzeliği
        self.at_w = AgirlikTekduzeligiWidget()
        self.at_w.degisti.connect(self.degisti)
        self.row_at = TestSatiri("Ağırlık Tekdüzeliği", self.at_w)
        self.row_at.cb_ipk.setChecked(True)
        self.row_at.cb_sb.setChecked(True)
        self.row_at.cb_raf.setChecked(True)
        self.row_at.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_at)

        # Dağılma (30 dk sabit)
        dagılma_lbl = QLabel("Maksimum 30 dakika  (Film Kaplama — sabit)")
        dagılma_lbl.setStyleSheet(f"font-size: 11px; color: {RENK_YAZI_IKINCIL};")
        self.row_dagılma = TestSatiri("Dağılma", dagılma_lbl)
        self.row_dagılma.cb_ipk.setChecked(True)
        self.row_dagılma.cb_sb.setChecked(True)
        self.row_dagılma.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_dagılma)

        # Mikrobiyolojik
        self.mikro = MikrobiyolojikPanel()
        self.mikro.degisti.connect(self.degisti)
        self._layout.addWidget(self.mikro)

        # Etken madde analitik paneller
        self._em_container = QWidget()
        self._em_layout = QVBoxLayout(self._em_container)
        self._em_layout.setContentsMargins(0, 0, 0, 0)
        self._em_layout.setSpacing(8)
        self._layout.addWidget(self._em_container)
        self._layout.addStretch()
        self.setWidget(w)
        self._em_panelleri_olustur()

    def _em_panelleri_olustur(self):
        for p in self._em_paneller:
            p.deleteLater()
        self._em_paneller.clear()
        for em in self._proje.etken_maddeler:
            self._em_layout.addWidget(_sek_baslik(f"{em.ad} — Analitik Testler"))
            panel = EtkenAnalitikPanel(em.ad, dissolusyon_goster=True, kt_goster=False)
            panel.degisti.connect(self.degisti)
            self._em_paneller.append(panel)
            self._em_layout.addWidget(panel)

    def to_model(self, spek: FilmTabletSpek, analitik_spekler: list):
        spek.gorunus = self.input_gorunus.text().strip()
        spek.gorunus_ipk = self.row_gorunus.cb_ipk.isChecked()
        spek.gorunus_sb = self.row_gorunus.cb_sb.isChecked()
        spek.gorunus_raf = self.row_gorunus.cb_raf.isChecked()
        spek.ort_agirlik_hedef_mg = self.agirlik_w.input_hedef.text().strip()
        spek.ort_agirlik_tolerans = self.agirlik_w.input_tol.text().strip()
        spek.ort_agirlik_ipk = self.row_agirlik.cb_ipk.isChecked()
        spek.ort_agirlik_sb = self.row_agirlik.cb_sb.isChecked()
        spek.ort_agirlik_raf = self.row_agirlik.cb_raf.isChecked()
        spek.at_l1_alt = self.at_w.l1_alt.text().strip()
        spek.at_l1_ust = self.at_w.l1_ust.text().strip()
        spek.at_l2_alt = self.at_w.l2_alt.text().strip()
        spek.at_l2_ust = self.at_w.l2_ust.text().strip()
        spek.at_ipk = self.row_at.cb_ipk.isChecked()
        spek.at_sb = self.row_at.cb_sb.isChecked()
        spek.at_raf = self.row_at.cb_raf.isChecked()
        spek.dagılma_ipk = self.row_dagılma.cb_ipk.isChecked()
        spek.dagılma_sb = self.row_dagılma.cb_sb.isChecked()
        spek.mikro_ipk = self.mikro.cb_ipk.isChecked()
        spek.mikro_sb = self.mikro.cb_sb.isChecked()
        spek.mikro_raf = self.mikro.cb_raf.isChecked()
        for i, panel in enumerate(self._em_paneller):
            if i < len(analitik_spekler):
                panel.to_model(analitik_spekler[i])

    def from_model(self, spek: FilmTabletSpek, analitik_spekler: list):
        self.input_gorunus.setText(spek.gorunus)
        self.row_gorunus.cb_ipk.setChecked(spek.gorunus_ipk)
        self.row_gorunus.cb_sb.setChecked(spek.gorunus_sb)
        self.row_gorunus.cb_raf.setChecked(spek.gorunus_raf)
        self.agirlik_w.input_hedef.setText(spek.ort_agirlik_hedef_mg)
        self.agirlik_w.input_tol.setText(spek.ort_agirlik_tolerans)
        self.row_agirlik.cb_ipk.setChecked(spek.ort_agirlik_ipk)
        self.row_agirlik.cb_sb.setChecked(spek.ort_agirlik_sb)
        self.row_agirlik.cb_raf.setChecked(spek.ort_agirlik_raf)
        self.at_w.l1_alt.setText(spek.at_l1_alt)
        self.at_w.l1_ust.setText(spek.at_l1_ust)
        self.at_w.l2_alt.setText(spek.at_l2_alt)
        self.at_w.l2_ust.setText(spek.at_l2_ust)
        self.row_at.cb_ipk.setChecked(spek.at_ipk)
        self.row_at.cb_sb.setChecked(spek.at_sb)
        self.row_at.cb_raf.setChecked(spek.at_raf)
        self.row_dagılma.cb_ipk.setChecked(spek.dagılma_ipk)
        self.row_dagılma.cb_sb.setChecked(spek.dagılma_sb)
        self.mikro.cb_ipk.setChecked(spek.mikro_ipk)
        self.mikro.cb_sb.setChecked(spek.mikro_sb)
        self.mikro.cb_raf.setChecked(spek.mikro_raf)
        for i, panel in enumerate(self._em_paneller):
            if i < len(analitik_spekler):
                panel.from_model(analitik_spekler[i])


# ─── Bulk Katman Sekmesi ──────────────────────────────────────────────────────

class BulkKatmanSekmesi(QScrollArea):
    """
    Tek bir bulk katmanı için sekme.
    İçerik: Genel (Görünüş, Elek, Bulk/Tap Dansite) +
            Her etken için analitik (Teşhis, Miktar, KT, İlgili Bileşikler) +
            Katman Mikrobiyolojik
    """
    degisti = pyqtSignal()

    def __init__(self, katman_spek: BulkKatmanSpek,
                 proje: ProjeVerisi, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._katman_spek = katman_spek
        self._proje = proje
        self._em_paneller: list[EtkenAnalitikPanel] = []

        w = QWidget()
        self._layout = QVBoxLayout(w)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._layout.setSpacing(8)

        # Genel bölüm
        self._layout.addWidget(_sek_baslik("Genel — Katman Testleri"))
        self._layout.addWidget(_satir_baslik())

        # Görünüş
        self.input_gorunus = QLineEdit()
        self.input_gorunus.setPlaceholderText("Örn: Beyaz renkli toz")
        self.input_gorunus.textChanged.connect(self.degisti)
        self.row_gorunus = TestSatiri("Görünüş", self.input_gorunus,
                                      ipk=True, sb=False, raf=False)
        self.row_gorunus.cb_ipk.setChecked(True)
        self.row_gorunus.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_gorunus)

        # Elek Testi
        elek_lbl = QLabel("Bilgi amaçlıdır.")
        elek_lbl.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_UCUNCUL}; font-style: italic;")
        self.row_elek = TestSatiri("Elek Testi", elek_lbl,
                                   ipk=True, sb=False, raf=False)
        self.row_elek.cb_ipk.setChecked(True)
        self.row_elek.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_elek)

        # Bulk Dansite
        bulk_lbl = QLabel("Bilgi amaçlıdır.")
        bulk_lbl.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_UCUNCUL}; font-style: italic;")
        self.row_bulk = TestSatiri("Bulk Dansite", bulk_lbl,
                                   ipk=True, sb=False, raf=False)
        self.row_bulk.cb_ipk.setChecked(True)
        self.row_bulk.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_bulk)

        # Tap Dansite
        tap_lbl = QLabel("Bilgi amaçlıdır.")
        tap_lbl.setStyleSheet(f"font-size: 10px; color: {RENK_YAZI_UCUNCUL}; font-style: italic;")
        self.row_tap = TestSatiri("Tap Dansite", tap_lbl,
                                  ipk=True, sb=False, raf=False)
        self.row_tap.cb_ipk.setChecked(True)
        self.row_tap.degisti.connect(self.degisti)
        self._layout.addWidget(self.row_tap)

        # Mikrobiyolojik — katman bazında tek
        self._layout.addWidget(_sek_baslik("Mikrobiyolojik Kontrol — Katman"))
        self.mikro = MikrobiyolojikPanel()
        self.mikro.degisti.connect(self.degisti)
        self._layout.addWidget(self.mikro)

        # Etken madde analitik paneller
        self._em_container = QWidget()
        self._em_layout = QVBoxLayout(self._em_container)
        self._em_layout.setContentsMargins(0, 0, 0, 0)
        self._em_layout.setSpacing(8)
        self._layout.addWidget(self._em_container)
        self._layout.addStretch()
        self.setWidget(w)
        self._em_panelleri_olustur()

    def _em_panelleri_olustur(self):
        for p in self._em_paneller:
            p.deleteLater()
        self._em_paneller.clear()
        for idx in self._katman_spek.etken_indeksler:
            if idx < len(self._proje.etken_maddeler):
                em = self._proje.etken_maddeler[idx]
                self._em_layout.addWidget(
                    _sek_baslik(f"{em.ad} — Analitik Testler (Bulk)"))
                panel = EtkenAnalitikPanel(em.ad, dissolusyon_goster=False,
                                           kt_goster=True)
                panel.degisti.connect(self.degisti)
                self._em_paneller.append(panel)
                self._em_layout.addWidget(panel)

    def to_model(self, analitik_spekler: list):
        self._katman_spek.gorunus = self.input_gorunus.text().strip()
        self._katman_spek.gorunus_ipk = self.row_gorunus.cb_ipk.isChecked()
        self._katman_spek.elek_ipk = self.row_elek.cb_ipk.isChecked()
        self._katman_spek.bulk_dans_ipk = self.row_bulk.cb_ipk.isChecked()
        self._katman_spek.tap_dans_ipk = self.row_tap.cb_ipk.isChecked()
        self._katman_spek.mikro_ipk = self.mikro.cb_ipk.isChecked()
        self._katman_spek.mikro_sb = self.mikro.cb_sb.isChecked()
        self._katman_spek.mikro_raf = self.mikro.cb_raf.isChecked()
        for i, (panel, idx) in enumerate(
                zip(self._em_paneller, self._katman_spek.etken_indeksler)):
            if idx < len(analitik_spekler):
                panel.to_model(analitik_spekler[idx])

    def from_model(self, analitik_spekler: list):
        self.input_gorunus.setText(self._katman_spek.gorunus)
        self.row_gorunus.cb_ipk.setChecked(self._katman_spek.gorunus_ipk)
        self.row_elek.cb_ipk.setChecked(self._katman_spek.elek_ipk)
        self.row_bulk.cb_ipk.setChecked(self._katman_spek.bulk_dans_ipk)
        self.row_tap.cb_ipk.setChecked(self._katman_spek.tap_dans_ipk)
        self.mikro.cb_ipk.setChecked(self._katman_spek.mikro_ipk)
        self.mikro.cb_sb.setChecked(self._katman_spek.mikro_sb)
        self.mikro.cb_raf.setChecked(self._katman_spek.mikro_raf)
        for panel, idx in zip(self._em_paneller,
                               self._katman_spek.etken_indeksler):
            if idx < len(analitik_spekler):
                panel.from_model(analitik_spekler[idx])


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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            background: {RENK_BG_BIRINCIL};
            border-bottom: 1px solid {RENK_KENARLIK};
        """)
        toolbar.setFixedHeight(46)
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(16, 0, 16, 0)
        tb.setSpacing(8)

        lbl = QLabel("Spec Kartı")
        lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {RENK_YAZI_BIRINCIL};")
        tb.addWidget(lbl)
        sep = QLabel("/")
        sep.setStyleSheet(f"color: {RENK_KENARLIK};")
        tb.addWidget(sep)
        alt_lbl = QLabel("Spesifikasyon tanımları")
        alt_lbl.setStyleSheet(f"font-size: 12px; color: {RENK_YAZI_IKINCIL};")
        tb.addWidget(alt_lbl)
        tb.addStretch()

        self.lbl_degisiklik = QLabel("")
        self.lbl_degisiklik.setVisible(False)
        self.lbl_degisiklik.setStyleSheet(f"""
            font-size: 11px; color: {RENK_PRIMARY_KOYU};
            background: {RENK_PRIMARY_ACIK};
            border-radius: 4px; padding: 2px 8px;
        """)
        tb.addWidget(self.lbl_degisiklik)

        btn_kaydet = QPushButton("💾  Kaydet")
        btn_kaydet.setFixedHeight(30)
        btn_kaydet.setMinimumWidth(90)
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{
                background: {RENK_PRIMARY}; color: #FFFFFF;
                border: none; border-radius: 6px;
                font-size: 12px; font-weight: bold;
                font-family: {FONT_AILESI}; padding: 0 14px;
            }}
            QPushButton:hover {{ background: {RENK_PRIMARY_KOYU}; }}
        """)
        btn_kaydet.clicked.connect(self._kaydet)
        tb.addWidget(btn_kaydet)
        layout.addWidget(toolbar)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none; background: {RENK_BG_BIRINCIL};
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
        """)
        layout.addWidget(self.tabs, 1)

    def _yukle(self):
        """Proje verisiyle tüm sekmeleri oluşturur."""
        self.tabs.clear()
        self._sekme_cekirdek = None
        self._sekme_film = None
        self._bulk_sekmeleri.clear()

        # Bulk katmanlarını oluştur (ilk açılışta)
        self._proje.bulk_katmanlari_olustur()

        # Çekirdek Tablet
        urun = self._proje.urun_formu
        if urun != UrunFormu.KAPSUL.value:
            self._sekme_cekirdek = CekirdekTabletSekmesi(self._proje)
            self._sekme_cekirdek.degisti.connect(self._on_degisti)
            self._sekme_cekirdek.from_model(
                self._proje.cekirdek_spek,
                self._proje.etken_analitik_spekler
            )
            self.tabs.addTab(self._sekme_cekirdek, "Çekirdek Tablet")

        # Film Tablet
        film_formlar = [UrunFormu.FILM_TABLET.value, UrunFormu.KAPSUL_FILM_TABLET.value]
        if urun in film_formlar:
            self._sekme_film = FilmTabletSekmesi(self._proje)
            self._sekme_film.degisti.connect(self._on_degisti)
            self._sekme_film.from_model(
                self._proje.film_spek,
                self._proje.etken_analitik_spekler
            )
            self.tabs.addTab(self._sekme_film, "Film Tablet")

        # Bulk Katmanları
        for katman_spek in self._proje.bulk_katmanlar:
            sekme = BulkKatmanSekmesi(katman_spek, self._proje)
            sekme.degisti.connect(self._on_degisti)
            sekme.from_model(self._proje.etken_analitik_spekler)
            self._bulk_sekmeleri.append(sekme)
            self.tabs.addTab(sekme, katman_spek.katman_adi)

        self._degisiklik_var = False
        self.lbl_degisiklik.setVisible(False)

    def _on_degisti(self):
        self._degisiklik_var = True
        self.lbl_degisiklik.setText("● Kaydedilmemiş değişiklik")
        self.lbl_degisiklik.setStyleSheet(f"""
            font-size: 11px; color: {RENK_PRIMARY_KOYU};
            background: {RENK_PRIMARY_ACIK};
            border-radius: 4px; padding: 2px 8px;
        """)
        self.lbl_degisiklik.setVisible(True)
        self.degisti.emit()

    def _kaydet(self):
        # Analitik speklerin sayısı etken madde sayısıyla eşit olmalı
        n = len(self._proje.etken_maddeler)
        while len(self._proje.etken_analitik_spekler) < n:
            em = self._proje.etken_maddeler[len(self._proje.etken_analitik_spekler)]
            self._proje.etken_analitik_spekler.append(
                EtkenMaddeAnalitikSpek(ad=em.ad))

        if self._sekme_cekirdek:
            self._sekme_cekirdek.to_model(
                self._proje.cekirdek_spek,
                self._proje.etken_analitik_spekler
            )
        if self._sekme_film:
            self._sekme_film.to_model(
                self._proje.film_spek,
                self._proje.etken_analitik_spekler
            )
        for sekme in self._bulk_sekmeleri:
            sekme.to_model(self._proje.etken_analitik_spekler)

        self._degisiklik_var = False
        self.lbl_degisiklik.setText("✓ Kaydedildi")
        self.lbl_degisiklik.setStyleSheet(f"""
            font-size: 11px; color: {RENK_YESIL};
            background: {RENK_YESIL_BG};
            border-radius: 4px; padding: 2px 8px;
        """)
        self.lbl_degisiklik.setVisible(True)
        self.kaydedildi.emit()

    def proje_guncelle(self, proje: ProjeVerisi):
        self._proje = proje
        self._yukle()

    def degisiklik_var_mi(self) -> bool:
        return self._degisiklik_var
