"""
PV-DOC — Akış Şeması Editörü
Sol panel: Operasyon/Test/Ok ekle, form listesi
Sağ panel: Gerçek zamanlı drag-drop canvas
Word çıktısı için 3 sütunlu format: Hammaddeler | İşlem | Testler
"""

import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel, QLineEdit, QPushButton, QScrollArea, QComboBox,
    QAbstractItemView, QListWidget, QListWidgetItem,
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem,
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsPathItem,
    QSizePolicy, QToolButton, QDialog, QDialogButtonBox,
    QFormLayout, QTextEdit, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QSizeF
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QFont, QPainter, QPolygonF,
    QPainterPath, QTransform
)

from ui.stiller import (
    RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    RENK_YESIL, RENK_YESIL_BG, FONT_AILESI
)


# ─── Renk Sabitleri ───────────────────────────────────────────────────────────

RENK_ISLEM   = "#EBF4FF"      # dikdörtgen (operasyon)
RENK_KARAR   = "#FFF8E1"      # elmas (karar)
RENK_TEST    = "#F0FFF4"      # yuvarlatılmış kutu (test)
RENK_PARALEL = "#F3E5F5"      # paralel akış
RENK_KENAR_ISLEM  = "#2C6EAB"
RENK_KENAR_KARAR  = "#F57C00"
RENK_KENAR_TEST   = "#2E7D32"
RENK_KENAR_PARALEL= "#7B1FA2"
RENK_OK      = "#455A64"


# ─── Şekil Tipleri ────────────────────────────────────────────────────────────

SEKIL_TIPLERI = {
    "operasyon":   "Operasyon (Dikdörtgen)",
    "karar":       "Karar (Elmas)",
    "test":        "Test",
    "paralel":     "Paralel Akış",
    "birlesme":    "Birleşme Noktası",
    "baslangic":   "Başlangıç/Bitiş (Oval)",
    "ok":          "Ok (Bağlantı)",
}


# ─── Veri Modelleri ───────────────────────────────────────────────────────────

class AkisEleman:
    def __init__(self, tip="operasyon", metin="", x=100.0, y=100.0,
                 genislik=160.0, yukseklik=50.0, eid=None):
        import uuid
        self.id = eid or str(uuid.uuid4())[:8]
        self.tip = tip
        self.metin = metin
        self.x = x
        self.y = y
        self.genislik = genislik
        self.yukseklik = yukseklik
        # Ek alanlar
        self.hammadde = ""   # Sol sütun (Word çıktısı için)
        self.testler = ""    # Sağ sütun (Word çıktısı için)

    def to_dict(self):
        return {
            "id": self.id, "tip": self.tip, "metin": self.metin,
            "x": self.x, "y": self.y,
            "genislik": self.genislik, "yukseklik": self.yukseklik,
            "hammadde": self.hammadde, "testler": self.testler,
        }

    @classmethod
    def from_dict(cls, d):
        e = cls(
            tip=d.get("tip","operasyon"),
            metin=d.get("metin",""),
            x=d.get("x",100.0), y=d.get("y",100.0),
            genislik=d.get("genislik",160.0),
            yukseklik=d.get("yukseklik",50.0),
            eid=d.get("id"),
        )
        e.hammadde = d.get("hammadde","")
        e.testler = d.get("testler","")
        return e


class AkisOk:
    def __init__(self, kaynak_id="", hedef_id="", etiket="", okid=None):
        import uuid
        self.id = okid or str(uuid.uuid4())[:8]
        self.kaynak_id = kaynak_id
        self.hedef_id = hedef_id
        self.etiket = etiket

    def to_dict(self):
        return {"id": self.id, "kaynak_id": self.kaynak_id,
                "hedef_id": self.hedef_id, "etiket": self.etiket}

    @classmethod
    def from_dict(cls, d):
        return cls(
            kaynak_id=d.get("kaynak_id",""),
            hedef_id=d.get("hedef_id",""),
            etiket=d.get("etiket",""),
            okid=d.get("id"),
        )


# ─── Grafik Eleman ────────────────────────────────────────────────────────────

class AkisElemanItem(QGraphicsItem):
    """Canvas'taki sürüklenebilir şekil."""

    def __init__(self, eleman: AkisEleman, canvas: 'AkisCanvas'):
        super().__init__()
        self.eleman = eleman
        self.canvas = canvas
        self.setPos(eleman.x, eleman.y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.eleman.genislik, self.eleman.yukseklik)

    def paint(self, painter: QPainter, option, widget=None):
        tip = self.eleman.tip
        w, h = self.eleman.genislik, self.eleman.yukseklik
        selected = self.isSelected()

        pen_width = 2.5 if selected else 1.5
        pen_color = RENK_PRIMARY if selected else {
            "operasyon": RENK_KENAR_ISLEM,
            "karar":     RENK_KENAR_KARAR,
            "test":      RENK_KENAR_TEST,
            "paralel":   RENK_KENAR_PARALEL,
            "birlesme":  RENK_KENAR_ISLEM,
            "baslangic": RENK_KENAR_ISLEM,
            "ok":        RENK_OK,
        }.get(tip, RENK_KENAR_ISLEM)

        fill_color = {
            "operasyon": RENK_ISLEM,
            "karar":     RENK_KARAR,
            "test":      RENK_TEST,
            "paralel":   RENK_PARALEL,
            "birlesme":  "#ECEFF1",
            "baslangic": "#E8EAF6",
        }.get(tip, RENK_ISLEM)

        painter.setPen(QPen(QColor(pen_color), pen_width))
        painter.setBrush(QBrush(QColor(fill_color)))

        if tip == "karar":
            # Elmas
            poly = QPolygonF([
                QPointF(w/2, 0), QPointF(w, h/2),
                QPointF(w/2, h), QPointF(0, h/2)
            ])
            painter.drawPolygon(poly)
        elif tip == "baslangic":
            painter.drawRoundedRect(QRectF(0, 0, w, h), h/2, h/2)
        elif tip == "birlesme":
            # Küçük daire
            r = min(w, h) / 2
            painter.drawEllipse(QPointF(w/2, h/2), r-2, r-2)
        else:
            painter.drawRoundedRect(QRectF(0, 0, w, h), 8, 8)

        # Metin
        painter.setPen(QPen(QColor(RENK_YAZI_BIRINCIL)))
        font = QFont(FONT_AILESI, 9)
        font.setBold(tip == "operasyon")
        painter.setFont(font)
        painter.drawText(
            QRectF(4, 4, w-8, h-8),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self.eleman.metin
        )

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.eleman.x = self.pos().x()
            self.eleman.y = self.pos().y()
            self.canvas.okları_yenile()
            self.canvas.degisti.emit()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        self.canvas.eleman_duzenle(self.eleman)


class OkItem(QGraphicsPathItem):
    """İki şekil arasındaki yönlü ok."""

    def __init__(self, ok: AkisOk, kaynak: AkisElemanItem,
                 hedef: AkisElemanItem):
        super().__init__()
        self.ok = ok
        self.kaynak_item = kaynak
        self.hedef_item = hedef
        self._ciz()
        self.setPen(QPen(QColor(RENK_OK), 1.8))
        self.setBrush(QBrush(QColor(RENK_OK)))
        self.setZValue(-1)

    def _ciz(self):
        k = self.kaynak_item
        h = self.hedef_item
        kx = k.eleman.x + k.eleman.genislik / 2
        ky = k.eleman.y + k.eleman.yukseklik
        hx = h.eleman.x + h.eleman.genislik / 2
        hy = h.eleman.y

        path = QPainterPath()
        path.moveTo(kx, ky)
        # Bezier kontrol noktaları
        path.cubicTo(kx, ky + 30, hx, hy - 30, hx, hy)

        # Ok başı
        ok_basi = QPainterPath()
        ok_basi.moveTo(hx, hy)
        ok_basi.lineTo(hx - 7, hy - 12)
        ok_basi.lineTo(hx + 7, hy - 12)
        ok_basi.closeSubpath()

        path.addPath(ok_basi)
        self.setPath(path)

    def guncelle(self):
        self._ciz()


# ─── Canvas ───────────────────────────────────────────────────────────────────

class AkisCanvas(QGraphicsView):
    degisti = pyqtSignal()
    eleman_secildi = pyqtSignal(object)  # AkisEleman

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sahne = QGraphicsScene(self)
        self._sahne.setSceneRect(0, 0, 1200, 900)
        self.setScene(self._sahne)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setStyleSheet(f"""
            QGraphicsView {{
                background: #F8F9FA;
                border: 1px solid {RENK_KENARLIK};
            }}
        """)
        self._eleman_items: dict[str, AkisElemanItem] = {}
        self._ok_items: dict[str, OkItem] = {}
        self._sahne.selectionChanged.connect(self._secim_degisti)

    def eleman_ekle(self, eleman: AkisEleman):
        item = AkisElemanItem(eleman, self)
        self._sahne.addItem(item)
        self._eleman_items[eleman.id] = item

    def ok_ekle(self, ok: AkisOk):
        kaynak = self._eleman_items.get(ok.kaynak_id)
        hedef = self._eleman_items.get(ok.hedef_id)
        if kaynak and hedef:
            item = OkItem(ok, kaynak, hedef)
            self._sahne.addItem(item)
            self._ok_items[ok.id] = item

    def eleman_sil(self, eid: str):
        item = self._eleman_items.pop(eid, None)
        if item:
            self._sahne.removeItem(item)
        # Bu elemana bağlı okları da sil
        to_del = [oid for oid, oi in self._ok_items.items()
                  if oi.ok.kaynak_id == eid or oi.ok.hedef_id == eid]
        for oid in to_del:
            oi = self._ok_items.pop(oid)
            self._sahne.removeItem(oi)
        self.degisti.emit()
        return to_del

    def okları_yenile(self):
        for oi in self._ok_items.values():
            oi.guncelle()

    def temizle(self):
        self._sahne.clear()
        self._eleman_items.clear()
        self._ok_items.clear()

    def eleman_duzenle(self, eleman: AkisEleman):
        dlg = ElemanDuzenleDialog(eleman, self)
        if dlg.exec():
            item = self._eleman_items.get(eleman.id)
            if item:
                item.update()
            self.degisti.emit()

    def _secim_degisti(self):
        secili = self._sahne.selectedItems()
        if secili and isinstance(secili[0], AkisElemanItem):
            self.eleman_secildi.emit(secili[0].eleman)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.87
        self.scale(factor, factor)


# ─── Eleman Düzenleme Dialog ──────────────────────────────────────────────────

class ElemanDuzenleDialog(QDialog):
    def __init__(self, eleman: AkisEleman, parent=None):
        super().__init__(parent)
        self.eleman = eleman
        self.setWindowTitle("Şekli Düzenle")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.input_metin = QLineEdit(eleman.metin)
        form.addRow("Metin:", self.input_metin)

        self.input_hammadde = QLineEdit(eleman.hammadde)
        self.input_hammadde.setPlaceholderText(
            "Bu adımda kullanılan hammaddeler (Word çıktısı için)")
        form.addRow("Hammaddeler:", self.input_hammadde)

        self.input_testler = QTextEdit()
        self.input_testler.setPlaceholderText(
            "Bu adımda yapılan testler (Word çıktısı için)")
        self.input_testler.setPlainText(eleman.testler)
        self.input_testler.setMaximumHeight(80)
        form.addRow("Testler:", self.input_testler)

        layout.addLayout(form)

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._kaydet)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def _kaydet(self):
        self.eleman.metin = self.input_metin.text().strip()
        self.eleman.hammadde = self.input_hammadde.text().strip()
        self.eleman.testler = self.input_testler.toPlainText().strip()
        self.accept()


# ─── Sol Panel — Form Listesi ─────────────────────────────────────────────────

class SolPanel(QWidget):
    eleman_eklendi = pyqtSignal(object)  # AkisEleman
    ok_eklendi = pyqtSignal(object)      # AkisOk
    eleman_silindi = pyqtSignal(str)     # id
    ok_silindi = pyqtSignal(str)         # id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._elemanlar: list[AkisEleman] = []
        self._oklar: list[AkisOk] = []
        self.setMaximumWidth(320)
        self.setMinimumWidth(260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8); layout.setSpacing(8)

        # Şekil Ekle bölümü
        ekle_grup = QGroupBox("Şekil Ekle")
        ekle_grup.setStyleSheet(f"""
            QGroupBox {{
                font-size:11px; font-weight:bold;
                color:{RENK_YAZI_BIRINCIL};
                border:1px solid {RENK_KENARLIK};
                border-radius:6px; margin-top:8px;
                padding:8px;
            }}
            QGroupBox::title {{
                subcontrol-origin:margin; left:8px; top:0px;
            }}
        """)
        ekle_l = QVBoxLayout(ekle_grup)
        ekle_l.setSpacing(4)

        self.combo_tip = QComboBox()
        for k, v in SEKIL_TIPLERI.items():
            self.combo_tip.addItem(v, k)
        self.combo_tip.setStyleSheet(f"""
            QComboBox {{
                border:1px solid {RENK_KENARLIK}; border-radius:5px;
                padding:4px 8px; font-size:11px;
                background:{RENK_BG_BIRINCIL};
            }}
        """)
        ekle_l.addWidget(self.combo_tip)

        self.input_metin = QLineEdit()
        self.input_metin.setPlaceholderText("Şekil metni...")
        self.input_metin.setStyleSheet(f"""
            border:1px solid {RENK_KENARLIK}; border-radius:5px;
            padding:4px 8px; font-size:11px;
        """)
        ekle_l.addWidget(self.input_metin)

        btn_ekle = QPushButton("+ Ekle")
        btn_ekle.setStyleSheet(f"""
            QPushButton {{
                background:{RENK_PRIMARY}; color:white; border:none;
                border-radius:5px; font-size:11px; padding:5px;
            }}
            QPushButton:hover {{ background:{RENK_PRIMARY_KOYU}; }}
        """)
        btn_ekle.clicked.connect(self._sekil_ekle)
        ekle_l.addWidget(btn_ekle)
        layout.addWidget(ekle_grup)

        # Ok Ekle bölümü
        ok_grup = QGroupBox("Ok Ekle (Bağlantı)")
        ok_grup.setStyleSheet(ekle_grup.styleSheet())
        ok_l = QFormLayout(ok_grup)
        ok_l.setSpacing(4)

        self.combo_kaynak = QComboBox()
        self.combo_hedef  = QComboBox()
        self.input_ok_etiket = QLineEdit()
        self.input_ok_etiket.setPlaceholderText("Etiket (opsiyonel)")
        for combo in [self.combo_kaynak, self.combo_hedef]:
            combo.setStyleSheet(self.combo_tip.styleSheet())
        self.input_ok_etiket.setStyleSheet(self.input_metin.styleSheet())
        ok_l.addRow("Kaynak:", self.combo_kaynak)
        ok_l.addRow("Hedef:",  self.combo_hedef)
        ok_l.addRow("Etiket:", self.input_ok_etiket)

        btn_ok = QPushButton("→ Ok Ekle")
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background:#455A64; color:white; border:none;
                border-radius:5px; font-size:11px; padding:5px;
            }}
            QPushButton:hover {{ background:#37474F; }}
        """)
        btn_ok.clicked.connect(self._ok_ekle)
        ok_l.addRow("", btn_ok)
        layout.addWidget(ok_grup)

        # Eleman Listesi
        liste_baslik = QLabel("Şekil Listesi")
        liste_baslik.setStyleSheet(
            f"font-size:11px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        layout.addWidget(liste_baslik)

        self._liste = QListWidget()
        self._liste.setStyleSheet(f"""
            QListWidget {{
                border:1px solid {RENK_KENARLIK}; border-radius:5px;
                font-size:11px; background:{RENK_BG_BIRINCIL};
            }}
            QListWidget::item:selected {{
                background:{RENK_PRIMARY_ACIK}; color:{RENK_PRIMARY_KOYU};
            }}
        """)
        layout.addWidget(self._liste, 1)

        btn_sil = QPushButton("✕ Seçili Şekli Sil")
        btn_sil.setStyleSheet(f"""
            QPushButton {{
                background:#FADBD8; color:#C0392B;
                border:1px solid #F1948A; border-radius:5px;
                font-size:11px; padding:5px;
            }}
            QPushButton:hover {{ background:#F1948A; color:white; }}
        """)
        btn_sil.clicked.connect(self._secili_sil)
        layout.addWidget(btn_sil)

    def _sekil_ekle(self):
        metin = self.input_metin.text().strip()
        if not metin:
            return
        tip = self.combo_tip.currentData()

        # Boyut tipine göre
        if tip == "karar":
            w, h = 140, 70
        elif tip == "birlesme":
            w, h = 40, 40
        elif tip == "baslangic":
            w, h = 130, 40
        else:
            w, h = 160, 50

        # Y konumunu mevcut elemanların altına koy
        y = 30.0
        if self._elemanlar:
            y = max(e.y + e.yukseklik + 40 for e in self._elemanlar)

        eleman = AkisEleman(
            tip=tip, metin=metin,
            x=200.0, y=y, genislik=w, yukseklik=h
        )
        self._elemanlar.append(eleman)
        self._liste_guncelle()
        self._combolar_guncelle()
        self.input_metin.clear()
        self.eleman_eklendi.emit(eleman)

    def _ok_ekle(self):
        if self.combo_kaynak.count() == 0 or self.combo_hedef.count() == 0:
            return
        k_id = self.combo_kaynak.currentData()
        h_id = self.combo_hedef.currentData()
        if not k_id or not h_id or k_id == h_id:
            return
        ok = AkisOk(
            kaynak_id=k_id, hedef_id=h_id,
            etiket=self.input_ok_etiket.text().strip()
        )
        self._oklar.append(ok)
        self.input_ok_etiket.clear()
        self.ok_eklendi.emit(ok)

    def _secili_sil(self):
        item = self._liste.currentItem()
        if not item: return
        eid = item.data(Qt.ItemDataRole.UserRole)
        self._elemanlar = [e for e in self._elemanlar if e.id != eid]
        self._oklar = [o for o in self._oklar
                       if o.kaynak_id != eid and o.hedef_id != eid]
        self._liste_guncelle()
        self._combolar_guncelle()
        self.eleman_silindi.emit(eid)

    def _liste_guncelle(self):
        self._liste.clear()
        for e in self._elemanlar:
            tip_adi = SEKIL_TIPLERI.get(e.tip, e.tip)
            it = QListWidgetItem(f"[{tip_adi[:3]}] {e.metin}")
            it.setData(Qt.ItemDataRole.UserRole, e.id)
            self._liste.addItem(it)

    def _combolar_guncelle(self):
        for combo in [self.combo_kaynak, self.combo_hedef]:
            combo.clear()
            for e in self._elemanlar:
                combo.addItem(e.metin[:25], e.id)

    def yukle(self, elemanlar: list[AkisEleman], oklar: list[AkisOk]):
        self._elemanlar = elemanlar
        self._oklar = oklar
        self._liste_guncelle()
        self._combolar_guncelle()

    def get_elemanlar(self): return self._elemanlar
    def get_oklar(self): return self._oklar


# ─── Ana Editör Widget ────────────────────────────────────────────────────────

class AkisEditoruWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._elemanlar: list[AkisEleman] = []
        self._oklar: list[AkisOk] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        # Araç çubuğu
        tb = QFrame()
        tb.setStyleSheet(
            f"background:{RENK_BG_IKINCIL};border-bottom:1px solid {RENK_KENARLIK};")
        tb.setFixedHeight(36)
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(10,0,10,0); tbl.setSpacing(6)

        for ikon, tooltip, slot in [
            ("⊕", "Yakınlaştır",   lambda: self._canvas.scale(1.2, 1.2)),
            ("⊖", "Uzaklaştır",    lambda: self._canvas.scale(0.83, 0.83)),
            ("⊡", "Sıfırla",       lambda: self._canvas.resetTransform()),
        ]:
            btn = QPushButton(ikon); btn.setFixedSize(28, 28)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(f"""
                QPushButton{{border:1px solid {RENK_KENARLIK};border-radius:4px;
                background:{RENK_BG_BIRINCIL};font-size:14px;color:{RENK_YAZI_BIRINCIL};}}
                QPushButton:hover{{background:{RENK_PRIMARY_ACIK};}}
            """)
            btn.clicked.connect(slot)
            tbl.addWidget(btn)

        tbl.addStretch()
        aciklama = QLabel("Çift tıkla: şekil düzenle  |  Tekerlek: yakınlaştır/uzaklaştır  |  Sürükle: taşı")
        aciklama.setStyleSheet(f"font-size:10px;color:{RENK_YAZI_UCUNCUL};")
        tbl.addWidget(aciklama)
        layout.addWidget(tb)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sol panel
        self._sol_panel = SolPanel()
        self._sol_panel.eleman_eklendi.connect(self._eleman_ekle)
        self._sol_panel.ok_eklendi.connect(self._ok_ekle)
        self._sol_panel.eleman_silindi.connect(self._eleman_sil)
        splitter.addWidget(self._sol_panel)

        # Canvas
        self._canvas = AkisCanvas()
        self._canvas.degisti.connect(self.degisti)
        splitter.addWidget(self._canvas)
        splitter.setSizes([280, 700])
        layout.addWidget(splitter, 1)

    def _eleman_ekle(self, eleman: AkisEleman):
        self._elemanlar.append(eleman)
        self._canvas.eleman_ekle(eleman)
        self.degisti.emit()

    def _ok_ekle(self, ok: AkisOk):
        self._oklar.append(ok)
        self._canvas.ok_ekle(ok)
        self.degisti.emit()

    def _eleman_sil(self, eid: str):
        self._elemanlar = [e for e in self._elemanlar if e.id != eid]
        silinen_ok_idler = self._canvas.eleman_sil(eid)
        self._oklar = [o for o in self._oklar if o.id not in silinen_ok_idler]
        self.degisti.emit()

    def yukle(self, elemanlar_data: list, oklar_data: list):
        self._canvas.temizle()
        self._elemanlar = [AkisEleman.from_dict(d) for d in elemanlar_data]
        self._oklar = [AkisOk.from_dict(d) for d in oklar_data]
        for e in self._elemanlar:
            self._canvas.eleman_ekle(e)
        for o in self._oklar:
            self._canvas.ok_ekle(o)
        self._sol_panel.yukle(self._elemanlar, self._oklar)

    def to_data(self):
        return (
            [e.to_dict() for e in self._elemanlar],
            [o.to_dict() for o in self._oklar]
        )

    def to_word_table(self) -> list[dict]:
        """
        Word çıktısı için 3 sütunlu format:
        [{"hammadde": ..., "islem": ..., "testler": ...}, ...]
        """
        return [
            {
                "hammadde": e.hammadde,
                "islem": e.metin,
                "testler": e.testler,
            }
            for e in self._elemanlar
            if e.tip not in ("ok", "birlesme")
        ]
