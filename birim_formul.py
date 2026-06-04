"""
PV-DOC — Birim Formül ve Ürün Bilgileri (Modül 3)
Tablo 1: Birim Formül (satır ekle/sil/sırala, % İçerik ve kg/seri otomatik)
Tablo 2: Kapsanan Ürünler (seri bilgileri)
Notlar  : PVP ve PVR için ayrı, dinamik not listesi
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QLineEdit, QPushButton, QScrollArea, QTabWidget,
    QComboBox, QSizePolicy, QMessageBox, QAbstractItemView,
    QTableWidget, QTableWidgetItem, QHeaderView, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QFont, QColor, QBrush, QDrag

from core.models import ProjeVerisi, UrunFormu, TabletYapisi
from ui.stiller import (
    RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    RENK_YESIL, RENK_YESIL_BG, FONT_AILESI,
    RENK_TURUNCU_BG, RENK_KIRMIZI_BG
)


# ─── Sabitler ────────────────────────────────────────────────────────────────

FONKSIYON_LISTESI = [
    "Etkin madde",
    "Dolgu Ajanı",
    "Bağlayıcı",
    "Dağıtıcı",
    "Lubrikant",
    "Kayıcı",
    "pH Düzenleyici",
    "Kaplama Malzemesi",
    "Çözücü",
    "Boyar Madde",
    "Tatlandırıcı",
    "Koruyucu",
    "Yüzey Aktif Madde",
    "Diğer",
]

# Her ürün formuna göre varsayılan gruplar
GRUP_ADLARI = {
    UrunFormu.TABLET.value: ["Tablet"],
    UrunFormu.FILM_TABLET.value: ["Katman I", "Katman II", "Kaplama"],
    UrunFormu.KAPSUL.value: ["İç Formül", "Kapsül Kabuğu"],
    UrunFormu.KAPSUL_FILM_TABLET.value: ["Katman I", "Katman II", "Kaplama", "Kapsül Kabuğu"],
}

# Sütun indeksleri
COL_DRAG = 0
COL_AD   = 1
COL_FONK = 2
COL_MG   = 3
COL_YUZ  = 4
COL_KG   = 5
COL_SIL  = 6
N_COLS   = 7


# ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────

def _float_veya_sifir(metin: str) -> float:
    try:
        return float(metin.replace(",", "."))
    except (ValueError, AttributeError):
        return 0.0


def _format_sayi(deger: float, ondalik: int = 3) -> str:
    if deger == 0.0:
        return ""
    return f"{deger:.{ondalik}f}".rstrip("0").rstrip(".")


# ─── Satır Widget'ı ───────────────────────────────────────────────────────────

class FormulSatiri:
    """Birim formül tablosundaki tek bir satırın veri modeli."""

    def __init__(
        self,
        ad: str = "",
        fonksiyon: str = "",
        mg_tb: str = "",
        yuzde: str = "",
        kg_seri: str = "",
        grup: str = "",
        manuel_yuzde: bool = False,
        manuel_kg: bool = False,
    ):
        self.ad = ad
        self.fonksiyon = fonksiyon
        self.mg_tb = mg_tb
        self.yuzde = yuzde
        self.kg_seri = kg_seri
        self.grup = grup
        self.manuel_yuzde = manuel_yuzde
        self.manuel_kg = manuel_kg

    def to_dict(self) -> dict:
        return {
            "ad": self.ad,
            "fonksiyon": self.fonksiyon,
            "mg_tb": self.mg_tb,
            "yuzde": self.yuzde,
            "kg_seri": self.kg_seri,
            "grup": self.grup,
            "manuel_yuzde": self.manuel_yuzde,
            "manuel_kg": self.manuel_kg,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FormulSatiri":
        return cls(
            ad=d.get("ad", ""),
            fonksiyon=d.get("fonksiyon", ""),
            mg_tb=d.get("mg_tb", ""),
            yuzde=d.get("yuzde", ""),
            kg_seri=d.get("kg_seri", ""),
            grup=d.get("grup", ""),
            manuel_yuzde=d.get("manuel_yuzde", False),
            manuel_kg=d.get("manuel_kg", False),
        )


# ─── Not Satırı Widget ────────────────────────────────────────────────────────

class NotSatiri(QFrame):
    """Tek bir not: sembol + açıklama + sil butonu."""

    silindi = pyqtSignal(object)
    degisti = pyqtSignal()

    def __init__(self, sembol: str = "", aciklama: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        self.input_sembol = QLineEdit(sembol)
        self.input_sembol.setPlaceholderText("Sembol")
        self.input_sembol.setFixedWidth(80)
        self.input_sembol.setStyleSheet(f"""
            border: 1px solid {RENK_KENARLIK};
            border-radius: 5px;
            padding: 3px 7px;
            font-size: 12px;
            font-family: {FONT_AILESI};
            background: {RENK_BG_BIRINCIL};
        """)
        layout.addWidget(self.input_sembol)

        self.input_aciklama = QLineEdit(aciklama)
        self.input_aciklama.setPlaceholderText("Açıklama")
        self.input_aciklama.setStyleSheet(f"""
            border: 1px solid {RENK_KENARLIK};
            border-radius: 5px;
            padding: 3px 7px;
            font-size: 12px;
            font-family: {FONT_AILESI};
            background: {RENK_BG_BIRINCIL};
        """)
        layout.addWidget(self.input_aciklama, 1)

        btn_sil = QPushButton("✕")
        btn_sil.setFixedSize(26, 26)
        btn_sil.setStyleSheet(f"""
            QPushButton {{
                border: none; background: transparent;
                color: {RENK_YAZI_UCUNCUL}; font-size: 13px;
            }}
            QPushButton:hover {{
                background: #FCEBEB; color: #A32D2D;
                border-radius: 4px;
            }}
        """)
        btn_sil.clicked.connect(lambda: self.silindi.emit(self))
        layout.addWidget(btn_sil)

        self.input_sembol.textChanged.connect(self.degisti)
        self.input_aciklama.textChanged.connect(self.degisti)

    def to_dict(self) -> dict:
        return {
            "sembol": self.input_sembol.text().strip(),
            "aciklama": self.input_aciklama.text().strip(),
        }


# ─── Not Paneli ───────────────────────────────────────────────────────────────

class NotPaneli(QWidget):
    """PVP veya PVR için dinamik not listesi."""

    degisti = pyqtSignal()

    VARSAYILAN_NOTLAR = [
        {"sembol": "*", "aciklama": "Uçucudur bitmiş üründe yer almaz."},
        {"sembol": "k.m.", "aciklama": "kafi miktarda"},
        {"sembol": "U.Y.", "aciklama": "Uygulama yoktur"},
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._satirlar: list[NotSatiri] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Başlık
        baslik = QFrame()
        baslik.setStyleSheet(f"""
            background: {RENK_BG_IKINCIL};
            border-bottom: 1px solid {RENK_KENARLIK};
        """)
        bl = QHBoxLayout(baslik)
        bl.setContentsMargins(12, 6, 12, 6)
        lbl_s = QLabel("Sembol")
        lbl_s.setFixedWidth(80)
        lbl_s.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {RENK_YAZI_IKINCIL};")
        bl.addWidget(lbl_s)
        lbl_a = QLabel("Açıklama")
        lbl_a.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {RENK_YAZI_IKINCIL};")
        bl.addWidget(lbl_a, 1)
        layout.addWidget(baslik)

        # Satır konteyneri
        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(12, 4, 12, 4)
        self._container_layout.setSpacing(2)
        layout.addWidget(self._container)

        # Ekle butonu
        btn_ekle = QPushButton("+ Not Ekle")
        btn_ekle.setStyleSheet(f"""
            QPushButton {{
                border: 1px dashed {RENK_PRIMARY};
                border-radius: 5px;
                background: transparent;
                color: {RENK_PRIMARY};
                font-size: 11px;
                padding: 4px 12px;
                margin: 4px 12px;
            }}
            QPushButton:hover {{ background: {RENK_PRIMARY_ACIK}; }}
        """)
        btn_ekle.clicked.connect(lambda: self._not_ekle())
        layout.addWidget(btn_ekle)

    def _not_ekle(self, sembol: str = "", aciklama: str = ""):
        satir = NotSatiri(sembol, aciklama, self._container)
        satir.silindi.connect(self._not_sil)
        satir.degisti.connect(self.degisti)
        self._satirlar.append(satir)
        self._container_layout.addWidget(satir)
        self.degisti.emit()

    def _not_sil(self, satir: NotSatiri):
        self._satirlar.remove(satir)
        satir.deleteLater()
        self.degisti.emit()

    def yukle(self, notlar: list):
        for s in self._satirlar[:]:
            s.deleteLater()
        self._satirlar.clear()
        for n in notlar:
            self._not_ekle(n.get("sembol", ""), n.get("aciklama", ""))

    def varsayilan_yukle(self):
        self.yukle(self.VARSAYILAN_NOTLAR)

    def to_list(self) -> list:
        return [s.to_dict() for s in self._satirlar]


# ─── Birim Formül Tablosu ─────────────────────────────────────────────────────

class BirimFormulTablosu(QWidget):
    """
    Birim formül tablosu.
    Gruplar (Katman I / II / Kaplama veya tek Tablet), her grup kendi
    alt toplamını gösterir. Genel toplam en altta.
    % İçerik ve kg/seri otomatik hesaplanır; kullanıcı override edebilir.
    """

    degisti = pyqtSignal()

    def __init__(self, urun_formu: str, seri_boyutu: str = "", parent=None):
        super().__init__(parent)
        self._urun_formu = urun_formu
        self._seri_boyutu = seri_boyutu
        self._gruplar: list[str] = GRUP_ADLARI.get(
            urun_formu, ["Tablet"]
        )
        # {grup_adi: [FormulSatiri]}
        self._veri: dict[str, list[FormulSatiri]] = {
            g: [] for g in self._gruplar
        }
        self._guncelleniyor = False  # reentrance koruması

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tablo
        self._tablo = QTableWidget()
        self._tablo.setColumnCount(N_COLS)
        self._tablo.setHorizontalHeaderLabels([
            "", "Hammadde / Yardımcı Madde", "Fonksiyon",
            "mg/tb", "% İçerik", "kg/seri", ""
        ])
        self._tablo.horizontalHeader().setSectionResizeMode(COL_AD, QHeaderView.ResizeMode.Stretch)
        self._tablo.horizontalHeader().setSectionResizeMode(COL_FONK, QHeaderView.ResizeMode.Stretch)
        self._tablo.setColumnWidth(COL_DRAG, 24)
        self._tablo.setColumnWidth(COL_MG, 80)
        self._tablo.setColumnWidth(COL_YUZ, 75)
        self._tablo.setColumnWidth(COL_KG, 90)
        self._tablo.setColumnWidth(COL_SIL, 32)
        self._tablo.verticalHeader().setVisible(False)
        self._tablo.setShowGrid(True)
        self._tablo.setAlternatingRowColors(False)
        self._tablo.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked |
                                    QAbstractItemView.EditTrigger.SelectedClicked)
        self._tablo.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                font-size: 11px;
                font-family: {FONT_AILESI};
                gridline-color: {RENK_KENARLIK};
            }}
            QTableWidget::item {{
                padding: 2px 6px;
            }}
            QTableWidget::item:selected {{
                background: {RENK_PRIMARY_ACIK};
                color: {RENK_PRIMARY_KOYU};
            }}
            QHeaderView::section {{
                background: {RENK_BG_IKINCIL};
                border: none;
                border-right: 1px solid {RENK_KENARLIK};
                border-bottom: 1px solid {RENK_KENARLIK};
                padding: 4px 6px;
                font-size: 10px;
                font-weight: bold;
                color: {RENK_YAZI_IKINCIL};
            }}
        """)
        self._tablo.cellChanged.connect(self._hucre_degisti)
        layout.addWidget(self._tablo)

        # Alt bilgi
        alt = QFrame()
        alt.setStyleSheet(f"""
            background: {RENK_BG_IKINCIL};
            border-top: 1px solid {RENK_KENARLIK};
        """)
        alt_l = QHBoxLayout(alt)
        alt_l.setContentsMargins(12, 6, 12, 6)
        alt_l.setSpacing(8)

        for grup in self._gruplar:
            btn = QPushButton(f"+ {grup}'a Satır Ekle")
            btn.setStyleSheet(f"""
                QPushButton {{
                    border: 1px solid {RENK_KENARLIK};
                    border-radius: 5px;
                    background: {RENK_BG_BIRINCIL};
                    color: {RENK_YAZI_IKINCIL};
                    font-size: 11px;
                    padding: 4px 10px;
                }}
                QPushButton:hover {{
                    background: {RENK_PRIMARY_ACIK};
                    color: {RENK_PRIMARY};
                    border-color: {RENK_PRIMARY};
                }}
            """)
            btn.clicked.connect(lambda checked, g=grup: self.satir_ekle(g))
            alt_l.addWidget(btn)

        alt_l.addStretch()

        self.lbl_toplam = QLabel("Toplam: — mg/tb")
        self.lbl_toplam.setStyleSheet(f"""
            font-size: 11px;
            font-weight: bold;
            color: {RENK_YAZI_BIRINCIL};
        """)
        alt_l.addWidget(self.lbl_toplam)
        layout.addWidget(alt)

        self._tabloyu_yenile()

    # ── Veri yönetimi ──────────────────────────────────────────────────────

    def satir_ekle(self, grup: str, satir: FormulSatiri = None):
        if satir is None:
            satir = FormulSatiri(grup=grup)
        self._veri[grup].append(satir)
        self._tabloyu_yenile()
        self.degisti.emit()

    def seri_boyutu_guncelle(self, boyut: str):
        self._seri_boyutu = boyut
        self._hesapla_kg()

    def yukle(self, satirlar: list):
        """Kaydedilmiş veriden yükler."""
        for g in self._gruplar:
            self._veri[g] = []
        for d in satirlar:
            g = d.get("grup", self._gruplar[0])
            if g not in self._veri:
                g = self._gruplar[0]
            self._veri[g].append(FormulSatiri.from_dict(d))
        self._tabloyu_yenile()

    def to_list(self) -> list:
        """Tüm satırları dict listesi olarak döner."""
        sonuc = []
        for g in self._gruplar:
            for s in self._veri[g]:
                s.grup = g
                sonuc.append(s.to_dict())
        return sonuc

    # ── Tablo render ───────────────────────────────────────────────────────

    def _tabloyu_yenile(self):
        self._guncelleniyor = True
        self._tablo.clearContents()

        # Toplam satır sayısını hesapla
        # Her grup için: 1 başlık + N veri + 1 alt toplam
        toplam_satir = 0
        for g in self._gruplar:
            toplam_satir += 1 + len(self._veri[g]) + 1
        # Genel toplam
        toplam_satir += 1
        self._tablo.setRowCount(toplam_satir)

        satir_idx = 0
        self._satir_haritasi = {}  # tablo_satır -> (grup, veri_idx)

        for grup in self._gruplar:
            # Grup başlığı
            self._grup_satiri_yaz(satir_idx, grup)
            satir_idx += 1

            # Veri satırları
            for vi, formul_s in enumerate(self._veri[grup]):
                self._veri_satiri_yaz(satir_idx, grup, vi, formul_s)
                self._satir_haritasi[satir_idx] = (grup, vi)
                satir_idx += 1

            # Alt toplam
            self._alt_toplam_yaz(satir_idx, grup)
            satir_idx += 1

        # Genel toplam
        self._genel_toplam_yaz(satir_idx)

        self._guncelleniyor = False
        self._hesapla_yuzde_kg()

    def _grup_satiri_yaz(self, satir: int, grup: str):
        self._tablo.setRowHeight(satir, 28)
        for col in range(N_COLS):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setBackground(QBrush(QColor(RENK_PRIMARY_ACIK)))
            self._tablo.setItem(satir, col, item)

        item_ad = QTableWidgetItem(f"  {grup}")
        item_ad.setFlags(Qt.ItemFlag.NoItemFlags)
        item_ad.setBackground(QBrush(QColor(RENK_PRIMARY_ACIK)))
        item_ad.setForeground(QBrush(QColor(RENK_PRIMARY_KOYU)))
        font = QFont(FONT_AILESI, 10)
        font.setBold(True)
        item_ad.setFont(font)
        self._tablo.setItem(satir, COL_AD, item_ad)

        # "+ Bu gruba satır ekle" butonu
        btn = QPushButton("+")
        btn.setFixedSize(22, 22)
        btn.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid {RENK_PRIMARY};
                border-radius: 3px;
                background: {RENK_PRIMARY_ACIK};
                color: {RENK_PRIMARY};
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {RENK_PRIMARY}; color: white; }}
        """)
        btn.clicked.connect(lambda checked, g=grup: self.satir_ekle(g))
        w = QWidget()
        wl = QHBoxLayout(w)
        wl.setContentsMargins(1, 2, 1, 2)
        wl.addWidget(btn)
        self._tablo.setCellWidget(satir, COL_SIL, w)

    def _veri_satiri_yaz(self, satir: int, grup: str, vi: int, s: FormulSatiri):
        self._tablo.setRowHeight(satir, 30)

        # Sürükleme ikonu
        drag_item = QTableWidgetItem("⠿")
        drag_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        drag_item.setForeground(QBrush(QColor(RENK_YAZI_UCUNCUL)))
        drag_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tablo.setItem(satir, COL_DRAG, drag_item)

        # Ad
        item_ad = QTableWidgetItem(s.ad)
        self._tablo.setItem(satir, COL_AD, item_ad)

        # Fonksiyon — ComboBox
        combo = QComboBox()
        combo.addItems(FONKSIYON_LISTESI)
        combo.setEditable(True)
        combo.setStyleSheet(f"""
            QComboBox {{
                border: none;
                font-size: 11px;
                font-family: {FONT_AILESI};
                padding: 1px 4px;
                background: transparent;
            }}
            QComboBox::drop-down {{ border: none; padding-right: 4px; }}
        """)
        if s.fonksiyon in FONKSIYON_LISTESI:
            combo.setCurrentText(s.fonksiyon)
        elif s.fonksiyon:
            combo.setCurrentText(s.fonksiyon)
        combo.currentTextChanged.connect(
            lambda txt, g=grup, i=vi: self._fonk_degisti(g, i, txt)
        )
        self._tablo.setCellWidget(satir, COL_FONK, combo)

        # mg/tb
        item_mg = QTableWidgetItem(s.mg_tb)
        item_mg.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._tablo.setItem(satir, COL_MG, item_mg)

        # % İçerik — otomatik (açık gri) ya da manuel (normal)
        item_yuz = QTableWidgetItem(s.yuzde)
        item_yuz.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if not s.manuel_yuzde:
            item_yuz.setForeground(QBrush(QColor(RENK_YAZI_UCUNCUL)))
        self._tablo.setItem(satir, COL_YUZ, item_yuz)

        # kg/seri — otomatik (açık gri) ya da manuel (normal)
        item_kg = QTableWidgetItem(s.kg_seri)
        item_kg.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if not s.manuel_kg:
            item_kg.setForeground(QBrush(QColor(RENK_YAZI_UCUNCUL)))
        self._tablo.setItem(satir, COL_KG, item_kg)

        # Sil butonu
        btn_sil = QPushButton("✕")
        btn_sil.setFixedSize(22, 22)
        btn_sil.setStyleSheet(f"""
            QPushButton {{
                border: none; background: transparent;
                color: {RENK_YAZI_UCUNCUL}; font-size: 12px;
            }}
            QPushButton:hover {{
                background: #FCEBEB; color: #A32D2D;
                border-radius: 3px;
            }}
        """)
        btn_sil.clicked.connect(lambda checked, g=grup, i=vi: self._satir_sil(g, i))
        w = QWidget()
        wl = QHBoxLayout(w)
        wl.setContentsMargins(2, 2, 2, 2)
        wl.addWidget(btn_sil)
        self._tablo.setCellWidget(satir, COL_SIL, w)

    def _alt_toplam_yaz(self, satir: int, grup: str):
        self._tablo.setRowHeight(satir, 26)
        for col in range(N_COLS):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setBackground(QBrush(QColor(RENK_BG_IKINCIL)))
            self._tablo.setItem(satir, col, item)

        toplam_mg = sum(_float_veya_sifir(s.mg_tb) for s in self._veri[grup])
        toplam_kg = sum(_float_veya_sifir(s.kg_seri) for s in self._veri[grup])

        font = QFont(FONT_AILESI, 10)
        font.setBold(True)

        item_lbl = QTableWidgetItem(f"  {grup} Toplam")
        item_lbl.setFlags(Qt.ItemFlag.NoItemFlags)
        item_lbl.setBackground(QBrush(QColor(RENK_BG_IKINCIL)))
        item_lbl.setForeground(QBrush(QColor(RENK_YAZI_IKINCIL)))
        item_lbl.setFont(font)
        self._tablo.setItem(satir, COL_AD, item_lbl)

        for col, val in [(COL_MG, toplam_mg), (COL_KG, toplam_kg)]:
            txt = _format_sayi(val, 3) if val else ""
            item = QTableWidgetItem(txt)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setBackground(QBrush(QColor(RENK_BG_IKINCIL)))
            item.setForeground(QBrush(QColor(RENK_YAZI_IKINCIL)))
            item.setFont(font)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._tablo.setItem(satir, col, item)

    def _genel_toplam_yaz(self, satir: int):
        self._tablo.setRowHeight(satir, 30)

        tum_satirlar = [s for g in self._gruplar for s in self._veri[g]]
        toplam_mg = sum(_float_veya_sifir(s.mg_tb) for s in tum_satirlar)
        toplam_kg = sum(_float_veya_sifir(s.kg_seri) for s in tum_satirlar)

        renk = QColor("#F0F8EC")
        font = QFont(FONT_AILESI, 11)
        font.setBold(True)

        for col in range(N_COLS):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setBackground(QBrush(renk))
            self._tablo.setItem(satir, col, item)

        item_lbl = QTableWidgetItem("  Toplam Ağırlık")
        item_lbl.setFlags(Qt.ItemFlag.NoItemFlags)
        item_lbl.setBackground(QBrush(renk))
        item_lbl.setForeground(QBrush(QColor(RENK_YESIL)))
        item_lbl.setFont(font)
        self._tablo.setItem(satir, COL_AD, item_lbl)

        for col, val in [(COL_MG, toplam_mg), (COL_KG, toplam_kg)]:
            txt = _format_sayi(val, 3) if val else "—"
            item = QTableWidgetItem(txt)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setBackground(QBrush(renk))
            item.setForeground(QBrush(QColor(RENK_YESIL)))
            item.setFont(font)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._tablo.setItem(satir, col, item)

        # Durum etiketi
        if toplam_mg > 0:
            self.lbl_toplam.setText(f"Toplam: {_format_sayi(toplam_mg, 3)} mg/tb")
        else:
            self.lbl_toplam.setText("Toplam: — mg/tb")

    # ── Hesaplamalar ───────────────────────────────────────────────────────

    def _hesapla_yuzde_kg(self):
        """Tüm satırlar için % İçerik ve kg/seri otomatik hesaplar."""
        tum = [s for g in self._gruplar for s in self._veri[g]]
        toplam_mg = sum(_float_veya_sifir(s.mg_tb) for s in tum)

        try:
            seri_boy = _float_veya_sifir(self._seri_boyutu.replace(".", "").replace(",", ""))
            if seri_boy == 0:
                # Sayısal değil — belki "150.000 ftb" gibi
                # Sadece sayıları al
                import re
                m = re.search(r"[\d.,]+", self._seri_boyutu.replace(".", "").replace(",", ""))
                seri_boy = float(m.group()) if m else 0
        except Exception:
            seri_boy = 0

        for grup in self._gruplar:
            for s in self._veri[grup]:
                mg = _float_veya_sifir(s.mg_tb)
                if not s.manuel_yuzde:
                    if toplam_mg > 0 and mg > 0:
                        s.yuzde = _format_sayi(mg / toplam_mg * 100, 2)
                    else:
                        s.yuzde = ""
                if not s.manuel_kg:
                    if seri_boy > 0 and mg > 0:
                        s.kg_seri = _format_sayi(mg * seri_boy / 1_000_000, 3)
                    else:
                        s.kg_seri = ""

        # Tabloyu güncelle
        self._guncelleniyor = True
        for tablo_satir, (grup, vi) in self._satir_haritasi.items():
            s = self._veri[grup][vi]
            item_yuz = self._tablo.item(tablo_satir, COL_YUZ)
            item_kg  = self._tablo.item(tablo_satir, COL_KG)
            if item_yuz:
                item_yuz.setText(s.yuzde)
                clr = RENK_YAZI_BIRINCIL if s.manuel_yuzde else RENK_YAZI_UCUNCUL
                item_yuz.setForeground(QBrush(QColor(clr)))
            if item_kg:
                item_kg.setText(s.kg_seri)
                clr = RENK_YAZI_BIRINCIL if s.manuel_kg else RENK_YAZI_UCUNCUL
                item_kg.setForeground(QBrush(QColor(clr)))
        self._guncelleniyor = False

        # Toplam ve alt toplamları güncelle
        self._tablo.blockSignals(True)
        satir_idx = 0
        for grup in self._gruplar:
            satir_idx += 1  # başlık
            satir_idx += len(self._veri[grup])  # veriler
            self._alt_toplam_yaz(satir_idx, grup)
            satir_idx += 1
        self._genel_toplam_yaz(satir_idx)
        self._tablo.blockSignals(False)

    def _hesapla_kg(self):
        """Sadece kg/seri yeniden hesaplar (seri boyutu değişince)."""
        self._hesapla_yuzde_kg()

    # ── Olay İşleyiciler ───────────────────────────────────────────────────

    def _hucre_degisti(self, satir: int, sutun: int):
        if self._guncelleniyor:
            return
        if satir not in self._satir_haritasi:
            return

        grup, vi = self._satir_haritasi[satir]
        s = self._veri[grup][vi]
        item = self._tablo.item(satir, sutun)
        if not item:
            return
        metin = item.text().strip()

        if sutun == COL_AD:
            s.ad = metin
        elif sutun == COL_MG:
            s.mg_tb = metin
            s.manuel_yuzde = False
            s.manuel_kg = False
            self._hesapla_yuzde_kg()
        elif sutun == COL_YUZ:
            s.yuzde = metin
            s.manuel_yuzde = bool(metin)
        elif sutun == COL_KG:
            s.kg_seri = metin
            s.manuel_kg = bool(metin)

        self.degisti.emit()

    def _fonk_degisti(self, grup: str, vi: int, metin: str):
        if self._guncelleniyor:
            return
        if vi < len(self._veri[grup]):
            self._veri[grup][vi].fonksiyon = metin
            self.degisti.emit()

    def _satir_sil(self, grup: str, vi: int):
        if vi < len(self._veri[grup]):
            self._veri[grup].pop(vi)
            self._tabloyu_yenile()
            self.degisti.emit()


# ─── Kapsanan Ürünler (Tablo 2) ───────────────────────────────────────────────

class KapsananUrunlerWidget(QWidget):
    """Tablo 2 — seri bilgileri, proje verilerinden otomatik gelir."""

    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        aciklama = QLabel(
            "Bu tablo proje oluştururken girdiğiniz seri bilgilerinden otomatik doldurulur. "
            "Değiştirmek için Proje Özeti sayfasını kullanın."
        )
        aciklama.setWordWrap(True)
        aciklama.setStyleSheet(f"""
            font-size: 11px;
            color: {RENK_YAZI_IKINCIL};
            background: {RENK_BG_IKINCIL};
            border: 1px solid {RENK_KENARLIK};
            border-radius: 6px;
            padding: 8px 12px;
        """)
        layout.addWidget(aciklama)

        self._tablo = QTableWidget(3, 4)
        self._tablo.setHorizontalHeaderLabels(
            ["Ürün Adı", "Seri No", "Seri Boyutu", "Ürün Formu"]
        )
        self._tablo.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._tablo.verticalHeader().setVisible(False)
        self._tablo.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {RENK_KENARLIK};
                border-radius: 6px;
                font-size: 11px;
                font-family: {FONT_AILESI};
                gridline-color: {RENK_KENARLIK};
            }}
            QHeaderView::section {{
                background: {RENK_BG_IKINCIL};
                border: none;
                border-right: 1px solid {RENK_KENARLIK};
                border-bottom: 1px solid {RENK_KENARLIK};
                padding: 5px 8px;
                font-size: 10px;
                font-weight: bold;
                color: {RENK_YAZI_IKINCIL};
            }}
        """)
        layout.addWidget(self._tablo)
        layout.addStretch()

    def yukle(self, proje: ProjeVerisi):
        seriler = [proje.seri_1_no, proje.seri_2_no, proje.seri_3_no]
        for i in range(3):
            for col, txt in enumerate([
                proje.urun_adi,
                seriler[i],
                proje.seri_boyutu,
                proje.urun_formu,
            ]):
                item = QTableWidgetItem(txt)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                item.setForeground(QBrush(QColor(RENK_YAZI_BIRINCIL)))
                self._tablo.setItem(i, col, item)


# ─── Ana Widget ──────────────────────────────────────────────────────────────

class BirimFormulWidget(QWidget):
    """
    Modül 3 ana widget.
    Üst sekmeler: Tablo 1 | Tablo 2
    Tablo 1 içinde: Formül tablosu + not paneli (PVP / PVR sekmeli)
    """

    kaydedildi = pyqtSignal()
    degisti = pyqtSignal()

    def __init__(self, proje: ProjeVerisi, parent=None):
        super().__init__(parent)
        self._proje = proje
        self._degisiklik_var = False
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

        lbl = QLabel("Birim Formül ve Ürün Bilgileri")
        lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {RENK_YAZI_BIRINCIL};")
        tb.addWidget(lbl)
        tb.addStretch()

        self.lbl_durum = QLabel("")
        self.lbl_durum.setVisible(False)
        self.lbl_durum.setStyleSheet(f"""
            font-size: 11px;
            color: {RENK_PRIMARY_KOYU};
            background: {RENK_PRIMARY_ACIK};
            border-radius: 4px;
            padding: 2px 8px;
        """)
        tb.addWidget(self.lbl_durum)

        btn_kaydet = QPushButton("💾  Kaydet")
        btn_kaydet.setFixedHeight(30)
        btn_kaydet.setMinimumWidth(90)
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{
                background: {RENK_PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                font-family: {FONT_AILESI};
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: {RENK_PRIMARY_KOYU}; }}
        """)
        btn_kaydet.clicked.connect(self._kaydet)
        tb.addWidget(btn_kaydet)
        layout.addWidget(toolbar)

        # Ana sekmeler
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
                padding: 6px 16px;
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

        # ── Tablo 1 sekmesi ──
        tablo1_widget = QWidget()
        t1_layout = QVBoxLayout(tablo1_widget)
        t1_layout.setContentsMargins(0, 0, 0, 0)
        t1_layout.setSpacing(0)

        # Formül tablosu (üst %65)
        self.formul_tablosu = BirimFormulTablosu(
            self._proje.urun_formu,
            self._proje.seri_boyutu,
        )
        self.formul_tablosu.degisti.connect(self._on_degisti)
        t1_layout.addWidget(self.formul_tablosu, 65)

        # Notlar bölümü (alt %35)
        notlar_frame = QFrame()
        notlar_frame.setStyleSheet(f"""
            border-top: 2px solid {RENK_KENARLIK};
            background: {RENK_BG_BIRINCIL};
        """)
        notlar_layout = QVBoxLayout(notlar_frame)
        notlar_layout.setContentsMargins(0, 0, 0, 0)
        notlar_layout.setSpacing(0)

        # Not başlık
        not_baslik = QFrame()
        not_baslik.setStyleSheet(f"""
            background: {RENK_BG_IKINCIL};
            border-bottom: 1px solid {RENK_KENARLIK};
        """)
        not_baslik.setFixedHeight(36)
        nb_layout = QHBoxLayout(not_baslik)
        nb_layout.setContentsMargins(14, 0, 14, 0)
        nb_lbl = QLabel("Tablo Altı Notlar")
        nb_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {RENK_YAZI_BIRINCIL};")
        nb_layout.addWidget(nb_lbl)
        nb_layout.addStretch()

        # PVP / PVR sekmeleri
        self.not_tabs = QTabWidget()
        self.not_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {RENK_BG_BIRINCIL};
            }}
            QTabBar::tab {{
                border: 1px solid {RENK_KENARLIK};
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                padding: 4px 12px;
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
        nb_layout.addWidget(self.not_tabs)
        notlar_layout.addWidget(not_baslik)

        # PVP notları scroll
        pvp_scroll = QScrollArea()
        pvp_scroll.setWidgetResizable(True)
        pvp_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.pvp_notlari = NotPaneli()
        self.pvp_notlari.degisti.connect(self._on_degisti)
        pvp_scroll.setWidget(self.pvp_notlari)
        self.not_tabs.addTab(pvp_scroll, "PVP")

        # PVR notları scroll
        pvr_scroll = QScrollArea()
        pvr_scroll.setWidgetResizable(True)
        pvr_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.pvr_notlari = NotPaneli()
        self.pvr_notlari.degisti.connect(self._on_degisti)
        pvr_scroll.setWidget(self.pvr_notlari)
        self.not_tabs.addTab(pvr_scroll, "PVR")

        notlar_layout.addWidget(self.not_tabs, 1)
        t1_layout.addWidget(notlar_frame, 35)

        self.tabs.addTab(tablo1_widget, "Tablo 1 — Birim Formül")

        # ── Tablo 2 sekmesi ──
        self.kapsanan = KapsananUrunlerWidget()
        self.tabs.addTab(self.kapsanan, "Tablo 2 — Kapsanan Ürünler")

    def _yukle(self):
        """Proje verisini arayüze yükler."""
        # Birim formül satırları
        if self._proje.birim_formul_satirlar:
            self.formul_tablosu.yukle(self._proje.birim_formul_satirlar)

        # Notlar
        if self._proje.pvp_notlar:
            self.pvp_notlari.yukle(self._proje.pvp_notlar)
        else:
            self.pvp_notlari.varsayilan_yukle()

        if self._proje.pvr_notlar:
            self.pvr_notlari.yukle(self._proje.pvr_notlar)
        else:
            self.pvr_notlari.varsayilan_yukle()

        # Kapsanan ürünler
        self.kapsanan.yukle(self._proje)

        self._degisiklik_var = False
        self.lbl_durum.setVisible(False)

    def _on_degisti(self):
        self._degisiklik_var = True
        self.lbl_durum.setText("● Kaydedilmemiş değişiklik")
        self.lbl_durum.setStyleSheet(f"""
            font-size: 11px;
            color: {RENK_PRIMARY_KOYU};
            background: {RENK_PRIMARY_ACIK};
            border-radius: 4px;
            padding: 2px 8px;
        """)
        self.lbl_durum.setVisible(True)
        self.degisti.emit()

    def _kaydet(self):
        self._proje.birim_formul_satirlar = self.formul_tablosu.to_list()
        self._proje.pvp_notlar = self.pvp_notlari.to_list()
        self._proje.pvr_notlar = self.pvr_notlari.to_list()

        self._degisiklik_var = False
        self.lbl_durum.setText("✓ Kaydedildi")
        self.lbl_durum.setStyleSheet(f"""
            font-size: 11px;
            color: {RENK_YESIL};
            background: {RENK_YESIL_BG};
            border-radius: 4px;
            padding: 2px 8px;
        """)
        self.lbl_durum.setVisible(True)
        self.kaydedildi.emit()

    def proje_guncelle(self, proje: ProjeVerisi):
        self._proje = proje
        self._yukle()

    def degisiklik_var_mi(self) -> bool:
        return self._degisiklik_var
