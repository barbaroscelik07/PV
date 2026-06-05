"""
PV-DOC — Birim Formül ve Ürün Bilgileri (Modül 3)
Tablo 1: Birim formül — satır ekle/sil/taşı, % ve kg otomatik hesapla
Tablo 2: Kapsanan ürünler
Notlar : PVP / PVR ayrı
"""

import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QLineEdit, QPushButton, QScrollArea, QTabWidget,
    QSizePolicy, QAbstractItemView, QTableWidget,
    QTableWidgetItem, QHeaderView, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QFont, QColor, QBrush, QKeySequence

from core.models import ProjeVerisi, UrunFormu
from ui.stiller import (
    RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    RENK_YESIL, RENK_YESIL_BG, FONT_AILESI
)


# ─── Sabitler ────────────────────────────────────────────────────────────────

FONKSIYON_LISTESI = [
    "",
    "Etkin madde",
    "Dolgu Ajanı",
    "Bağlayıcı",
    "Dağıtıcı",
    "Lubrikant",
    "Kaydırıcı",
    "pH Ajanı",
    "Kaplama Malzemesi",
    "Çözücü",
    "Boyar Madde",
    "Tatlandırıcı",
    "Koruyucu",
    "Yüzey Aktif Madde",
    "Diğer",
]

GRUP_ADLARI = {
    UrunFormu.TABLET.value:            ["Tablet"],
    UrunFormu.FILM_TABLET.value:       ["Katman I", "Katman II", "Kaplama"],
    UrunFormu.KAPSUL.value:            ["İç Formül", "Kapsül Kabuğu"],
    UrunFormu.KAPSUL_FILM_TABLET.value:["Katman I", "Katman II", "Kaplama", "Kapsül Kabuğu"],
}

# Sütun indeksleri — artık QTableWidget değil, her satır QWidget
COL_DRAG = 0
COL_AD   = 1
COL_FONK = 2
COL_MG   = 3
COL_YUZ  = 4
COL_KG   = 5
COL_SIL  = 6
N_COLS   = 7


# ─── Yardımcı ─────────────────────────────────────────────────────────────────

def _float_or_zero(s: str) -> float:
    try:
        return float(str(s).replace(",", ".").strip())
    except (ValueError, AttributeError):
        return 0.0


def _fmt(val: float, n: int = 3) -> str:
    if val == 0.0:
        return ""
    s = f"{val:.{n}f}"
    s = s.rstrip("0").rstrip(".")
    return s


def _parse_seri(metin: str) -> float:
    """'150.000 ftb' → 150000.0"""
    if not metin:
        return 0.0
    temiz = metin.strip()
    m = re.search(r'[\d.,]+', temiz)
    if not m:
        return 0.0
    sayi = m.group()
    parcalar = sayi.split('.')
    virgul_parcalar = sayi.split(',')
    # Türkçe format: 1.234,56 → 1234.56
    if ',' in sayi and '.' in sayi:
        sayi = sayi.replace('.', '').replace(',', '.')
    elif '.' in sayi and len(parcalar) > 1 and len(parcalar[-1]) == 3:
        sayi = sayi.replace('.', '')  # binlik ayırıcı
    elif ',' in sayi and len(virgul_parcalar) > 1 and len(virgul_parcalar[-1]) == 3:
        sayi = sayi.replace(',', '')
    try:
        return float(sayi)
    except ValueError:
        return 0.0


# ─── Veri Modeli ──────────────────────────────────────────────────────────────

class FormulSatiri:
    def __init__(self, ad="", fonksiyon="", mg_tb="",
                 yuzde="", kg_seri="", grup="",
                 manuel_yuzde=False, manuel_kg=False):
        self.ad = ad
        self.fonksiyon = fonksiyon
        self.mg_tb = mg_tb
        self.yuzde = yuzde
        self.kg_seri = kg_seri
        self.grup = grup
        self.manuel_yuzde = manuel_yuzde
        self.manuel_kg = manuel_kg

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, d):
        s = cls()
        for k, v in d.items():
            if hasattr(s, k):
                setattr(s, k, v)
        return s


# ─── Not Satırı / Paneli ──────────────────────────────────────────────────────

class NotSatiri(QFrame):
    silindi = pyqtSignal(object)
    degisti = pyqtSignal()

    def __init__(self, sembol="", aciklama="", parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self); l.setContentsMargins(0,2,0,2); l.setSpacing(8)
        self.input_sembol = QLineEdit(sembol)
        self.input_sembol.setPlaceholderText("Sembol"); self.input_sembol.setFixedWidth(80)
        l.addWidget(self.input_sembol)
        self.input_aciklama = QLineEdit(aciklama)
        self.input_aciklama.setPlaceholderText("Açıklama")
        l.addWidget(self.input_aciklama, 1)
        btn = QPushButton("✕"); btn.setFixedSize(24,24)
        btn.setStyleSheet(f"""
            QPushButton{{border:1px solid {RENK_KENARLIK};background:{RENK_BG_IKINCIL};
            color:#A32D2D;font-size:12px;font-weight:bold;border-radius:3px;}}
            QPushButton:hover{{background:#FCEBEB;border:1px solid #F09595;}}
        """)
        btn.clicked.connect(lambda: self.silindi.emit(self)); l.addWidget(btn)
        self.input_sembol.textChanged.connect(self.degisti)
        self.input_aciklama.textChanged.connect(self.degisti)

    def to_dict(self):
        return {"sembol": self.input_sembol.text().strip(),
                "aciklama": self.input_aciklama.text().strip()}


class NotPaneli(QWidget):
    degisti = pyqtSignal()
    VARSAYILAN = [
        {"sembol": "*",    "aciklama": "Uçucudur bitmiş üründe yer almaz."},
        {"sembol": "k.m.", "aciklama": "Kafi miktarda"},
        {"sembol": "U.Y.", "aciklama": "Uygulama yoktur"},
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._satirlar: list[NotSatiri] = []
        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(0)

        hdr = QFrame()
        hdr.setStyleSheet(f"background:{RENK_BG_IKINCIL};border-bottom:1px solid {RENK_KENARLIK};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(12,5,12,5)
        for txt, w in [("Sembol", 80), ("Açıklama", 0)]:
            lb = QLabel(txt)
            lb.setStyleSheet(f"font-size:10px;font-weight:bold;color:{RENK_YAZI_IKINCIL};")
            if w: lb.setFixedWidth(w)
            hl.addWidget(lb)
        l.addWidget(hdr)

        self._cont = QWidget(); self._cl = QVBoxLayout(self._cont)
        self._cl.setContentsMargins(12,4,12,4); self._cl.setSpacing(3)
        l.addWidget(self._cont)

        btn = QPushButton("+ Not Ekle")
        btn.setStyleSheet(f"""
            QPushButton{{border:1px dashed {RENK_PRIMARY};border-radius:5px;
            background:transparent;color:{RENK_PRIMARY};font-size:11px;
            padding:4px 12px;margin:4px 12px;}}
            QPushButton:hover{{background:{RENK_PRIMARY_ACIK};}}
        """)
        btn.clicked.connect(lambda: self._ekle()); l.addWidget(btn)

    def _ekle(self, sembol="", aciklama=""):
        s = NotSatiri(sembol, aciklama, self._cont)
        s.silindi.connect(self._sil); s.degisti.connect(self.degisti)
        self._satirlar.append(s); self._cl.addWidget(s)
        self.degisti.emit()

    def _sil(self, s):
        self._satirlar.remove(s); s.deleteLater(); self.degisti.emit()

    def yukle(self, notlar):
        for s in self._satirlar[:]: s.deleteLater()
        self._satirlar.clear()
        for n in notlar: self._ekle(n.get("sembol",""), n.get("aciklama",""))

    def varsayilan_yukle(self): self.yukle(self.VARSAYILAN)

    def to_list(self): return [s.to_dict() for s in self._satirlar]


# ─── Birim Formül Tablosu ─────────────────────────────────────────────────────

class BirimFormulTablosu(QWidget):
    """
    Temiz QTableWidget tabanlı birim formül tablosu.
    - Tek tıkla düzenleme
    - Sürükle-bırak sıralama
    - Ctrl+V ile toplu yapıştırma (tüm tablo: Ad\tFonksiyon\tmg\t%\tkg)
    - Her zaman görünür kırmızı sil butonu
    - Fonksiyon dropdown ok'u görünür
    """
    degisti = pyqtSignal()

    def __init__(self, urun_formu: str, seri_boyutu: str = "", parent=None):
        super().__init__(parent)
        self._gruplar = GRUP_ADLARI.get(urun_formu, ["Tablet"])
        self._veri: dict[str, list[FormulSatiri]] = {g: [] for g in self._gruplar}
        self._seri_boyutu = seri_boyutu
        self._yukleniyor = False

        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)

        # Tablo
        self._tablo = QTableWidget()
        self._tablo.setColumnCount(N_COLS)
        self._tablo.setHorizontalHeaderLabels(
            ["", "Hammadde / Yardımcı Madde", "Fonksiyon",
             "mg/tb", "% İçerik", "kg/seri", ""])
        hdr = self._tablo.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(False)
        self._tablo.setColumnWidth(COL_DRAG, 26)
        self._tablo.setColumnWidth(COL_AD,  170)
        self._tablo.setColumnWidth(COL_FONK,125)
        self._tablo.setColumnWidth(COL_MG,   65)
        self._tablo.setColumnWidth(COL_YUZ,  65)
        self._tablo.setColumnWidth(COL_KG,   72)
        self._tablo.setColumnWidth(COL_SIL,  36)
        self._tablo.verticalHeader().setVisible(False)
        self._tablo.setShowGrid(True)
        self._tablo.setAlternatingRowColors(False)
        # Tek tıkla düzenleme
        self._tablo.setEditTriggers(
            QAbstractItemView.EditTrigger.CurrentChanged |
            QAbstractItemView.EditTrigger.AnyKeyPressed |
            QAbstractItemView.EditTrigger.SelectedClicked)
        self._tablo.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tablo.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tablo.setStyleSheet(f"""
            QTableWidget {{
                border:none;font-size:11px;font-family:{FONT_AILESI};
                gridline-color:{RENK_KENARLIK};
            }}
            QTableWidget::item{{padding:2px 6px;}}
            QTableWidget::item:selected{{
                background:{RENK_PRIMARY_ACIK};color:{RENK_PRIMARY_KOYU};}}
            QHeaderView::section{{
                background:{RENK_BG_IKINCIL};border:none;
                border-right:1px solid {RENK_KENARLIK};
                border-bottom:1px solid {RENK_KENARLIK};
                padding:4px 6px;font-size:10px;font-weight:bold;
                color:{RENK_YAZI_IKINCIL};}}
        """)
        self._tablo.cellChanged.connect(self._hucre_degisti)
        self._tablo.installEventFilter(self)
        layout.addWidget(self._tablo)

        # Alt butonlar
        alt = QFrame()
        alt.setStyleSheet(
            f"background:{RENK_BG_IKINCIL};border-top:1px solid {RENK_KENARLIK};")
        al = QHBoxLayout(alt); al.setContentsMargins(10,5,10,5); al.setSpacing(6)
        for grup in self._gruplar:
            btn = QPushButton(f"+ {grup}")
            btn.setStyleSheet(f"""
                QPushButton{{border:1px solid {RENK_PRIMARY};border-radius:5px;
                background:{RENK_PRIMARY_ACIK};color:{RENK_PRIMARY};
                font-size:11px;padding:3px 10px;}}
                QPushButton:hover{{background:{RENK_PRIMARY};color:white;}}
            """)
            btn.clicked.connect(lambda _, g=grup: self.satir_ekle(g))
            al.addWidget(btn)
        al.addStretch()
        self.lbl_toplam = QLabel("Toplam: — mg")
        self.lbl_toplam.setStyleSheet(
            f"font-size:11px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        al.addWidget(self.lbl_toplam)
        layout.addWidget(alt)

        self._yenile()

    # ── Olay Filtresi (Ctrl+V) ────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if obj is self._tablo and event.type() == event.Type.KeyPress:
            if event.matches(QKeySequence.StandardKey.Paste):
                self._yapistir()
                return True
        return super().eventFilter(obj, event)

    def _yapistir(self):
        """Excel/Word tablosunu yapıştır.
        Format: Ad [tab] Fonksiyon [tab] mg/tb [tab] % [tab] kg
        Her satır ayrı bir formül satırı olur.
        """
        metin = QApplication.clipboard().text().strip()
        if not metin:
            return

        # Hedef grup
        secili = self._tablo.currentRow()
        hedef_grup = self._gruplar[0]
        if secili in self._satir_haritasi:
            hedef_grup = self._satir_haritasi[secili][0]

        eklenen = 0
        for satir_metin in metin.split('\n'):
            satir_metin = satir_metin.strip('\r\n ')
            if not satir_metin:
                continue
            k = [x.strip() for x in satir_metin.split('\t')]
            if not k[0]:
                continue
            s = FormulSatiri(grup=hedef_grup)
            s.ad = k[0]
            if len(k) > 1: s.fonksiyon = k[1]
            if len(k) > 2: s.mg_tb = k[2].replace(',', '.')
            if len(k) > 3:
                s.yuzde = k[3].replace(',', '.')
                s.manuel_yuzde = bool(s.yuzde)
            if len(k) > 4:
                s.kg_seri = k[4].replace(',', '.')
                s.manuel_kg = bool(s.kg_seri)
            self._veri[hedef_grup].append(s)
            eklenen += 1

        if eklenen:
            self._yenile()
            self.degisti.emit()

    # ── Veri Yönetimi ─────────────────────────────────────────────────────────

    def satir_ekle(self, grup: str, s: FormulSatiri = None):
        if s is None:
            s = FormulSatiri(grup=grup)
        self._veri[grup].append(s)
        self._yenile()
        self.degisti.emit()

    def seri_boyutu_guncelle(self, boyut: str):
        self._seri_boyutu = boyut
        self._hesapla()

    def yukle(self, satirlar: list):
        for g in self._gruplar:
            self._veri[g] = []
        for d in satirlar:
            g = d.get("grup", self._gruplar[0])
            if g not in self._veri:
                g = self._gruplar[0]
            self._veri[g].append(FormulSatiri.from_dict(d))
        self._yenile()

    def to_list(self) -> list:
        sonuc = []
        for g in self._gruplar:
            for s in self._veri[g]:
                s.grup = g
                sonuc.append(s.to_dict())
        return sonuc

    # ── Tablo Render ──────────────────────────────────────────────────────────

    def _yenile(self):
        self._yukleniyor = True
        self._tablo.clearContents()
        self._satir_haritasi: dict[int, tuple[str, int]] = {}

        # Toplam satır sayısı
        n = sum(1 + len(self._veri[g]) + 1 for g in self._gruplar) + 1
        self._tablo.setRowCount(n)

        r = 0
        for grup in self._gruplar:
            self._grup_baslik(r, grup); r += 1
            for vi, s in enumerate(self._veri[grup]):
                self._veri_satiri(r, grup, vi, s)
                self._satir_haritasi[r] = (grup, vi)
                r += 1
            self._alt_toplam(r, grup); r += 1
        self._genel_toplam(r)

        self._yukleniyor = False
        self._hesapla()

    def _grup_baslik(self, r: int, grup: str):
        self._tablo.setRowHeight(r, 26)
        for c in range(N_COLS):
            it = QTableWidgetItem()
            it.setFlags(Qt.ItemFlag.NoItemFlags)
            it.setBackground(QBrush(QColor(RENK_PRIMARY_ACIK)))
            self._tablo.setItem(r, c, it)
        lbl = QTableWidgetItem(f"  {grup}")
        lbl.setFlags(Qt.ItemFlag.NoItemFlags)
        lbl.setBackground(QBrush(QColor(RENK_PRIMARY_ACIK)))
        lbl.setForeground(QBrush(QColor(RENK_PRIMARY_KOYU)))
        f = QFont(FONT_AILESI, 10); f.setBold(True); lbl.setFont(f)
        self._tablo.setItem(r, COL_AD, lbl)

    def _veri_satiri(self, r: int, grup: str, vi: int, s: FormulSatiri):
        self._tablo.setRowHeight(r, 28)

        # Sürükleme
        drag = QTableWidgetItem("⠿")
        drag.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        drag.setForeground(QBrush(QColor(RENK_YAZI_UCUNCUL)))
        drag.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tablo.setItem(r, COL_DRAG, drag)

        # Ad
        self._tablo.setItem(r, COL_AD, QTableWidgetItem(s.ad))

        # Fonksiyon — inline widget yerine özel hücre
        fonk_item = QTableWidgetItem(s.fonksiyon)
        self._tablo.setItem(r, COL_FONK, fonk_item)

        # mg/tb
        mg = QTableWidgetItem(s.mg_tb)
        mg.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._tablo.setItem(r, COL_MG, mg)

        # % İçerik
        yuz = QTableWidgetItem(s.yuzde)
        yuz.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if not s.manuel_yuzde:
            yuz.setForeground(QBrush(QColor(RENK_YAZI_UCUNCUL)))
        self._tablo.setItem(r, COL_YUZ, yuz)

        # kg/seri
        kg = QTableWidgetItem(s.kg_seri)
        kg.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if not s.manuel_kg:
            kg.setForeground(QBrush(QColor(RENK_YAZI_UCUNCUL)))
        self._tablo.setItem(r, COL_KG, kg)

        # Sil — her zaman görünür kırmızı X
        sil = QTableWidgetItem("✕")
        sil.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        sil.setForeground(QBrush(QColor("#C0392B")))
        sil.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        f2 = QFont(FONT_AILESI, 12); f2.setBold(True); sil.setFont(f2)
        sil.setBackground(QBrush(QColor("#FCEBEB")))
        sil.setToolTip("Bu satırı sil")
        self._tablo.setItem(r, COL_SIL, sil)

    def _alt_toplam(self, r: int, grup: str):
        self._tablo.setRowHeight(r, 24)
        toplam_mg = sum(_float_or_zero(s.mg_tb) for s in self._veri[grup])
        toplam_kg = sum(_float_or_zero(s.kg_seri) for s in self._veri[grup])
        f = QFont(FONT_AILESI, 10); f.setBold(True)
        for c in range(N_COLS):
            it = QTableWidgetItem(); it.setFlags(Qt.ItemFlag.NoItemFlags)
            it.setBackground(QBrush(QColor(RENK_BG_IKINCIL)))
            self._tablo.setItem(r, c, it)
        for c, txt in [(COL_AD, f"  {grup} Toplam"),
                       (COL_MG, _fmt(toplam_mg) if toplam_mg else ""),
                       (COL_KG, _fmt(toplam_kg) if toplam_kg else "")]:
            it = QTableWidgetItem(txt); it.setFlags(Qt.ItemFlag.NoItemFlags)
            it.setBackground(QBrush(QColor(RENK_BG_IKINCIL)))
            it.setForeground(QBrush(QColor(RENK_YAZI_IKINCIL))); it.setFont(f)
            if c in (COL_MG, COL_KG):
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._tablo.setItem(r, c, it)

    def _genel_toplam(self, r: int):
        self._tablo.setRowHeight(r, 30)
        tum = [s for g in self._gruplar for s in self._veri[g]]
        t_mg = sum(_float_or_zero(s.mg_tb) for s in tum)
        t_kg = sum(_float_or_zero(s.kg_seri) for s in tum)
        renk = QColor("#F0F8EC"); f = QFont(FONT_AILESI, 11); f.setBold(True)
        for c in range(N_COLS):
            it = QTableWidgetItem(); it.setFlags(Qt.ItemFlag.NoItemFlags)
            it.setBackground(QBrush(renk)); self._tablo.setItem(r, c, it)
        for c, txt in [(COL_AD, "  Toplam Ağırlık"),
                       (COL_MG, _fmt(t_mg) if t_mg else "—"),
                       (COL_KG, _fmt(t_kg) if t_kg else "—")]:
            it = QTableWidgetItem(txt); it.setFlags(Qt.ItemFlag.NoItemFlags)
            it.setBackground(QBrush(renk))
            it.setForeground(QBrush(QColor(RENK_YESIL))); it.setFont(f)
            if c in (COL_MG, COL_KG):
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._tablo.setItem(r, c, it)
        self.lbl_toplam.setText(f"Toplam: {_fmt(t_mg)} mg" if t_mg else "Toplam: — mg")

    # ── Olay İşleyiciler ──────────────────────────────────────────────────────

    def _hucre_degisti(self, r: int, c: int):
        if self._yukleniyor:
            return
        # Sil sütununa tıklandı mı?
        if c == COL_SIL and r in self._satir_haritasi:
            grup, vi = self._satir_haritasi[r]
            self._satir_sil(grup, vi)
            return
        if r not in self._satir_haritasi:
            return
        grup, vi = self._satir_haritasi[r]
        s = self._veri[grup][vi]
        item = self._tablo.item(r, c)
        if not item:
            return
        metin = item.text().strip()
        if c == COL_AD:
            s.ad = metin
        elif c == COL_FONK:
            s.fonksiyon = metin
        elif c == COL_MG:
            s.mg_tb = metin
            s.manuel_yuzde = False
            s.manuel_kg = False
            self._hesapla()
        elif c == COL_YUZ:
            s.yuzde = metin
            s.manuel_yuzde = bool(metin)
        elif c == COL_KG:
            s.kg_seri = metin
            s.manuel_kg = bool(metin)
        self.degisti.emit()

    def mousePressEvent(self, event):
        """Sil sütununa tıklanınca satırı sil."""
        idx = self._tablo.indexAt(
            self._tablo.viewport().mapFrom(self, event.pos()))
        if idx.isValid() and idx.column() == COL_SIL:
            r = idx.row()
            if r in self._satir_haritasi:
                grup, vi = self._satir_haritasi[r]
                self._satir_sil(grup, vi)
                return
        super().mousePressEvent(event)

    def _satir_sil(self, grup: str, vi: int):
        if vi < len(self._veri[grup]):
            self._veri[grup].pop(vi)
            self._yenile()
            self.degisti.emit()

    # ── Hesaplamalar ──────────────────────────────────────────────────────────

    def _hesapla(self):
        tum = [s for g in self._gruplar for s in self._veri[g]]
        t_mg = sum(_float_or_zero(s.mg_tb) for s in tum)
        seri_boy = _parse_seri(self._seri_boyutu)

        for g in self._gruplar:
            for s in self._veri[g]:
                mg = _float_or_zero(s.mg_tb)
                if not s.manuel_yuzde:
                    s.yuzde = _fmt(mg / t_mg * 100, 2) if t_mg > 0 and mg > 0 else ""
                if not s.manuel_kg:
                    s.kg_seri = _fmt(mg * seri_boy / 1_000_000, 3) if seri_boy > 0 and mg > 0 else ""

        self._yukleniyor = True
        for tablo_r, (grup, vi) in self._satir_haritasi.items():
            s = self._veri[grup][vi]
            for c, val, manuel in [(COL_YUZ, s.yuzde, s.manuel_yuzde),
                                    (COL_KG,  s.kg_seri, s.manuel_kg)]:
                it = self._tablo.item(tablo_r, c)
                if it:
                    it.setText(val)
                    it.setForeground(QBrush(QColor(
                        RENK_YAZI_BIRINCIL if manuel else RENK_YAZI_UCUNCUL)))
        self._yukleniyor = False
        # Alt toplamları güncelle
        self._tablo.blockSignals(True)
        r = 0
        for g in self._gruplar:
            r += 1
            r += len(self._veri[g])
            self._alt_toplam(r, g); r += 1
        self._genel_toplam(r)
        self._tablo.blockSignals(False)


# ─── Kapsanan Ürünler ─────────────────────────────────────────────────────────

class KapsananUrunlerWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QVBoxLayout(self); l.setContentsMargins(12,12,12,12); l.setSpacing(10)
        aciklama = QLabel(
            "Bu tablo proje oluştururken girilen seri bilgilerinden otomatik doldurulur.")
        aciklama.setWordWrap(True)
        aciklama.setStyleSheet(f"""
            font-size:11px;color:{RENK_YAZI_IKINCIL};
            background:{RENK_BG_IKINCIL};border:1px solid {RENK_KENARLIK};
            border-radius:6px;padding:8px 12px;
        """)
        l.addWidget(aciklama)
        self._tablo = QTableWidget(3, 4)
        self._tablo.setHorizontalHeaderLabels(
            ["Ürün Adı","Seri No","Seri Boyutu","Ürün Formu"])
        self._tablo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tablo.verticalHeader().setVisible(False)
        self._tablo.setStyleSheet(f"""
            QTableWidget{{border:1px solid {RENK_KENARLIK};border-radius:6px;
            font-size:11px;font-family:{FONT_AILESI};gridline-color:{RENK_KENARLIK};}}
            QHeaderView::section{{background:{RENK_BG_IKINCIL};border:none;
            border-right:1px solid {RENK_KENARLIK};
            border-bottom:1px solid {RENK_KENARLIK};
            padding:5px 8px;font-size:10px;font-weight:bold;color:{RENK_YAZI_IKINCIL};}}
        """)
        l.addWidget(self._tablo); l.addStretch()

    def yukle(self, proje: ProjeVerisi):
        seriler = [proje.seri_1_no, proje.seri_2_no, proje.seri_3_no]
        for i in range(3):
            for j, txt in enumerate([proje.urun_adi, seriler[i],
                                      proje.seri_boyutu, proje.urun_formu]):
                it = QTableWidgetItem(txt)
                it.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self._tablo.setItem(i, j, it)


# ─── Ana Widget ───────────────────────────────────────────────────────────────

class BirimFormulWidget(QWidget):
    kaydedildi = pyqtSignal()
    degisti = pyqtSignal()

    def __init__(self, proje: ProjeVerisi, parent=None):
        super().__init__(parent)
        self._proje = proje
        self._setup_ui()
        self._yukle()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)

        # Toolbar
        tb_frame = QFrame()
        tb_frame.setStyleSheet(
            f"background:{RENK_BG_BIRINCIL};border-bottom:1px solid {RENK_KENARLIK};")
        tb_frame.setFixedHeight(46)
        tb = QHBoxLayout(tb_frame); tb.setContentsMargins(16,0,16,0); tb.setSpacing(8)
        lbl = QLabel("Birim Formül ve Ürün Bilgileri")
        lbl.setStyleSheet(f"font-size:13px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        tb.addWidget(lbl); tb.addStretch()

        self.lbl_durum = QLabel(""); self.lbl_durum.setVisible(False)
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
        btn_kaydet.clicked.connect(self._kaydet); tb.addWidget(btn_kaydet)
        layout.addWidget(tb_frame)

        # Ana sekmeler
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane{{border:none;background:{RENK_BG_BIRINCIL};}}
            QTabBar::tab{{border:1px solid {RENK_KENARLIK};border-bottom:none;
            border-radius:6px 6px 0 0;padding:6px 16px;font-size:11px;
            color:{RENK_YAZI_IKINCIL};background:{RENK_BG_IKINCIL};margin-right:2px;}}
            QTabBar::tab:selected{{background:{RENK_BG_BIRINCIL};
            color:{RENK_PRIMARY};font-weight:bold;}}
        """)
        layout.addWidget(self.tabs, 1)

        # Tablo 1
        t1 = QWidget()
        t1l = QVBoxLayout(t1); t1l.setContentsMargins(0,0,0,0); t1l.setSpacing(0)

        self.formul_tablosu = BirimFormulTablosu(
            self._proje.urun_formu, self._proje.seri_boyutu)
        self.formul_tablosu.degisti.connect(self._on_degisti)
        t1l.addWidget(self.formul_tablosu, 65)

        # Notlar bölümü
        notlar_frame = QFrame()
        notlar_frame.setStyleSheet(
            f"border-top:2px solid {RENK_KENARLIK};background:{RENK_BG_BIRINCIL};")
        nfl = QVBoxLayout(notlar_frame); nfl.setContentsMargins(0,0,0,0); nfl.setSpacing(0)

        not_hdr = QFrame()
        not_hdr.setStyleSheet(
            f"background:{RENK_BG_IKINCIL};border-bottom:1px solid {RENK_KENARLIK};")
        not_hdr.setFixedHeight(36)
        nhl = QHBoxLayout(not_hdr); nhl.setContentsMargins(14,0,14,0)
        nhl.addWidget(QLabel("Tablo Altı Notlar").setStyleSheet if False else
                      QLabel("Tablo Altı Notlar"))
        nhl.addStretch()

        self.not_tabs = QTabWidget()
        self.not_tabs.setStyleSheet(f"""
            QTabWidget::pane{{border:none;background:{RENK_BG_BIRINCIL};}}
            QTabBar::tab{{border:1px solid {RENK_KENARLIK};border-bottom:none;
            border-radius:4px 4px 0 0;padding:4px 12px;font-size:11px;
            color:{RENK_YAZI_IKINCIL};background:{RENK_BG_IKINCIL};margin-right:2px;}}
            QTabBar::tab:selected{{background:{RENK_BG_BIRINCIL};
            color:{RENK_PRIMARY};font-weight:bold;}}
        """)
        nhl.addWidget(self.not_tabs)
        nfl.addWidget(not_hdr)

        for attr, sekme_adi in [("pvp_notlari","PVP"), ("pvr_notlari","PVR")]:
            scroll = QScrollArea(); scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            panel = NotPaneli(); panel.degisti.connect(self._on_degisti)
            setattr(self, attr, panel)
            scroll.setWidget(panel)
            self.not_tabs.addTab(scroll, sekme_adi)

        nfl.addWidget(self.not_tabs, 1)
        t1l.addWidget(notlar_frame, 35)
        self.tabs.addTab(t1, "Tablo 1 — Birim Formül")

        # Tablo 2
        self.kapsanan = KapsananUrunlerWidget()
        self.tabs.addTab(self.kapsanan, "Tablo 2 — Kapsanan Ürünler")

    def _yukle(self):
        if self._proje.birim_formul_satirlar:
            self.formul_tablosu.yukle(self._proje.birim_formul_satirlar)
        if self._proje.pvp_notlar:
            self.pvp_notlari.yukle(self._proje.pvp_notlar)
        else:
            self.pvp_notlari.varsayilan_yukle()
        if self._proje.pvr_notlar:
            self.pvr_notlari.yukle(self._proje.pvr_notlar)
        else:
            self.pvr_notlari.varsayilan_yukle()
        self.kapsanan.yukle(self._proje)
        self.lbl_durum.setVisible(False)

    def _on_degisti(self):
        self.lbl_durum.setText("● Kaydedilmemiş değişiklik")
        self.lbl_durum.setStyleSheet(f"""
            font-size:11px;color:{RENK_PRIMARY_KOYU};
            background:{RENK_PRIMARY_ACIK};border-radius:4px;padding:2px 8px;
        """)
        self.lbl_durum.setVisible(True)
        self.degisti.emit()

    def _kaydet(self):
        self._proje.birim_formul_satirlar = self.formul_tablosu.to_list()
        self._proje.pvp_notlar = self.pvp_notlari.to_list()
        self._proje.pvr_notlar = self.pvr_notlari.to_list()
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

    def degisiklik_var_mi(self): return False
