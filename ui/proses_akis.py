"""
PV-DOC — Üretim Prosesi ve Akış Şeması (Modül 4)

Sol Panel — Form Tabanlı:
  'Operasyon Ekle', 'Karar Noktası Ekle', 'Ok Ekle' butonları.
  Her eklenen eleman form listesinde görünür, düzenlenebilir, silinebilir.

Sağ Panel — Canvas Önizleme:
  Sol panele eklenen elemanlar gerçek zamanlı render edilir.
  Şekiller üzerine tıklanarak drag-and-drop ile konumlandırılabilir.

Desteklenen Şekil Tipleri:
  Dikdörtgen  — işlem adımları
  Elmas       — karar noktaları
  Ok          — bağlantılar (yönlü)

Word Çıktısı (gelecekte):
  Üç sütunlu tablo: Sol=Hammaddeler, Orta=İşlem adımları, Sağ=Testler
"""

import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFrame, QLabel, QLineEdit, QPushButton, QTextEdit,
    QScrollArea, QAbstractItemView, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox,
    QSizePolicy, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPointF, QRectF, QSizeF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont,
    QPolygonF, QPainterPath
)

from core.models import ProjeVerisi, UrunFormu
from ui.stiller import (
    RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    RENK_YESIL, RENK_YESIL_BG, FONT_AILESI
)


# ─── Şekil Tipleri ────────────────────────────────────────────────────────────

SEKIL_DIKDORTGEN = "dikdortgen"   # işlem adımı
SEKIL_ELMAS      = "elmas"        # karar noktası
SEKIL_OK         = "ok"           # bağlantı


# ─── Veri Modeli ──────────────────────────────────────────────────────────────

class AkisSekli:
    def __init__(self, tip: str, metin: str = "",
                 x: float = 100, y: float = 100,
                 genislik: float = 160, yukseklik: float = 48,
                 kaynak_id: str = "", hedef_id: str = "",
                 sid: str = ""):
        import uuid
        self.sid = sid or str(uuid.uuid4())[:8]
        self.tip = tip
        self.metin = metin
        self.x = x
        self.y = y
        self.genislik = genislik
        self.yukseklik = yukseklik
        self.kaynak_id = kaynak_id   # ok için
        self.hedef_id = hedef_id     # ok için

    def to_dict(self):
        return {
            "sid": self.sid, "tip": self.tip, "metin": self.metin,
            "x": self.x, "y": self.y,
            "genislik": self.genislik, "yukseklik": self.yukseklik,
            "kaynak_id": self.kaynak_id, "hedef_id": self.hedef_id,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            tip=d.get("tip", SEKIL_DIKDORTGEN),
            metin=d.get("metin", ""),
            x=d.get("x", 100), y=d.get("y", 100),
            genislik=d.get("genislik", 160),
            yukseklik=d.get("yukseklik", 48),
            kaynak_id=d.get("kaynak_id", ""),
            hedef_id=d.get("hedef_id", ""),
            sid=d.get("sid", ""),
        )

    def merkez(self):
        return QPointF(self.x + self.genislik/2, self.y + self.yukseklik/2)


# ─── Varsayılan Şekiller ──────────────────────────────────────────────────────

def _varsayilan_sekiller(urun_formu: str) -> list[AkisSekli]:
    adimlar = {
        UrunFormu.FILM_TABLET.value: [
            "Tartım", "Karıştırma", "Tablet Baskı", "Film Kaplama", "Ambalajlama"
        ],
        UrunFormu.TABLET.value: [
            "Tartım", "Karıştırma", "Tablet Baskı", "Ambalajlama"
        ],
        UrunFormu.KAPSUL.value: [
            "Tartım", "Karıştırma", "Kapsül Dolum", "Ambalajlama"
        ],
    }
    liste = adimlar.get(urun_formu, adimlar[UrunFormu.FILM_TABLET.value])
    sekiller = []
    for i, ad in enumerate(liste):
        sekiller.append(AkisSekli(
            tip=SEKIL_DIKDORTGEN, metin=ad,
            x=80, y=30 + i * 80,
            genislik=200, yukseklik=50
        ))
    # Oklar
    for i in range(len(sekiller) - 1):
        sekiller.append(AkisSekli(
            tip=SEKIL_OK, metin="",
            kaynak_id=sekiller[i].sid,
            hedef_id=sekiller[i+1].sid,
        ))
    return sekiller


# ─── Canvas Widget ────────────────────────────────────────────────────────────

class AkisCanvas(QWidget):
    """
    Akış şeması çizim alanı.
    Şekiller sürüklenebilir, seçilebilir.
    """
    sekil_secildi = pyqtSignal(str)  # sid
    degisti = pyqtSignal()

    RENK_DIKDORTGEN = QColor("#EBF4FF")
    RENK_ELMAS      = QColor("#FEF9E7")
    RENK_KENARLIM   = QColor("#2C6EAB")
    RENK_SECILI     = QColor("#E74C3C")
    RENK_OK         = QColor("#2C6EAB")
    RENK_METIN      = QColor("#1A3A5C")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sekiller: list[AkisSekli] = []
        self._secili_sid: str = ""
        self._suruklenen_sid: str = ""
        self._surukle_offset = QPointF(0, 0)
        self.setMinimumSize(350, 500)
        self.setMouseTracking(True)
        self.setStyleSheet(f"background: {RENK_BG_BIRINCIL}; border: 1px solid {RENK_KENARLIK};")

    def sekilleri_yukle(self, sekiller: list[AkisSekli]):
        self._sekiller = sekiller
        self._guncelle_boyut()
        self.update()

    def _guncelle_boyut(self):
        """Canvas boyutunu içeriğe göre ayarla."""
        if not self._sekiller:
            return
        max_x = max((s.x + s.genislik for s in self._sekiller
                     if s.tip != SEKIL_OK), default=400)
        max_y = max((s.y + s.yukseklik for s in self._sekiller
                     if s.tip != SEKIL_OK), default=500)
        self.setMinimumSize(int(max_x + 60), int(max_y + 60))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Arka plan
        painter.fillRect(self.rect(), QColor(RENK_BG_BIRINCIL))

        # Hafif ızgara
        pen = QPen(QColor(RENK_KENARLIK), 0.5, Qt.PenStyle.DotLine)
        painter.setPen(pen)
        for x in range(0, self.width(), 20):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 20):
            painter.drawLine(0, y, self.width(), y)

        # Önce okları çiz
        for s in self._sekiller:
            if s.tip == SEKIL_OK:
                self._ok_ciz(painter, s)

        # Sonra şekilleri çiz
        for s in self._sekiller:
            if s.tip != SEKIL_OK:
                self._sekil_ciz(painter, s)

        painter.end()

    def _sekil_ciz(self, painter: QPainter, s: AkisSekli):
        secili = s.sid == self._secili_sid
        kenarlim_renk = self.RENK_SECILI if secili else self.RENK_KENARLIM
        kenarlim_kalinlik = 2.5 if secili else 1.5

        if s.tip == SEKIL_DIKDORTGEN:
            rect = QRectF(s.x, s.y, s.genislik, s.yukseklik)
            painter.setBrush(QBrush(self.RENK_DIKDORTGEN))
            painter.setPen(QPen(kenarlim_renk, kenarlim_kalinlik))
            painter.drawRoundedRect(rect, 8, 8)
            self._metin_ciz(painter, s, rect)

        elif s.tip == SEKIL_ELMAS:
            cx = s.x + s.genislik / 2
            cy = s.y + s.yukseklik / 2
            w2 = s.genislik / 2
            h2 = s.yukseklik / 2
            elmas = QPolygonF([
                QPointF(cx, s.y),
                QPointF(s.x + s.genislik, cy),
                QPointF(cx, s.y + s.yukseklik),
                QPointF(s.x, cy),
            ])
            painter.setBrush(QBrush(self.RENK_ELMAS))
            painter.setPen(QPen(kenarlim_renk, kenarlim_kalinlik))
            painter.drawPolygon(elmas)
            rect = QRectF(s.x, s.y, s.genislik, s.yukseklik)
            self._metin_ciz(painter, s, rect)

    def _metin_ciz(self, painter: QPainter, s: AkisSekli, rect: QRectF):
        if not s.metin:
            return
        font = QFont(FONT_AILESI, 10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(self.RENK_METIN))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, s.metin)

    def _ok_ciz(self, painter: QPainter, s: AkisSekli):
        kaynak = self._sid_bul(s.kaynak_id)
        hedef = self._sid_bul(s.hedef_id)
        if not kaynak or not hedef:
            return

        # Kaynak alt orta → Hedef üst orta
        p1 = QPointF(kaynak.x + kaynak.genislik/2,
                     kaynak.y + kaynak.yukseklik)
        p2 = QPointF(hedef.x + hedef.genislik/2, hedef.y)

        pen = QPen(self.RENK_OK, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        # Bezier eğrisi
        path = QPainterPath(p1)
        my = (p1.y() + p2.y()) / 2
        path.cubicTo(
            QPointF(p1.x(), my),
            QPointF(p2.x(), my),
            p2
        )
        painter.drawPath(path)

        # Ok başı
        painter.setBrush(QBrush(self.RENK_OK))
        painter.setPen(QPen(self.RENK_OK))
        ok_ucu = QPolygonF([
            QPointF(p2.x(), p2.y()),
            QPointF(p2.x()-6, p2.y()-10),
            QPointF(p2.x()+6, p2.y()-10),
        ])
        painter.drawPolygon(ok_ucu)

    def _sid_bul(self, sid: str):
        return next((s for s in self._sekiller if s.sid == sid), None)

    def mousePressEvent(self, event):
        pos = QPointF(event.pos())
        # Şekil seç
        tiklanan = None
        for s in reversed(self._sekiller):
            if s.tip == SEKIL_OK:
                continue
            rect = QRectF(s.x, s.y, s.genislik, s.yukseklik)
            if rect.contains(pos):
                tiklanan = s
                break

        if tiklanan:
            self._secili_sid = tiklanan.sid
            self._suruklenen_sid = tiklanan.sid
            self._surukle_offset = QPointF(
                pos.x() - tiklanan.x, pos.y() - tiklanan.y)
            self.sekil_secildi.emit(tiklanan.sid)
        else:
            self._secili_sid = ""
        self.update()

    def mouseMoveEvent(self, event):
        if self._suruklenen_sid:
            pos = QPointF(event.pos())
            s = self._sid_bul(self._suruklenen_sid)
            if s:
                s.x = max(0, pos.x() - self._surukle_offset.x())
                s.y = max(0, pos.y() - self._surukle_offset.y())
                self._guncelle_boyut()
                self.update()
                self.degisti.emit()

    def mouseReleaseEvent(self, event):
        self._suruklenen_sid = ""

    def get_sekiller(self): return self._sekiller


# ─── Sol Form Paneli ──────────────────────────────────────────────────────────

class FormPaneli(QWidget):
    """
    Sol panel — form tabanlı eleman yönetimi.
    Operasyon Ekle / Karar Noktası Ekle / Ok Ekle butonları.
    Liste: her eleman düzenlenebilir ve silinebilir.
    """
    degisti = pyqtSignal()
    sekil_guncellendi = pyqtSignal()  # canvas'ı yenile

    def __init__(self, canvas: AkisCanvas, parent=None):
        super().__init__(parent)
        self._canvas = canvas
        self._secili_sid = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        # Başlık
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:{RENK_BG_IKINCIL};border-bottom:1px solid {RENK_KENARLIK};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(12,8,12,8)
        hl.addWidget(QLabel("Akış Şeması Elemanları"))
        layout.addWidget(hdr)

        # Eleman listesi
        self._liste = QTableWidget()
        self._liste.setColumnCount(3)
        self._liste.setHorizontalHeaderLabels(["Tip", "Metin", ""])
        self._liste.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self._liste.setColumnWidth(0, 90)
        self._liste.setColumnWidth(2, 32)
        self._liste.verticalHeader().setVisible(False)
        self._liste.setShowGrid(True)
        self._liste.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked |
            QAbstractItemView.EditTrigger.SelectedClicked)
        self._liste.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self._liste.setStyleSheet(f"""
            QTableWidget {{
                border: none; font-size: 11px;
                font-family: {FONT_AILESI};
                gridline-color: {RENK_KENARLIK};
            }}
            QTableWidget::item {{ padding: 3px 5px; }}
            QTableWidget::item:selected {{
                background: {RENK_PRIMARY_ACIK};
                color: {RENK_PRIMARY_KOYU};
            }}
            QHeaderView::section {{
                background: {RENK_BG_IKINCIL}; border: none;
                border-bottom: 1px solid {RENK_KENARLIK};
                padding: 4px; font-size: 10px;
                font-weight: bold; color: {RENK_YAZI_IKINCIL};
            }}
        """)
        self._liste.cellChanged.connect(self._liste_degisti)
        self._liste.cellClicked.connect(self._liste_tiklandi)
        layout.addWidget(self._liste, 1)

        # Butonlar
        btn_frame = QFrame()
        btn_frame.setStyleSheet(
            f"background:{RENK_BG_IKINCIL};border-top:1px solid {RENK_KENARLIK};")
        btn_l = QVBoxLayout(btn_frame)
        btn_l.setContentsMargins(10, 8, 10, 8); btn_l.setSpacing(5)

        for txt, tip, renk in [
            ("+ Operasyon Ekle",      SEKIL_DIKDORTGEN, RENK_PRIMARY),
            ("◆ Karar Noktası Ekle",  SEKIL_ELMAS,      "#E67E22"),
            ("→ Ok Ekle",             SEKIL_OK,         "#27AE60"),
        ]:
            btn = QPushButton(txt)
            btn.setStyleSheet(f"""
                QPushButton {{
                    border: 1px solid {renk};
                    border-radius: 5px;
                    background: white;
                    color: {renk};
                    font-size: 11px;
                    padding: 5px 10px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: {renk}22;
                }}
            """)
            btn.clicked.connect(lambda _, t=tip: self._eleman_ekle(t))
            btn_l.addWidget(btn)

        layout.addWidget(btn_frame)

        # Canvas sinyalini bağla
        canvas.sekil_secildi.connect(self._canvas_secim)

    def _eleman_ekle(self, tip: str):
        sekiller = self._canvas.get_sekiller()

        # Ok için kaynak/hedef seç
        if tip == SEKIL_OK:
            secenekler = [s for s in sekiller if s.tip != SEKIL_OK]
            if len(secenekler) < 2:
                QMessageBox.information(
                    self, "Ok Ekle",
                    "Ok eklemek için en az 2 şekil olmalıdır.")
                return

            from PyQt6.QtWidgets import QInputDialog
            isimler = [f"{s.metin or s.sid} [{s.tip}]" for s in secenekler]
            k, ok1 = QInputDialog.getItem(
                self, "Ok Ekle", "Kaynak şekil:", isimler, 0, False)
            if not ok1: return
            h, ok2 = QInputDialog.getItem(
                self, "Ok Ekle", "Hedef şekil:", isimler, 1, False)
            if not ok2: return
            k_idx = isimler.index(k)
            h_idx = isimler.index(h)
            yeni = AkisSekli(
                tip=SEKIL_OK,
                kaynak_id=secenekler[k_idx].sid,
                hedef_id=secenekler[h_idx].sid)
        else:
            # Pozisyonu mevcut şekillerin altına yerleştir
            diger = [s for s in sekiller if s.tip != SEKIL_OK]
            y_yeni = max((s.y + s.yukseklik for s in diger), default=20) + 20
            yeni = AkisSekli(
                tip=tip, metin="Yeni Adım",
                x=80, y=y_yeni,
                genislik=200, yukseklik=50 if tip == SEKIL_DIKDORTGEN else 60)

        sekiller.append(yeni)
        self._canvas.update()
        self._listeyi_yenile()
        self.degisti.emit()

    def _listeyi_yenile(self):
        self._liste.blockSignals(True)
        self._liste.clearContents()
        sekiller = self._canvas.get_sekiller()
        self._liste.setRowCount(len(sekiller))
        tip_isimler = {
            SEKIL_DIKDORTGEN: "Operasyon",
            SEKIL_ELMAS: "Karar",
            SEKIL_OK: "Ok",
        }
        for i, s in enumerate(sekiller):
            self._liste.setRowHeight(i, 26)
            tip_item = QTableWidgetItem(tip_isimler.get(s.tip, s.tip))
            tip_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            if s.tip == SEKIL_OK:
                kaynak = next((x for x in sekiller if x.sid == s.kaynak_id), None)
                hedef = next((x for x in sekiller if x.sid == s.hedef_id), None)
                metin = f"{kaynak.metin if kaynak else '?'} → {hedef.metin if hedef else '?'}"
                metin_item = QTableWidgetItem(metin)
                metin_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            else:
                metin_item = QTableWidgetItem(s.metin)
            # Seçili vurgusu
            if s.sid == self._secili_sid:
                for item in [tip_item, metin_item]:
                    item.setBackground(QBrush(QColor(RENK_PRIMARY_ACIK)))
            self._liste.setItem(i, 0, tip_item)
            self._liste.setItem(i, 1, metin_item)
            # Sil
            sil_item = QTableWidgetItem("✕")
            sil_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            sil_item.setForeground(QBrush(QColor("#C0392B")))
            sil_item.setBackground(QBrush(QColor("#FADBD8")))
            sil_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._liste.setItem(i, 2, sil_item)
        self._liste.blockSignals(False)

    def _liste_degisti(self, r, c):
        if c != 1: return
        sekiller = self._canvas.get_sekiller()
        if r >= len(sekiller): return
        s = sekiller[r]
        if s.tip == SEKIL_OK: return
        item = self._liste.item(r, c)
        if item:
            s.metin = item.text().strip()
            self._canvas.update()
            self.degisti.emit()

    def _liste_tiklandi(self, r, c):
        sekiller = self._canvas.get_sekiller()
        if r >= len(sekiller): return
        if c == 2:
            sekiller.pop(r)
            self._canvas.update()
            self._listeyi_yenile()
            self.degisti.emit()
        else:
            s = sekiller[r]
            self._secili_sid = s.sid
            self._canvas._secili_sid = s.sid
            self._canvas.update()
            self._listeyi_yenile()

    def _canvas_secim(self, sid: str):
        self._secili_sid = sid
        self._listeyi_yenile()

    def yukle(self, sekiller: list[AkisSekli]):
        self._canvas.sekilleri_yukle(sekiller)
        self._listeyi_yenile()

    def varsayilan_yukle(self, urun_formu: str):
        sekiller = _varsayilan_sekiller(urun_formu)
        self.yukle(sekiller)


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

        # Sekmeler: Akış Şeması Editörü
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane{{border:none;background:{RENK_BG_BIRINCIL};}}
            QTabBar::tab{{border:1px solid {RENK_KENARLIK};border-bottom:none;
            border-radius:6px 6px 0 0;padding:6px 14px;font-size:11px;
            color:{RENK_YAZI_IKINCIL};background:{RENK_BG_IKINCIL};margin-right:2px;}}
            QTabBar::tab:selected{{background:{RENK_BG_BIRINCIL};
            color:{RENK_PRIMARY};font-weight:bold;}}
        """)

        # Sekme 1: Akış Şeması Editörü
        from ui.akis_editoru import AkisEditoruWidget
        self._akis_editoru = AkisEditoruWidget()
        self._akis_editoru.degisti.connect(self._on_degisti)
        self.tabs.addTab(self._akis_editoru, "Akış Şeması Editörü")

        layout.addWidget(self.tabs, 1)

    def _yukle(self):
        elemanlar = getattr(self._proje, 'akis_elemanlar', [])
        oklar = getattr(self._proje, 'akis_oklar', [])
        self._akis_editoru.yukle(elemanlar, oklar)
        self.lbl_durum.setVisible(False)

    def _on_degisti(self):
        self.lbl_durum.setText("● Kaydedilmemiş değişiklik")
        self.lbl_durum.setStyleSheet(f"""
            font-size:11px; color:{RENK_PRIMARY_KOYU};
            background:{RENK_PRIMARY_ACIK}; border-radius:4px; padding:2px 8px;
        """)
        self.lbl_durum.setVisible(True)
        self.degisti.emit()

    def _kaydet(self):
        elemanlar, oklar = self._akis_editoru.to_data()
        self._proje.akis_elemanlar = elemanlar
        self._proje.akis_oklar = oklar
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
