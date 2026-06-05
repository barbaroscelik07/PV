"""
PV-DOC — Üretim Prosesi ve Akış Şeması (Modül 4)
- Proses adımları tablosu (operasyon no, adı, ekipman, parametreler)
- Otomatik akış şeması SVG önizlemesi
- PVP için proses açıklama metni
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFrame, QLabel, QLineEdit, QPushButton, QTextEdit,
    QScrollArea, QAbstractItemView, QTableWidget,
    QTableWidgetItem, QHeaderView, QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QBrush, QKeySequence
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtCore import QByteArray

from core.models import ProjeVerisi, UrunFormu
from ui.stiller import (
    RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    RENK_YESIL, RENK_YESIL_BG, FONT_AILESI
)


# ─── Varsayılan Proses Adımları ───────────────────────────────────────────────

VARSAYILAN_ADIMLAR = {
    UrunFormu.FILM_TABLET.value: [
        {"no": "1", "ad": "Tartım",         "ekipman": "Hassas Terazi",          "parametreler": ""},
        {"no": "2", "ad": "Karıştırma",     "ekipman": "V-Tipi Karıştırıcı",     "parametreler": "Hız, Süre"},
        {"no": "3", "ad": "Tablet Baskı",   "ekipman": "Rotary Tablet Presi",    "parametreler": "Baskı kuvveti, Hız"},
        {"no": "4", "ad": "Film Kaplama",   "ekipman": "Film Kaplama Sistemi",   "parametreler": "Giriş/çıkış sıcaklığı, Kaplama süresi"},
        {"no": "5", "ad": "Ambalajlama",    "ekipman": "Blister Makinesi",       "parametreler": ""},
    ],
    UrunFormu.TABLET.value: [
        {"no": "1", "ad": "Tartım",         "ekipman": "Hassas Terazi",          "parametreler": ""},
        {"no": "2", "ad": "Karıştırma",     "ekipman": "V-Tipi Karıştırıcı",     "parametreler": "Hız, Süre"},
        {"no": "3", "ad": "Tablet Baskı",   "ekipman": "Rotary Tablet Presi",    "parametreler": "Baskı kuvveti, Hız"},
        {"no": "4", "ad": "Ambalajlama",    "ekipman": "Blister Makinesi",       "parametreler": ""},
    ],
    UrunFormu.KAPSUL.value: [
        {"no": "1", "ad": "Tartım",         "ekipman": "Hassas Terazi",          "parametreler": ""},
        {"no": "2", "ad": "Karıştırma",     "ekipman": "V-Tipi Karıştırıcı",     "parametreler": "Hız, Süre"},
        {"no": "3", "ad": "Dolum",          "ekipman": "Kapsül Dolum Makinesi",  "parametreler": "Dolum ağırlığı"},
        {"no": "4", "ad": "Ambalajlama",    "ekipman": "Blister Makinesi",       "parametreler": ""},
    ],
}

# Sütun indeksleri
COL_NO    = 0
COL_AD    = 1
COL_EKP   = 2
COL_PAR   = 3
COL_SIL   = 4
N_COLS    = 5


# ─── Proses Veri Modeli ───────────────────────────────────────────────────────

class ProsesAdimi:
    def __init__(self, no="", ad="", ekipman="", parametreler=""):
        self.no = no
        self.ad = ad
        self.ekipman = ekipman
        self.parametreler = parametreler

    def to_dict(self):
        return {"no": self.no, "ad": self.ad,
                "ekipman": self.ekipman, "parametreler": self.parametreler}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("no",""), d.get("ad",""),
                   d.get("ekipman",""), d.get("parametreler",""))


# ─── Akış Şeması SVG Oluşturucu ───────────────────────────────────────────────

def _akis_svg(adimlar: list[ProsesAdimi]) -> str:
    if not adimlar:
        return '<svg viewBox="0 0 300 60" xmlns="http://www.w3.org/2000/svg"><text x="150" y="35" text-anchor="middle" font-size="12" fill="#999">Henüz adım eklenmedi</text></svg>'

    BOX_W = 160; BOX_H = 44; GAP_Y = 28
    TOTAL_H = len(adimlar) * (BOX_H + GAP_Y) + 20
    CX = 200  # merkez x

    lines = [
        f'<svg viewBox="0 0 400 {TOTAL_H}" xmlns="http://www.w3.org/2000/svg">'
        f'<style>text{{font-family:Arial,sans-serif;}}</style>'
    ]

    for i, adim in enumerate(adimlar):
        y = 10 + i * (BOX_H + GAP_Y)
        bx = CX - BOX_W // 2

        # Ok (ilk adım hariç)
        if i > 0:
            ok_y = y - GAP_Y
            lines.append(
                f'<line x1="{CX}" y1="{ok_y}" x2="{CX}" y2="{y}" '
                f'stroke="#2C6EAB" stroke-width="2" marker-end="url(#arrow)"/>')

        # Kutu
        lines.append(
            f'<rect x="{bx}" y="{y}" width="{BOX_W}" height="{BOX_H}" '
            f'rx="8" fill="#EBF4FF" stroke="#2C6EAB" stroke-width="1.5"/>')

        # Operasyon No
        lines.append(
            f'<text x="{bx+10}" y="{y+15}" font-size="9" fill="#2C6EAB" font-weight="bold">'
            f'{adim.no}</text>')

        # Operasyon Adı
        ad_txt = adim.ad[:22] + "…" if len(adim.ad) > 22 else adim.ad
        lines.append(
            f'<text x="{CX}" y="{y+26}" text-anchor="middle" '
            f'font-size="12" font-weight="bold" fill="#1A3A5C">{ad_txt}</text>')

        # Ekipman
        if adim.ekipman:
            ekp_txt = adim.ekipman[:28] + "…" if len(adim.ekipman) > 28 else adim.ekipman
            lines.append(
                f'<text x="{CX}" y="{y+39}" text-anchor="middle" '
                f'font-size="9" fill="#5B7FA6">{ekp_txt}</text>')

    # Ok başı tanımı
    lines.insert(1,
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" '
        'refX="4" refY="3" orient="auto">'
        '<path d="M0,0 L0,6 L8,3 z" fill="#2C6EAB"/>'
        '</marker></defs>')

    lines.append('</svg>')
    return '\n'.join(lines)


# ─── Proses Tablosu ───────────────────────────────────────────────────────────

class ProsesTablosu(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._adimlar: list[ProsesAdimi] = []
        self._yukleniyor = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        self._tablo = QTableWidget()
        self._tablo.setColumnCount(N_COLS)
        self._tablo.setHorizontalHeaderLabels(
            ["No", "Operasyon Adı", "Ekipman", "Kritik Parametreler", ""])
        hdr = self._tablo.horizontalHeader()
        hdr.setSectionResizeMode(COL_AD,  QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(COL_EKP, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(COL_PAR, QHeaderView.ResizeMode.Stretch)
        self._tablo.setColumnWidth(COL_NO,  40)
        self._tablo.setColumnWidth(COL_SIL, 36)
        self._tablo.verticalHeader().setVisible(False)
        self._tablo.setShowGrid(True)
        self._tablo.setAlternatingRowColors(True)
        self._tablo.setEditTriggers(
            QAbstractItemView.EditTrigger.CurrentChanged |
            QAbstractItemView.EditTrigger.AnyKeyPressed |
            QAbstractItemView.EditTrigger.SelectedClicked)
        self._tablo.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self._tablo.setDragEnabled(True)
        self._tablo.setAcceptDrops(True)
        self._tablo.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._tablo.setStyleSheet(f"""
            QTableWidget {{
                border: none; font-size: 11px;
                font-family: {FONT_AILESI};
                gridline-color: {RENK_KENARLIK};
                alternate-background-color: {RENK_BG_IKINCIL};
            }}
            QTableWidget::item {{ padding: 3px 6px; }}
            QTableWidget::item:selected {{
                background: {RENK_PRIMARY_ACIK}; color: {RENK_PRIMARY_KOYU};
            }}
            QHeaderView::section {{
                background: {RENK_BG_IKINCIL}; border: none;
                border-right: 1px solid {RENK_KENARLIK};
                border-bottom: 1px solid {RENK_KENARLIK};
                padding: 5px 6px; font-size: 10px;
                font-weight: bold; color: {RENK_YAZI_IKINCIL};
            }}
        """)
        self._tablo.cellChanged.connect(self._hucre_degisti)
        self._tablo.cellClicked.connect(self._hucre_tiklandi)
        layout.addWidget(self._tablo)

        # Alt buton
        alt = QFrame()
        alt.setStyleSheet(
            f"background:{RENK_BG_IKINCIL};border-top:1px solid {RENK_KENARLIK};")
        al = QHBoxLayout(alt); al.setContentsMargins(10,5,10,5)
        btn_ekle = QPushButton("+ Adım Ekle")
        btn_ekle.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid {RENK_PRIMARY}; border-radius: 5px;
                background: {RENK_PRIMARY_ACIK}; color: {RENK_PRIMARY};
                font-size: 11px; padding: 4px 14px;
            }}
            QPushButton:hover {{ background: {RENK_PRIMARY}; color: white; }}
        """)
        btn_ekle.clicked.connect(self._adim_ekle)
        al.addWidget(btn_ekle); al.addStretch()
        layout.addWidget(alt)

    def _yenile(self):
        self._yukleniyor = True
        self._tablo.clearContents()
        self._tablo.setRowCount(len(self._adimlar))
        for i, a in enumerate(self._adimlar):
            self._tablo.setRowHeight(i, 30)
            for c, val in [(COL_NO, a.no), (COL_AD, a.ad),
                           (COL_EKP, a.ekipman), (COL_PAR, a.parametreler)]:
                it = QTableWidgetItem(val)
                self._tablo.setItem(i, c, it)
            # Sil butonu
            sil = QTableWidgetItem("✕")
            sil.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            sil.setForeground(QBrush(QColor("#C0392B")))
            sil.setBackground(QBrush(QColor("#FADBD8")))
            sil.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            f = QFont(FONT_AILESI, 12); f.setBold(True); sil.setFont(f)
            sil.setToolTip("Bu adımı sil")
            self._tablo.setItem(i, COL_SIL, sil)
        self._yukleniyor = False

    def _adim_ekle(self):
        no = str(len(self._adimlar) + 1)
        self._adimlar.append(ProsesAdimi(no=no))
        self._yenile()
        self.degisti.emit()

    def _hucre_tiklandi(self, r, c):
        if c == COL_SIL and r < len(self._adimlar):
            self._adimlar.pop(r)
            # Numaraları güncelle
            for i, a in enumerate(self._adimlar):
                a.no = str(i + 1)
            self._yenile()
            self.degisti.emit()

    def _hucre_degisti(self, r, c):
        if self._yukleniyor or c == COL_SIL: return
        if r >= len(self._adimlar): return
        a = self._adimlar[r]
        it = self._tablo.item(r, c)
        if not it: return
        val = it.text().strip()
        if c == COL_NO:   a.no = val
        elif c == COL_AD:  a.ad = val
        elif c == COL_EKP: a.ekipman = val
        elif c == COL_PAR: a.parametreler = val
        self.degisti.emit()

    def yukle(self, adimlar: list):
        self._adimlar = [ProsesAdimi.from_dict(d) for d in adimlar]
        self._yenile()

    def varsayilan_yukle(self, urun_formu: str):
        sarjlar = VARSAYILAN_ADIMLAR.get(
            urun_formu, VARSAYILAN_ADIMLAR[UrunFormu.FILM_TABLET.value])
        self._adimlar = [ProsesAdimi.from_dict(d) for d in sarjlar]
        self._yenile()

    def to_list(self): return [a.to_dict() for a in self._adimlar]
    def get_adimlar(self): return self._adimlar


# ─── Akış Şeması Paneli ───────────────────────────────────────────────────────

class AkisSemasiPanel(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setMinimumWidth(260)

        w = QWidget()
        l = QVBoxLayout(w); l.setContentsMargins(8, 8, 8, 8)

        baslik = QLabel("Akış Şeması")
        baslik.setStyleSheet(
            f"font-size:12px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};"
            f"padding:4px 0;")
        l.addWidget(baslik)

        self._svg = QSvgWidget()
        self._svg.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        l.addWidget(self._svg)
        l.addStretch()
        self.setWidget(w)

    def guncelle(self, adimlar: list[ProsesAdimi]):
        svg_str = _akis_svg(adimlar)
        self._svg.load(QByteArray(svg_str.encode('utf-8')))
        # Yüksekliği ayarla
        n = max(1, len(adimlar))
        self._svg.setFixedHeight(n * 72 + 30)


# ─── Proses Metin Alanı ───────────────────────────────────────────────────────

class ProsesMetinWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        l = QVBoxLayout(self); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(6)

        baslik = QLabel("Proses Açıklaması (PVP Metni)")
        baslik.setStyleSheet(
            f"font-size:11px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        l.addWidget(baslik)

        aciklama = QLabel(
            "Her operasyon için proses açıklamasını buraya girebilirsiniz. "
            "Bu metin PVP dokümanında ilgili bölümde kullanılır.")
        aciklama.setWordWrap(True)
        aciklama.setStyleSheet(f"font-size:10px;color:{RENK_YAZI_IKINCIL};")
        l.addWidget(aciklama)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "Üretim prosesini buraya yazın...\n\n"
            "Örn: Tartım operasyonunda tüm hammaddeler ±0.1 g hassasiyetle tartılır. "
            "Karıştırma operasyonunda V-tipi karıştırıcıda 20 dakika karıştırılır...")
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {RENK_KENARLIK};
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                font-family: {FONT_AILESI};
                background: {RENK_BG_BIRINCIL};
            }}
        """)
        self.text_edit.textChanged.connect(self.degisti)
        l.addWidget(self.text_edit, 1)


# ─── Ana Widget ───────────────────────────────────────────────────────────────

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
            QPushButton {{
                background:{RENK_PRIMARY}; color:#FFFFFF; border:none;
                border-radius:6px; font-size:12px; font-weight:bold;
                font-family:{FONT_AILESI}; padding:0 14px;
            }}
            QPushButton:hover {{ background:{RENK_PRIMARY_KOYU}; }}
        """)
        btn_kaydet.clicked.connect(self._kaydet)
        tbl.addWidget(btn_kaydet)
        layout.addWidget(tb)

        # İçerik — splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sol: tablo + metin
        sol = QWidget()
        sol_l = QVBoxLayout(sol); sol_l.setContentsMargins(12,12,6,12); sol_l.setSpacing(8)

        # Tablo başlık
        tablo_baslik = QLabel("Proses Adımları")
        tablo_baslik.setStyleSheet(
            f"font-size:11px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        sol_l.addWidget(tablo_baslik)

        self.proses_tablosu = ProsesTablosu()
        self.proses_tablosu.degisti.connect(self._tablo_degisti)
        sol_l.addWidget(self.proses_tablosu, 55)

        self.metin_widget = ProsesMetinWidget()
        self.metin_widget.degisti.connect(self._on_degisti)
        sol_l.addWidget(self.metin_widget, 45)
        splitter.addWidget(sol)

        # Sağ: akış şeması
        self.akis_paneli = AkisSemasiPanel()
        splitter.addWidget(self.akis_paneli)
        splitter.setSizes([600, 280])
        layout.addWidget(splitter, 1)

    def _yukle(self):
        if self._proje.proses_adimlar:
            self.proses_tablosu.yukle(self._proje.proses_adimlar)
        else:
            self.proses_tablosu.varsayilan_yukle(self._proje.urun_formu)
        self.metin_widget.text_edit.setPlainText(
            getattr(self._proje, 'uretim_prosesi_metni', ''))
        self._akis_guncelle()
        self.lbl_durum.setVisible(False)

    def _tablo_degisti(self):
        self._akis_guncelle()
        self._on_degisti()

    def _akis_guncelle(self):
        self.akis_paneli.guncelle(self.proses_tablosu.get_adimlar())

    def _on_degisti(self):
        self.lbl_durum.setText("● Kaydedilmemiş değişiklik")
        self.lbl_durum.setStyleSheet(f"""
            font-size:11px; color:{RENK_PRIMARY_KOYU};
            background:{RENK_PRIMARY_ACIK}; border-radius:4px; padding:2px 8px;
        """)
        self.lbl_durum.setVisible(True)
        self.degisti.emit()

    def _kaydet(self):
        self._proje.proses_adimlar = self.proses_tablosu.to_list()
        self._proje.uretim_prosesi_metni = \
            self.metin_widget.text_edit.toPlainText()
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
