"""
PV-DOC — Proses Akış Şeması Editörü
Seçenek 2: 4 sütun kılavuzlu serbest canvas
Sütunlar: Başlangıç Maddeleri | Proses Adımı | IPK Testleri | Rutin/Val. Testleri
Word çıktısı için PNG render.
"""

import json
import uuid
import math
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFrame, QLabel, QLineEdit, QPushButton, QScrollArea,
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem,
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsPathItem,
    QGraphicsEllipseItem, QSizePolicy, QToolButton, QButtonGroup,
    QColorDialog, QComboBox, QSpinBox, QTextEdit, QInputDialog,
    QApplication, QMessageBox, QFileDialog, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QPointF, QRectF, QSizeF, QLineF, QTimer
)
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QFont, QPainter, QPolygonF,
    QPainterPath, QTransform, QImage, QPixmap, QCursor,
    QKeySequence, QAction
)

from ui.stiller import (
    RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    FONT_AILESI
)

# ─── Sabitler ────────────────────────────────────────────────────────────────

CANVAS_W = 1400
CANVAS_H = 1000
IZGARA_ARALIK = 20

# 4 Sütun kılavuz oranları
SUTUN_ORANLARI = [0.0, 0.22, 0.50, 0.72, 1.0]
SUTUN_ADLARI = [
    "Başlangıç Maddeleri",
    "Proses Adımı",
    "IPK Testleri",
    "Rutin / Validasyon Testleri"
]

# Araç modları
MOD_SEC     = "sec"
MOD_DIKDORT = "dikdortgen"
MOD_ELMAS   = "elmas"
MOD_OVAL    = "oval"
MOD_METIN   = "metin"
MOD_OK      = "ok"
MOD_CIZGI   = "cizgi"

SEKIL_RENKLERI = {
    "siyah":   "#1A1A1A",
    "mavi":    "#1a5fa5",
    "yesil":   "#2e7d32",
    "turuncu": "#e65100",
    "kirmizi": "#b71c1c",
    "gri":     "#607d8b",
}

KENAR_STILLERI = {
    "Düz":   Qt.PenStyle.SolidLine,
    "Kesik": Qt.PenStyle.DashLine,
    "Nokta": Qt.PenStyle.DotLine,
}


# ─── Veri Modeli ─────────────────────────────────────────────────────────────

class SekliVeri:
    def __init__(self, tip="dikdortgen", metin="",
                 x=100.0, y=100.0, w=150.0, h=50.0,
                 kenar_renk="#1A1A1A", kenar_stil="Düz",
                 yazi_boyut=11, sid=None):
        self.id = sid or str(uuid.uuid4())[:8]
        self.tip = tip
        self.metin = metin
        self.x = x; self.y = y
        self.w = w; self.h = h
        self.kenar_renk = kenar_renk
        self.kenar_stil = kenar_stil
        self.yazi_boyut = yazi_boyut

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d):
        s = cls(); s.__dict__.update(d); return s


class OkVeri:
    def __init__(self, x1=0, y1=0, x2=0, y2=0,
                 etiket="", tip="duz", oid=None):
        self.id = oid or str(uuid.uuid4())[:8]
        self.x1 = x1; self.y1 = y1
        self.x2 = x2; self.y2 = y2
        self.etiket = etiket
        self.tip = tip  # duz, l, asagi

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d):
        o = cls(); o.__dict__.update(d); return o


# ─── Şekil Grafik Elemanı ─────────────────────────────────────────────────────

TUTAMAC_BOYUT = 8

class Tutamac(QGraphicsRectItem):
    def __init__(self, yön, parent):
        super().__init__(-TUTAMAC_BOYUT/2, -TUTAMAC_BOYUT/2,
                         TUTAMAC_BOYUT, TUTAMAC_BOYUT, parent)
        self.yön = yön
        self.setBrush(QBrush(QColor("#1a5fa5")))
        self.setPen(QPen(QColor("white"), 1.5))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, False)
        self.setCursor(self._cursor())
        self.setZValue(10)

    def _cursor(self):
        cursors = {
            "tl": Qt.CursorShape.SizeFDiagCursor,
            "tr": Qt.CursorShape.SizeBDiagCursor,
            "bl": Qt.CursorShape.SizeBDiagCursor,
            "br": Qt.CursorShape.SizeFDiagCursor,
            "t":  Qt.CursorShape.SizeVerCursor,
            "b":  Qt.CursorShape.SizeVerCursor,
            "l":  Qt.CursorShape.SizeHorCursor,
            "r":  Qt.CursorShape.SizeHorCursor,
        }
        return cursors.get(self.yön, Qt.CursorShape.SizeAllCursor)


class SekliItem(QGraphicsItem):
    def __init__(self, veri: SekliVeri, sahne: 'AkisSahne'):
        super().__init__()
        self.veri = veri
        self.sahne = sahne
        self._tutamaclar = {}
        self._yeniden_boyutlandirma = False
        self._yb_yon = None
        self._yb_baslangic = None
        self._yb_orig_rect = None

        self.setPos(veri.x, veri.y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def boundingRect(self):
        return QRectF(0, 0, self.veri.w, self.veri.h)

    def _pen(self):
        stil = KENAR_STILLERI.get(self.veri.kenar_stil, Qt.PenStyle.SolidLine)
        kalınlık = 2.5 if self.isSelected() else 1.5
        renk = RENK_PRIMARY if self.isSelected() else self.veri.kenar_renk
        return QPen(QColor(renk), kalınlık, stil)

    def _brush(self):
        return QBrush(QColor("white"))

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self._pen())
        painter.setBrush(self._brush())
        w, h = self.veri.w, self.veri.h
        tip = self.veri.tip

        if tip == "dikdortgen" or tip == "metin":
            painter.drawRoundedRect(QRectF(0, 0, w, h), 6, 6)
        elif tip == "elmas":
            poly = QPolygonF([
                QPointF(w/2, 0), QPointF(w, h/2),
                QPointF(w/2, h), QPointF(0, h/2)
            ])
            painter.drawPolygon(poly)
        elif tip == "oval":
            painter.drawEllipse(QRectF(0, 0, w, h))

        # Metin
        painter.setPen(QPen(QColor(self.veri.kenar_renk)))
        font = QFont(FONT_AILESI, self.veri.yazi_boyut)
        painter.setFont(font)
        painter.drawText(
            QRectF(4, 4, w-8, h-8),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self.veri.metin
        )

    def _tutamaclari_guncelle(self):
        w, h = self.veri.w, self.veri.h
        pozisyonlar = {
            "tl": QPointF(0, 0),    "t":  QPointF(w/2, 0),   "tr": QPointF(w, 0),
            "l":  QPointF(0, h/2),                             "r":  QPointF(w, h/2),
            "bl": QPointF(0, h),    "b":  QPointF(w/2, h),   "br": QPointF(w, h),
        }
        for yon, pos in pozisyonlar.items():
            if yon not in self._tutamaclar:
                t = Tutamac(yon, self)
                self._tutamaclar[yon] = t
            self._tutamaclar[yon].setPos(pos)

    def _tutamaclari_gizle(self):
        for t in self._tutamaclar.values():
            t.setVisible(False)

    def _tutamaclari_goster(self):
        self._tutamaclari_guncelle()
        for t in self._tutamaclar.values():
            t.setVisible(True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value:
                self._tutamaclari_goster()
            else:
                self._tutamaclari_gizle()
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.veri.x = self.pos().x()
            self.veri.y = self.pos().y()
            self.sahne.okları_guncelle()
            self.sahne.degisti.emit()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        metin, ok = QInputDialog.getMultiLineText(
            None, "Metin Düzenle", "Metin:", self.veri.metin)
        if ok:
            self.veri.metin = metin
            self.update()
            self.sahne.degisti.emit()

    def mousePressEvent(self, event):
        # Tutamaca tıklandı mı?
        for yon, t in self._tutamaclar.items():
            if t.isVisible() and t.sceneBoundingRect().contains(
                    event.scenePos()):
                self._yeniden_boyutlandirma = True
                self._yb_yon = yon
                self._yb_baslangic = event.scenePos()
                self._yb_orig_rect = QRectF(
                    self.veri.x, self.veri.y, self.veri.w, self.veri.h)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._yeniden_boyutlandirma:
            delta = event.scenePos() - self._yb_baslangic
            r = QRectF(self._yb_orig_rect)
            yon = self._yb_yon
            min_w, min_h = 40, 24

            if "r" in yon:
                r.setRight(max(r.left() + min_w, r.right() + delta.x()))
            if "b" in yon:
                r.setBottom(max(r.top() + min_h, r.bottom() + delta.y()))
            if "l" in yon:
                r.setLeft(min(r.right() - min_w, r.left() + delta.x()))
            if "t" in yon:
                r.setTop(min(r.bottom() - min_h, r.top() + delta.y()))

            self.prepareGeometryChange()
            self.setPos(r.topLeft())
            self.veri.x = r.x(); self.veri.y = r.y()
            self.veri.w = r.width(); self.veri.h = r.height()
            self._tutamaclari_guncelle()
            self.sahne.okları_guncelle()
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._yeniden_boyutlandirma:
            self._yeniden_boyutlandirma = False
            self._yb_yon = None
            self.sahne.degisti.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)


# ─── Ok Grafik Elemanı ────────────────────────────────────────────────────────

class OkItem(QGraphicsPathItem):
    def __init__(self, veri: OkVeri):
        super().__init__()
        self.veri = veri
        self._ciz()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(-1)

    def _ciz(self):
        x1, y1, x2, y2 = self.veri.x1, self.veri.y1, self.veri.x2, self.veri.y2
        path = QPainterPath()
        path.moveTo(x1, y1)

        tip = self.veri.tip
        if tip == "l":
            path.lineTo(x2, y1)
            path.lineTo(x2, y2)
        else:
            path.lineTo(x2, y2)

        # Ok başı
        dx = x2 - (x2 if tip == "l" else x1)
        dy = y2 - y1
        uzunluk = math.sqrt(dx*dx + dy*dy) if (dx != 0 or dy != 0) else 1
        if uzunluk > 0:
            ux = (dx / uzunluk) if tip != "l" else 0
            uy = dy / uzunluk
            ok_basi = QPainterPath()
            ok_basi.moveTo(x2, y2)
            ok_basi.lineTo(x2 - 10*ux - 5*uy, y2 - 10*uy + 5*ux)
            ok_basi.lineTo(x2 - 10*ux + 5*uy, y2 - 10*uy - 5*ux)
            ok_basi.closeSubpath()
            path.addPath(ok_basi)

        self.setPath(path)
        renk = RENK_PRIMARY if self.isSelected() else "#455A64"
        self.setPen(QPen(QColor(renk), 1.8))
        self.setBrush(QBrush(QColor("#455A64")))

    def guncelle(self):
        self._ciz()


# ─── Sahne ────────────────────────────────────────────────────────────────────

class AkisSahne(QGraphicsScene):
    degisti = pyqtSignal()
    sekil_secildi = pyqtSignal(object)  # SekliVeri veya None

    def __init__(self):
        super().__init__(0, 0, CANVAS_W, CANVAS_H)
        self._mod = MOD_SEC
        self._sekil_items: dict[str, SekliItem] = {}
        self._ok_items: dict[str, OkItem] = {}
        self._sekil_verileri: list[SekliVeri] = []
        self._ok_verileri: list[OkVeri] = []
        self._geri_al_yigin: list = []
        self._ok_baslangic: QPointF | None = None
        self._gecici_ok: QGraphicsLineItem | None = None
        self._izgara_aktif = True
        self.selectionChanged.connect(self._secim_degisti)

    def set_mod(self, mod: str):
        self._mod = mod

    # ── Izgara çizimi ──────────────────────────────────────────────────────────

    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.fillRect(rect, QColor("#F8F9FA"))

        # Izgara
        if self._izgara_aktif:
            painter.setPen(QPen(QColor("#E0E4E8"), 0.5))
            sol = int(rect.left()) - (int(rect.left()) % IZGARA_ARALIK)
            ust = int(rect.top()) - (int(rect.top()) % IZGARA_ARALIK)
            x = sol
            while x < rect.right():
                painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
                x += IZGARA_ARALIK
            y = ust
            while y < rect.bottom():
                painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
                y += IZGARA_ARALIK

        # Sütun kılavuzları
        for i, oran in enumerate(SUTUN_ORANLARI[1:-1], 1):
            x = int(CANVAS_W * oran)
            painter.setPen(QPen(QColor("#B5C8E0"), 1.2, Qt.PenStyle.DashLine))
            painter.drawLine(x, 0, x, CANVAS_H)

        # Sütun başlıkları
        for i in range(4):
            x1 = int(CANVAS_W * SUTUN_ORANLARI[i])
            x2 = int(CANVAS_W * SUTUN_ORANLARI[i+1])
            cx = (x1 + x2) // 2
            painter.setPen(QPen(QColor("#7B9EC4")))
            font = QFont(FONT_AILESI, 9)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                QRectF(x1+4, 4, x2-x1-8, 22),
                Qt.AlignmentFlag.AlignCenter,
                SUTUN_ADLARI[i]
            )

    # ── Mouse Events ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event); return

        pos = event.scenePos()

        if self._mod == MOD_SEC:
            super().mousePressEvent(event); return

        if self._mod == MOD_OK or self._mod == MOD_CIZGI:
            self._ok_baslangic = pos
            self._gecici_ok = QGraphicsLineItem(
                pos.x(), pos.y(), pos.x(), pos.y())
            self._gecici_ok.setPen(QPen(QColor("#455A64"), 1.5,
                                        Qt.PenStyle.DashLine))
            self.addItem(self._gecici_ok)
            return

        # Şekil ekle
        self._durum_kaydet()
        tip_map = {
            MOD_DIKDORT: ("dikdortgen", 160, 50),
            MOD_ELMAS:   ("elmas",      140, 70),
            MOD_OVAL:    ("oval",       130, 45),
            MOD_METIN:   ("metin",      160, 45),
        }
        if self._mod in tip_map:
            tip, w, h = tip_map[self._mod]
            x = self._izgara_yapistir(pos.x() - w/2)
            y = self._izgara_yapistir(pos.y() - h/2)
            veri = SekliVeri(tip=tip, metin="Metin",
                             x=x, y=y, w=w, h=h)
            self._sekil_ekle(veri)
            self.degisti.emit()

    def mouseMoveEvent(self, event):
        if self._gecici_ok and self._ok_baslangic:
            p = event.scenePos()
            self._gecici_ok.setLine(
                self._ok_baslangic.x(), self._ok_baslangic.y(),
                p.x(), p.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if (self._gecici_ok and self._ok_baslangic and
                event.button() == Qt.MouseButton.LeftButton):
            bitis = event.scenePos()
            self.removeItem(self._gecici_ok)
            self._gecici_ok = None
            # Ok ekle
            self._durum_kaydet()
            tip = "l" if self._mod == MOD_CIZGI else "duz"
            ok = OkVeri(
                x1=self._ok_baslangic.x(), y1=self._ok_baslangic.y(),
                x2=bitis.x(), y2=bitis.y(), tip=tip)
            self._ok_ekle(ok)
            self._ok_baslangic = None
            self.degisti.emit()
            return
        super().mouseReleaseEvent(event)

    # ── Izgara yapıştır ───────────────────────────────────────────────────────

    def _izgara_yapistir(self, v: float) -> float:
        if not self._izgara_aktif:
            return v
        return round(v / IZGARA_ARALIK) * IZGARA_ARALIK

    # ── Şekil / Ok yönetimi ───────────────────────────────────────────────────

    def _sekil_ekle(self, veri: SekliVeri):
        self._sekil_verileri.append(veri)
        item = SekliItem(veri, self)
        self.addItem(item)
        self._sekil_items[veri.id] = item

    def _ok_ekle(self, veri: OkVeri):
        self._ok_verileri.append(veri)
        item = OkItem(veri)
        self.addItem(item)
        self._ok_items[veri.id] = item

    def okları_guncelle(self):
        for oi in self._ok_items.values():
            oi.guncelle()

    def _secim_degisti(self):
        secili = self.selectedItems()
        if secili and isinstance(secili[0], SekliItem):
            self.sekil_secildi.emit(secili[0].veri)
        else:
            self.sekil_secildi.emit(None)

    def secili_sil(self):
        self._durum_kaydet()
        for item in self.selectedItems():
            if isinstance(item, SekliItem):
                self._sekil_verileri = [
                    v for v in self._sekil_verileri if v.id != item.veri.id]
                del self._sekil_items[item.veri.id]
                self.removeItem(item)
            elif isinstance(item, OkItem):
                self._ok_verileri = [
                    v for v in self._ok_verileri if v.id != item.veri.id]
                del self._ok_items[item.veri.id]
                self.removeItem(item)
        self.degisti.emit()

    def secili_cogalt(self):
        self._durum_kaydet()
        for item in list(self.selectedItems()):
            if isinstance(item, SekliItem):
                v = item.veri
                yeni = SekliVeri(
                    tip=v.tip, metin=v.metin,
                    x=v.x+20, y=v.y+20, w=v.w, h=v.h,
                    kenar_renk=v.kenar_renk,
                    kenar_stil=v.kenar_stil,
                    yazi_boyut=v.yazi_boyut)
                self._sekil_ekle(yeni)
        self.degisti.emit()

    # ── Geri al ───────────────────────────────────────────────────────────────

    def _durum_kaydet(self):
        durum = {
            "sekiller": [s.to_dict() for s in self._sekil_verileri],
            "oklar":    [o.to_dict() for o in self._ok_verileri],
        }
        self._geri_al_yigin.append(durum)
        if len(self._geri_al_yigin) > 50:
            self._geri_al_yigin.pop(0)

    def geri_al(self):
        if not self._geri_al_yigin: return
        durum = self._geri_al_yigin.pop()
        self._yukle_durum(durum)

    def _yukle_durum(self, durum):
        for item in list(self._sekil_items.values()):
            self.removeItem(item)
        for item in list(self._ok_items.values()):
            self.removeItem(item)
        self._sekil_items.clear(); self._ok_items.clear()
        self._sekil_verileri.clear(); self._ok_verileri.clear()

        for d in durum["sekiller"]:
            self._sekil_ekle(SekliVeri.from_dict(d))
        for d in durum["oklar"]:
            self._ok_ekle(OkVeri.from_dict(d))
        self.degisti.emit()

    # ── Serialize ─────────────────────────────────────────────────────────────

    def to_data(self):
        return {
            "sekiller": [s.to_dict() for s in self._sekil_verileri],
            "oklar":    [o.to_dict() for o in self._ok_verileri],
        }

    def yukle(self, data: dict):
        self._yukle_durum(data)

    def temizle(self):
        self._yukle_durum({"sekiller": [], "oklar": []})

    # ── PNG Render ────────────────────────────────────────────────────────────

    def png_render(self, dpi: int = 200) -> bytes:
        """Tüm canvas'ı PNG binary olarak döner."""
        import tempfile, os
        # Şekillerin bounding rect'ini bul
        rect = self.itemsBoundingRect()
        if rect.isEmpty():
            rect = QRectF(0, 0, CANVAS_W, CANVAS_H)
        margin = 30
        rect = rect.adjusted(-margin, -margin, margin, margin)
        rect = rect.intersected(QRectF(0, 0, CANVAS_W, CANVAS_H))

        scale = dpi / 96.0
        img = QImage(int(rect.width() * scale), int(rect.height() * scale),
                     QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.white)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(scale, scale)
        self.render(painter, source=rect)
        painter.end()

        tmp = tempfile.mktemp(suffix='.png')
        img.save(tmp)
        with open(tmp, 'rb') as f:
            data = f.read()
        os.unlink(tmp)
        return data

    def png_kaydet(self, dosya: str, dpi: int = 200):
        data = self.png_render(dpi)
        with open(dosya, 'wb') as f:
            f.write(data)


# ─── Canvas Görünümü ─────────────────────────────────────────────────────────

class AkisCanvas(QGraphicsView):
    def __init__(self, sahne: AkisSahne, parent=None):
        super().__init__(sahne, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("background: #F8F9FA; border: none;")
        self.fitInView(QRectF(0, 0, CANVAS_W, CANVAS_H),
                       Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.87
        self.scale(factor, factor)

    def set_mod(self, mod: str):
        self.scene().set_mod(mod)
        if mod == MOD_SEC:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif mod in (MOD_OK, MOD_CIZGI):
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)

    def keyPressEvent(self, event):
        sahne = self.scene()
        if event.matches(QKeySequence.StandardKey.Undo):
            sahne.geri_al()
        elif event.key() == Qt.Key.Key_Delete:
            sahne.secili_sil()
        elif event.matches(QKeySequence.StandardKey.Copy) or (
                event.key() == Qt.Key.Key_D and
                event.modifiers() == Qt.KeyboardModifier.ControlModifier):
            sahne.secili_cogalt()
        else:
            super().keyPressEvent(event)


# ─── Sağ Özellikler Paneli ───────────────────────────────────────────────────

class OzelliklerPaneli(QWidget):
    degisti = pyqtSignal(object)  # SekliVeri

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(210)
        self._veri: SekliVeri | None = None
        self._guncelleniyor = False

        l = QVBoxLayout(self)
        l.setContentsMargins(10, 10, 10, 10); l.setSpacing(8)

        baslik = QLabel("Özellikler")
        baslik.setStyleSheet(
            f"font-size:12px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        l.addWidget(baslik)

        self.lbl_bos = QLabel("Şekil seçilmedi")
        self.lbl_bos.setStyleSheet(
            f"font-size:11px;color:{RENK_YAZI_UCUNCUL};"
            f"padding:20px 0;text-align:center;")
        self.lbl_bos.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.panel = QWidget()
        pl = QVBoxLayout(self.panel)
        pl.setContentsMargins(0,0,0,0); pl.setSpacing(6)

        # Metin
        pl.addWidget(self._etiket("Metin"))
        self.txt_metin = QTextEdit(); self.txt_metin.setMaximumHeight(70)
        self.txt_metin.setStyleSheet(self._input_stil())
        self.txt_metin.textChanged.connect(self._metin_degisti)
        pl.addWidget(self.txt_metin)

        # Boyut
        pl.addWidget(self._etiket("Genişlik × Yükseklik"))
        boyut_w = QWidget(); bl = QHBoxLayout(boyut_w)
        bl.setContentsMargins(0,0,0,0); bl.setSpacing(4)
        self.spin_w = QSpinBox(); self.spin_w.setRange(20, 1200)
        self.spin_h = QSpinBox(); self.spin_h.setRange(15, 900)
        for sp in (self.spin_w, self.spin_h):
            sp.setStyleSheet(self._input_stil()); bl.addWidget(sp)
        self.spin_w.valueChanged.connect(self._boyut_degisti)
        self.spin_h.valueChanged.connect(self._boyut_degisti)
        pl.addWidget(boyut_w)

        # Konum
        pl.addWidget(self._etiket("X × Y"))
        konum_w = QWidget(); kl = QHBoxLayout(konum_w)
        kl.setContentsMargins(0,0,0,0); kl.setSpacing(4)
        self.spin_x = QSpinBox(); self.spin_x.setRange(0, 1400)
        self.spin_y = QSpinBox(); self.spin_y.setRange(0, 1000)
        for sp in (self.spin_x, self.spin_y):
            sp.setStyleSheet(self._input_stil()); kl.addWidget(sp)
        self.spin_x.valueChanged.connect(self._konum_degisti)
        self.spin_y.valueChanged.connect(self._konum_degisti)
        pl.addWidget(konum_w)

        # Yazı boyutu
        pl.addWidget(self._etiket("Yazı Boyutu"))
        self.spin_yazi = QSpinBox(); self.spin_yazi.setRange(7, 24)
        self.spin_yazi.setStyleSheet(self._input_stil())
        self.spin_yazi.valueChanged.connect(self._yazi_degisti)
        pl.addWidget(self.spin_yazi)

        # Kenarlık rengi
        pl.addWidget(self._etiket("Kenarlık Rengi"))
        renk_w = QWidget(); rl = QHBoxLayout(renk_w)
        rl.setContentsMargins(0,0,0,0); rl.setSpacing(4)
        self._renk_butonlar = {}
        for isim, renk in SEKIL_RENKLERI.items():
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(f"""
                QPushButton{{background:{renk};border:2px solid transparent;
                border-radius:11px;}}
                QPushButton:checked{{border-color:#1a5fa5;}}
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, r=renk: self._renk_sec(r))
            rl.addWidget(btn)
            self._renk_butonlar[renk] = btn
        pl.addWidget(renk_w)

        # Kenarlık stili
        pl.addWidget(self._etiket("Kenarlık Stili"))
        self.combo_stil = QComboBox()
        self.combo_stil.addItems(list(KENAR_STILLERI.keys()))
        self.combo_stil.setStyleSheet(self._input_stil())
        self.combo_stil.currentTextChanged.connect(self._stil_degisti)
        pl.addWidget(self.combo_stil)

        # Butonlar
        pl.addSpacing(4)
        btn_kopyala = QPushButton("⧉  Çoğalt (Ctrl+D)")
        btn_kopyala.setStyleSheet(f"""
            QPushButton{{border:1px solid {RENK_KENARLIK};border-radius:5px;
            background:{RENK_BG_IKINCIL};color:{RENK_YAZI_IKINCIL};
            font-size:11px;padding:5px;}}
            QPushButton:hover{{background:{RENK_PRIMARY_ACIK};
            color:{RENK_PRIMARY};}}
        """)
        pl.addWidget(btn_kopyala)

        btn_sil = QPushButton("✕  Sil (Del)")
        btn_sil.setStyleSheet(f"""
            QPushButton{{border:1px solid #F1948A;border-radius:5px;
            background:#FADBD8;color:#C0392B;font-size:11px;padding:5px;}}
            QPushButton:hover{{background:#F1948A;color:white;}}
        """)
        pl.addWidget(btn_sil)
        pl.addStretch()

        l.addWidget(self.lbl_bos)
        l.addWidget(self.panel)
        l.addStretch()

        self.panel.setVisible(False)

    def _etiket(self, txt):
        lbl = QLabel(txt)
        lbl.setStyleSheet(
            f"font-size:10px;font-weight:bold;color:{RENK_YAZI_IKINCIL};")
        return lbl

    def _input_stil(self):
        return f"""
            QSpinBox, QTextEdit, QComboBox{{
                border:1px solid {RENK_KENARLIK};border-radius:4px;
                padding:3px 6px;font-size:11px;
                background:{RENK_BG_BIRINCIL};
            }}
        """

    def yukle(self, veri: SekliVeri | None):
        self._veri = veri
        if veri is None:
            self.lbl_bos.setVisible(True)
            self.panel.setVisible(False)
            return
        self.lbl_bos.setVisible(False)
        self.panel.setVisible(True)

        self._guncelleniyor = True
        self.txt_metin.setPlainText(veri.metin)
        self.spin_w.setValue(int(veri.w))
        self.spin_h.setValue(int(veri.h))
        self.spin_x.setValue(int(veri.x))
        self.spin_y.setValue(int(veri.y))
        self.spin_yazi.setValue(veri.yazi_boyut)
        for renk, btn in self._renk_butonlar.items():
            btn.setChecked(renk == veri.kenar_renk)
        idx = self.combo_stil.findText(veri.kenar_stil)
        if idx >= 0:
            self.combo_stil.setCurrentIndex(idx)
        self._guncelleniyor = False

    def _metin_degisti(self):
        if self._guncelleniyor or not self._veri: return
        self._veri.metin = self.txt_metin.toPlainText()
        self.degisti.emit(self._veri)

    def _boyut_degisti(self):
        if self._guncelleniyor or not self._veri: return
        self._veri.w = self.spin_w.value()
        self._veri.h = self.spin_h.value()
        self.degisti.emit(self._veri)

    def _konum_degisti(self):
        if self._guncelleniyor or not self._veri: return
        self._veri.x = self.spin_x.value()
        self._veri.y = self.spin_y.value()
        self.degisti.emit(self._veri)

    def _yazi_degisti(self):
        if self._guncelleniyor or not self._veri: return
        self._veri.yazi_boyut = self.spin_yazi.value()
        self.degisti.emit(self._veri)

    def _renk_sec(self, renk: str):
        if self._guncelleniyor or not self._veri: return
        self._veri.kenar_renk = renk
        for r, btn in self._renk_butonlar.items():
            btn.setChecked(r == renk)
        self.degisti.emit(self._veri)

    def _stil_degisti(self, stil: str):
        if self._guncelleniyor or not self._veri: return
        self._veri.kenar_stil = stil
        self.degisti.emit(self._veri)


# ─── Araç Çubuğu ─────────────────────────────────────────────────────────────

class AracCubugu(QFrame):
    mod_degisti = pyqtSignal(str)
    geri_al = pyqtSignal()
    izgara_toggled = pyqtSignal(bool)
    zoom_in = pyqtSignal()
    zoom_out = pyqtSignal()
    zoom_sifirla = pyqtSignal()
    png_aktar = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame{{background:{RENK_BG_BIRINCIL};
            border-bottom:1px solid {RENK_KENARLIK};}}
        """)
        self.setFixedHeight(44)
        l = QHBoxLayout(self); l.setContentsMargins(10,0,10,0); l.setSpacing(2)

        self._mod_grup = QButtonGroup(self)
        self._mod_grup.setExclusive(True)

        araclar = [
            (MOD_SEC,     "↖",  "Seç (Esc)"),
            (MOD_DIKDORT, "▭",  "Dikdörtgen"),
            (MOD_ELMAS,   "◇",  "Elmas (Karar)"),
            (MOD_OVAL,    "⬭",  "Oval (Baş/Bitiş)"),
            (MOD_METIN,   "T",  "Metin Kutusu"),
            (None,        None, None),  # ayraç
            (MOD_OK,      "→",  "Ok Çiz"),
            (MOD_CIZGI,   "⌐",  "L-Ok Çiz"),
        ]

        for mod, ikon, tooltip in araclar:
            if mod is None:
                sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet(f"color:{RENK_KENARLIK};"); sep.setFixedHeight(24)
                l.addWidget(sep); continue
            btn = QToolButton(); btn.setText(ikon); btn.setToolTip(tooltip)
            btn.setCheckable(True); btn.setFixedSize(34, 32)
            btn.setStyleSheet(f"""
                QToolButton{{border:1px solid transparent;border-radius:5px;
                font-size:14px;color:{RENK_YAZI_BIRINCIL};}}
                QToolButton:hover{{background:{RENK_PRIMARY_ACIK};}}
                QToolButton:checked{{background:{RENK_PRIMARY_ACIK};
                border-color:{RENK_PRIMARY};color:{RENK_PRIMARY};}}
            """)
            if mod == MOD_SEC:
                btn.setChecked(True)
            btn.clicked.connect(lambda _, m=mod: self.mod_degisti.emit(m))
            self._mod_grup.addButton(btn)
            l.addWidget(btn)

        l.addSpacing(8)
        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet(f"color:{RENK_KENARLIK};"); sep2.setFixedHeight(24)
        l.addWidget(sep2); l.addSpacing(8)

        # Geri Al
        btn_geri = QPushButton("↩ Geri Al")
        btn_geri.setFixedHeight(30)
        btn_geri.setStyleSheet(self._btn_stil())
        btn_geri.clicked.connect(self.geri_al)
        l.addWidget(btn_geri)

        # Izgara
        self.btn_izgara = QPushButton("⊞ Izgara")
        self.btn_izgara.setCheckable(True); self.btn_izgara.setChecked(True)
        self.btn_izgara.setFixedHeight(30)
        self.btn_izgara.setStyleSheet(self._btn_stil())
        self.btn_izgara.toggled.connect(self.izgara_toggled)
        l.addWidget(self.btn_izgara)

        l.addStretch()

        # Zoom
        for txt, sig in [("⊖", self.zoom_out), ("⊕", self.zoom_in),
                          ("⊡", self.zoom_sifirla)]:
            b = QPushButton(txt); b.setFixedSize(28, 28)
            b.setStyleSheet(self._btn_stil()); b.clicked.connect(sig)
            l.addWidget(b)

        l.addSpacing(8)
        # PNG Aktar
        btn_png = QPushButton("📷 PNG Aktar")
        btn_png.setFixedHeight(30)
        btn_png.setStyleSheet(f"""
            QPushButton{{border:1px solid {RENK_PRIMARY};border-radius:5px;
            background:{RENK_PRIMARY_ACIK};color:{RENK_PRIMARY};
            font-size:11px;padding:0 10px;}}
            QPushButton:hover{{background:{RENK_PRIMARY};color:white;}}
        """)
        btn_png.clicked.connect(self.png_aktar)
        l.addWidget(btn_png)

    def _btn_stil(self):
        return f"""
            QPushButton{{border:1px solid {RENK_KENARLIK};border-radius:5px;
            background:{RENK_BG_IKINCIL};color:{RENK_YAZI_BIRINCIL};
            font-size:11px;padding:0 8px;}}
            QPushButton:hover{{background:{RENK_PRIMARY_ACIK};
            color:{RENK_PRIMARY};}}
            QPushButton:checked{{background:{RENK_PRIMARY_ACIK};
            border-color:{RENK_PRIMARY};color:{RENK_PRIMARY};}}
        """


# ─── Sol Palet ────────────────────────────────────────────────────────────────

class SolPalet(QFrame):
    sekil_ekle = pyqtSignal(str)  # mod

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(70)
        self.setStyleSheet(f"""
            QFrame{{background:{RENK_BG_BIRINCIL};
            border-right:1px solid {RENK_KENARLIK};}}
        """)
        l = QVBoxLayout(self); l.setContentsMargins(5,10,5,10); l.setSpacing(4)

        sekiller = [
            (MOD_DIKDORT, "▭", "İşlem"),
            (MOD_ELMAS,   "◇", "Karar"),
            (MOD_OVAL,    "⬭", "Baş/Bitiş"),
            (MOD_METIN,   "T", "Metin"),
        ]
        oklar = [
            (MOD_OK,    "→", "Düz Ok"),
            (MOD_CIZGI, "⌐", "L-Ok"),
        ]

        self._sec_label("Şekil", l)
        for mod, ikon, ad in sekiller:
            l.addWidget(self._palet_btn(mod, ikon, ad))

        self._sec_label("Ok", l)
        for mod, ikon, ad in oklar:
            l.addWidget(self._palet_btn(mod, ikon, ad))

        l.addStretch()

    def _sec_label(self, txt, layout):
        lbl = QLabel(txt)
        lbl.setStyleSheet(
            f"font-size:8px;color:{RENK_YAZI_UCUNCUL};"
            f"text-transform:uppercase;letter-spacing:0.5px;"
            f"padding:4px 0 2px 2px;")
        layout.addWidget(lbl)

    def _palet_btn(self, mod, ikon, ad):
        btn = QPushButton()
        btn.setFixedSize(58, 50)
        btn.setToolTip(ad)
        btn.setStyleSheet(f"""
            QPushButton{{
                border:1px solid {RENK_KENARLIK};border-radius:6px;
                background:{RENK_BG_IKINCIL};
                font-size:18px;color:{RENK_YAZI_BIRINCIL};
            }}
            QPushButton:hover{{
                background:{RENK_PRIMARY_ACIK};
                border-color:{RENK_PRIMARY};
                color:{RENK_PRIMARY};
            }}
        """)
        # İkon + metin
        from PyQt6.QtWidgets import QVBoxLayout as QVL
        inner = QWidget(btn)
        il = QVL(inner); il.setContentsMargins(0,4,0,4); il.setSpacing(1)
        lbl_i = QLabel(ikon); lbl_i.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_i.setStyleSheet("font-size:16px;border:none;background:transparent;")
        lbl_t = QLabel(ad); lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_t.setStyleSheet(f"font-size:8px;border:none;background:transparent;color:{RENK_YAZI_IKINCIL};")
        il.addWidget(lbl_i); il.addWidget(lbl_t)
        inner.setGeometry(0, 0, 58, 50)
        btn.clicked.connect(lambda: self.sekil_ekle.emit(mod))
        return btn


# ─── Ana Editör Dialog ────────────────────────────────────────────────────────

class AkisEditoruDialog(QDialog):
    """Tam ekran akış şeması editörü."""
    kaydedildi = pyqtSignal(dict)  # {sekiller, oklar}

    def __init__(self, data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Proses Akış Şeması Editörü")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)

        # Başlık
        baslik_f = QFrame()
        baslik_f.setStyleSheet(
            f"background:{RENK_PRIMARY};border-bottom:1px solid {RENK_PRIMARY_KOYU};")
        baslik_f.setFixedHeight(40)
        bl = QHBoxLayout(baslik_f); bl.setContentsMargins(14,0,14,0)
        lbl = QLabel("Proses Akış Şeması Editörü")
        lbl.setStyleSheet("font-size:13px;font-weight:bold;color:white;")
        bl.addWidget(lbl); bl.addStretch()
        ipucu = QLabel("Çift tıkla: metin düzenle  ·  Del: sil  ·  Ctrl+D: çoğalt  ·  Ctrl+Z: geri al  ·  Tekerlek: zoom")
        ipucu.setStyleSheet("font-size:10px;color:rgba(255,255,255,180);")
        bl.addWidget(ipucu)
        layout.addWidget(baslik_f)

        # Araç çubuğu
        self._arac = AracCubugu()
        layout.addWidget(self._arac)

        # İçerik
        icerik = QHBoxLayout(); icerik.setContentsMargins(0,0,0,0); icerik.setSpacing(0)

        # Sol palet
        self._palet = SolPalet()
        icerik.addWidget(self._palet)

        # Sahne + Canvas
        self._sahne = AkisSahne()
        self._canvas = AkisCanvas(self._sahne)
        icerik.addWidget(self._canvas, 1)

        # Sağ panel
        panel_frame = QFrame()
        panel_frame.setStyleSheet(
            f"border-left:1px solid {RENK_KENARLIK};background:{RENK_BG_BIRINCIL};")
        pfl = QVBoxLayout(panel_frame); pfl.setContentsMargins(0,0,0,0)
        self._ozellikler = OzelliklerPaneli()
        pfl.addWidget(self._ozellikler)
        icerik.addWidget(panel_frame)

        icerik_w = QWidget(); icerik_w.setLayout(icerik)
        layout.addWidget(icerik_w, 1)

        # Alt bar
        alt = QFrame()
        alt.setStyleSheet(
            f"background:{RENK_BG_IKINCIL};border-top:1px solid {RENK_KENARLIK};")
        alt.setFixedHeight(34)
        al = QHBoxLayout(alt); al.setContentsMargins(12,0,12,0); al.setSpacing(12)

        self.lbl_durum = QLabel("Hazır")
        self.lbl_durum.setStyleSheet(
            f"font-size:10px;color:{RENK_YAZI_UCUNCUL};")
        al.addWidget(self.lbl_durum); al.addStretch()

        btn_iptal = QPushButton("İptal")
        btn_iptal.setFixedHeight(26)
        btn_iptal.setStyleSheet(f"""
            QPushButton{{border:1px solid {RENK_KENARLIK};border-radius:5px;
            background:{RENK_BG_IKINCIL};color:{RENK_YAZI_BIRINCIL};
            font-size:11px;padding:0 14px;}}
            QPushButton:hover{{background:#FCEBEB;color:#A32D2D;}}
        """)
        btn_iptal.clicked.connect(self.reject)
        al.addWidget(btn_iptal)

        btn_kaydet = QPushButton("💾  Kaydet ve Kapat")
        btn_kaydet.setFixedHeight(26)
        btn_kaydet.setStyleSheet(f"""
            QPushButton{{border:none;border-radius:5px;
            background:{RENK_PRIMARY};color:white;
            font-size:11px;font-weight:bold;padding:0 16px;}}
            QPushButton:hover{{background:{RENK_PRIMARY_KOYU};}}
        """)
        btn_kaydet.clicked.connect(self._kaydet)
        al.addWidget(btn_kaydet)
        layout.addWidget(alt)

        # Bağlantılar
        self._arac.mod_degisti.connect(self._canvas.set_mod)
        self._arac.geri_al.connect(self._sahne.geri_al)
        self._arac.izgara_toggled.connect(self._izgara_toggle)
        self._arac.zoom_in.connect(lambda: self._canvas.scale(1.2, 1.2))
        self._arac.zoom_out.connect(lambda: self._canvas.scale(0.83, 0.83))
        self._arac.zoom_sifirla.connect(lambda: self._canvas.fitInView(
            QRectF(0,0,CANVAS_W,CANVAS_H), Qt.AspectRatioMode.KeepAspectRatio))
        self._arac.png_aktar.connect(self._png_aktar)
        self._palet.sekil_ekle.connect(self._canvas.set_mod)
        self._sahne.degisti.connect(
            lambda: self.lbl_durum.setText("● Kaydedilmemiş değişiklik"))
        self._sahne.sekil_secildi.connect(self._ozellikler.yukle)
        self._ozellikler.degisti.connect(self._ozellik_degisti)

        if data:
            self._sahne.yukle(data)

    def _izgara_toggle(self, aktif: bool):
        self._sahne._izgara_aktif = aktif
        self._sahne.update()

    def _ozellik_degisti(self, veri: SekliVeri):
        sid = veri.id
        if sid in self._sahne._sekil_items:
            item = self._sahne._sekil_items[sid]
            item.setPos(veri.x, veri.y)
            item.prepareGeometryChange()
            item.update()
        self._sahne.degisti.emit()

    def _png_aktar(self):
        dosya, _ = QFileDialog.getSaveFileName(
            self, "PNG Olarak Kaydet", "akis_semasi.png",
            "PNG (*.png)")
        if dosya:
            self._sahne.png_kaydet(dosya, dpi=200)
            QMessageBox.information(self, "Kaydedildi",
                                    f"Akış şeması kaydedildi:\n{dosya}")

    def _kaydet(self):
        data = self._sahne.to_data()
        self.kaydedildi.emit(data)
        self.accept()

    def get_data(self) -> dict:
        return self._sahne.to_data()

    def png_binary(self, dpi: int = 200) -> bytes:
        return self._sahne.png_render(dpi)


# ─── Küçük Önizleme Widget (Ana Pencere için) ─────────────────────────────────

class AkisEditoruWidget(QWidget):
    """
    Ana pencereye gömülen küçük panel.
    'Editörü Aç' butonu ile tam ekran QDialog açılır.
    """
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict = {"sekiller": [], "oklar": []}
        self._setup_ui()

    def _setup_ui(self):
        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(0)

        # Toolbar
        tb = QFrame()
        tb.setStyleSheet(
            f"background:{RENK_BG_BIRINCIL};border-bottom:1px solid {RENK_KENARLIK};")
        tb.setFixedHeight(46)
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(16,0,16,0); tbl.setSpacing(8)
        lbl = QLabel("Proses Akış Şeması")
        lbl.setStyleSheet(
            f"font-size:13px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        tbl.addWidget(lbl); tbl.addStretch()

        self.lbl_durum = QLabel("Henüz çizilmedi")
        self.lbl_durum.setStyleSheet(
            f"font-size:11px;color:{RENK_YAZI_UCUNCUL};")
        tbl.addWidget(self.lbl_durum)

        btn_ac = QPushButton("✏️  Editörü Aç")
        btn_ac.setFixedHeight(30)
        btn_ac.setStyleSheet(f"""
            QPushButton{{background:{RENK_PRIMARY};color:white;border:none;
            border-radius:6px;font-size:12px;font-weight:bold;
            padding:0 14px;}}
            QPushButton:hover{{background:{RENK_PRIMARY_KOYU};}}
        """)
        btn_ac.clicked.connect(self._editor_ac)
        tbl.addWidget(btn_ac)
        l.addWidget(tb)

        # Önizleme
        self._onizleme = QLabel()
        self._onizleme.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._onizleme.setStyleSheet(
            f"background:#F8F9FA;border:1px dashed {RENK_KENARLIK};")
        self._onizleme.setMinimumHeight(300)
        self._onizleme.setText("Akış şeması henüz oluşturulmadı.\n'Editörü Aç' butonu ile başlayın.")
        self._onizleme.setStyleSheet(f"""
            background:#F8F9FA;border:1px dashed {RENK_KENARLIK};
            color:{RENK_YAZI_UCUNCUL};font-size:12px;
        """)
        l.addWidget(self._onizleme, 1)

    def _editor_ac(self):
        dlg = AkisEditoruDialog(
            data=self._data if self._data["sekiller"] else None,
            parent=self)
        dlg.kaydedildi.connect(self._kayit_al)
        dlg.exec()

    def _kayit_al(self, data: dict):
        self._data = data
        # Önizleme güncelle
        n_sekil = len(data.get("sekiller", []))
        n_ok = len(data.get("oklar", []))
        if n_sekil > 0:
            self.lbl_durum.setText(
                f"{n_sekil} şekil, {n_ok} ok")
            self.lbl_durum.setStyleSheet(
                f"font-size:11px;color:{RENK_PRIMARY};font-weight:bold;")
            # Küçük önizleme render
            self._onizleme_guncelle(data)
        self.degisti.emit()

    def _onizleme_guncelle(self, data: dict):
        """Küçük önizleme PNG'si."""
        try:
            # Geçici sahne oluştur
            gecici = AkisSahne()
            gecici._izgara_aktif = False
            gecici.yukle(data)
            png = gecici.png_render(dpi=60)
            pix = QPixmap()
            pix.loadFromData(png)
            self._onizleme.setPixmap(
                pix.scaledToWidth(
                    min(self._onizleme.width() - 20,
                        pix.width()),
                    Qt.TransformationMode.SmoothTransformation))
        except Exception:
            pass

    def yukle(self, data: dict):
        self._data = data
        if data and data.get("sekiller"):
            n = len(data["sekiller"])
            self.lbl_durum.setText(f"{n} şekil")
            self._onizleme_guncelle(data)

    def to_data(self) -> dict:
        return self._data

    def png_binary(self, dpi: int = 200) -> bytes:
        """Word çıktısı için PNG binary döner."""
        sahne = AkisSahne()
        sahne._izgara_aktif = False
        sahne.yukle(self._data)
        return sahne.png_render(dpi)
