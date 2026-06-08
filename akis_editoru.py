"""
PV-DOC — Proses Akış Şeması Editörü
4 sütun kılavuzlu serbest canvas
Sütunlar: Başlangıç Maddeleri | Proses Adımı | IPK Testleri | Rutin/Val. Testleri
"""

import math
import uuid
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QLineEdit, QPushButton, QGraphicsView, QGraphicsScene,
    QGraphicsItem, QGraphicsRectItem, QGraphicsPathItem,
    QSizePolicy, QToolButton, QButtonGroup, QComboBox, QSpinBox,
    QTextEdit, QInputDialog, QApplication, QMessageBox,
    QFileDialog, QScrollArea, QGraphicsEllipseItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QSizeF
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QFont, QPainter, QPolygonF,
    QPainterPath, QImage, QPixmap, QKeySequence, QCursor
)
from ui.stiller import (
    RENK_PRIMARY, RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU,
    RENK_BG_BIRINCIL, RENK_BG_IKINCIL, RENK_KENARLIK,
    RENK_YAZI_BIRINCIL, RENK_YAZI_IKINCIL, RENK_YAZI_UCUNCUL,
    FONT_AILESI
)

# ─── Sabitler ─────────────────────────────────────────────────────────────────
CANVAS_W = 1400
CANVAS_H = 1000
IZGARA = 20
SUTUN_ORANLARI = [0.0, 0.22, 0.50, 0.72, 1.0]
SUTUN_ADLARI = [
    "Başlangıç Maddeleri",
    "Proses Adımı",
    "IPK Testleri",
    "Rutin / Val. Testleri",
]
MOD_SEC     = "sec"
MOD_DKRT    = "dikdortgen"
MOD_ELMAS   = "elmas"
MOD_OVAL    = "oval"
MOD_METIN   = "metin"
MOD_OK      = "ok"
MOD_LOK     = "lok"

KENAR_RENKLERI = {
    "Siyah":   "#1A1A1A",
    "Mavi":    "#1a5fa5",
    "Yeşil":   "#2e7d32",
    "Turuncu": "#e65100",
    "Kırmızı": "#b71c1c",
    "Gri":     "#607d8b",
}
KENAR_STILLERI = {
    "Düz":   Qt.PenStyle.SolidLine,
    "Kesik": Qt.PenStyle.DashLine,
    "Nokta": Qt.PenStyle.DotLine,
}
TUTAMAC = 8  # tutamaç boyutu px

# ─── Veri ─────────────────────────────────────────────────────────────────────
class SekliVeri:
    def __init__(self, tip="dikdortgen", metin="",
                 x=100.0, y=100.0, w=160.0, h=52.0,
                 kenar_renk="#1A1A1A", kenar_stil="Düz",
                 yazi_boyut=11, yatay="orta", dikey="orta",
                 sid=None):
        self.id = sid or str(uuid.uuid4())[:8]
        self.tip = tip; self.metin = metin
        self.x = x; self.y = y; self.w = w; self.h = h
        self.kenar_renk = kenar_renk; self.kenar_stil = kenar_stil
        self.yazi_boyut = yazi_boyut
        self.yatay = yatay; self.dikey = dikey

    def to_dict(self): return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d):
        s = cls(); s.__dict__.update(d); return s

    def kopya(self):
        d = self.to_dict(); d["id"] = str(uuid.uuid4())[:8]
        return SekliVeri.from_dict(d)


class OkVeri:
    def __init__(self, x1=0.0, y1=0.0, x2=0.0, y2=0.0,
                 tip="ok", oid=None):
        self.id = oid or str(uuid.uuid4())[:8]
        self.x1 = x1; self.y1 = y1; self.x2 = x2; self.y2 = y2
        self.tip = tip  # "ok" düz dik, "lok" L-şekilli

    def to_dict(self): return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d):
        o = cls(); o.__dict__.update(d); return o


# ─── Tutamaç ──────────────────────────────────────────────────────────────────
class Tutamac(QGraphicsRectItem):
    def __init__(self, yon: str, sekil_item):
        super().__init__(-TUTAMAC/2, -TUTAMAC/2, TUTAMAC, TUTAMAC)
        self.yon = yon
        self.sekil_item = sekil_item
        self.setBrush(QBrush(QColor("#1a5fa5")))
        self.setPen(QPen(QColor("white"), 1.5))
        self.setZValue(100)
        self.setParentItem(sekil_item)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresParentOpacity, True)
        cursor_map = {
            "tl": Qt.CursorShape.SizeFDiagCursor,
            "tr": Qt.CursorShape.SizeBDiagCursor,
            "bl": Qt.CursorShape.SizeBDiagCursor,
            "br": Qt.CursorShape.SizeFDiagCursor,
            "t":  Qt.CursorShape.SizeVerCursor,
            "b":  Qt.CursorShape.SizeVerCursor,
            "l":  Qt.CursorShape.SizeHorCursor,
            "r":  Qt.CursorShape.SizeHorCursor,
        }
        self.setCursor(cursor_map.get(yon, Qt.CursorShape.SizeAllCursor))
        self.setVisible(False)

    def pozisyon_guncelle(self):
        v = self.sekil_item.veri
        w, h = v.w, v.h
        poz = {
            "tl": QPointF(0, 0),   "t": QPointF(w/2, 0),   "tr": QPointF(w, 0),
            "l":  QPointF(0, h/2),                           "r":  QPointF(w, h/2),
            "bl": QPointF(0, h),   "b": QPointF(w/2, h),   "br": QPointF(w, h),
        }
        self.setPos(poz[self.yon])


# ─── Şekil Item ────────────────────────────────────────────────────────────────
class SekliItem(QGraphicsItem):
    def __init__(self, veri: SekliVeri, sahne: 'AkisSahne'):
        super().__init__()
        self.veri = veri
        self.sahne = sahne
        self._tutamaclar: dict[str, Tutamac] = {}
        self._yb_yon = None          # yeniden boyutlandırma yönü
        self._yb_bas = None          # başlangıç mouse pozisyonu (sahne)
        self._yb_orijinal = None     # başlangıçtaki (x,y,w,h)

        self.setPos(veri.x, veri.y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

        for yon in ("tl","t","tr","l","r","bl","b","br"):
            t = Tutamac(yon, self)
            self._tutamaclar[yon] = t

    def boundingRect(self):
        return QRectF(0, 0, self.veri.w, self.veri.h)

    def _pen(self):
        stil = KENAR_STILLERI.get(self.veri.kenar_stil, Qt.PenStyle.SolidLine)
        w = 2.5 if self.isSelected() else 1.5
        renk = RENK_PRIMARY if self.isSelected() else self.veri.kenar_renk
        return QPen(QColor(renk), w, stil)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self._pen())
        painter.setBrush(QBrush(QColor("white")))
        w, h = self.veri.w, self.veri.h

        if self.veri.tip in ("dikdortgen", "metin"):
            painter.drawRoundedRect(QRectF(0, 0, w, h), 6, 6)
        elif self.veri.tip == "elmas":
            poly = QPolygonF([QPointF(w/2,0), QPointF(w,h/2),
                               QPointF(w/2,h), QPointF(0,h/2)])
            painter.drawPolygon(poly)
        elif self.veri.tip == "oval":
            painter.drawEllipse(QRectF(0, 0, w, h))

        # Metin
        painter.setPen(QPen(QColor(self.veri.kenar_renk)))
        font = QFont(FONT_AILESI, self.veri.yazi_boyut)
        painter.setFont(font)
        yatay_flag = {"sol": Qt.AlignmentFlag.AlignLeft,
                      "orta": Qt.AlignmentFlag.AlignHCenter,
                      "sag": Qt.AlignmentFlag.AlignRight
                      }.get(self.veri.yatay, Qt.AlignmentFlag.AlignHCenter)
        dikey_flag = {"ust": Qt.AlignmentFlag.AlignTop,
                      "orta": Qt.AlignmentFlag.AlignVCenter,
                      "alt": Qt.AlignmentFlag.AlignBottom
                      }.get(self.veri.dikey, Qt.AlignmentFlag.AlignVCenter)
        painter.drawText(QRectF(6, 4, w-12, h-8),
                         yatay_flag | dikey_flag | Qt.TextFlag.TextWordWrap,
                         self.veri.metin)

    def _tutamac_guncelle(self):
        for t in self._tutamaclar.values():
            t.pozisyon_guncelle()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            goster = bool(value)
            for t in self._tutamaclar.values():
                t.setVisible(goster)
            if goster:
                self._tutamac_guncelle()
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.veri.x = self.pos().x()
            self.veri.y = self.pos().y()
            self.sahne.okları_guncelle()
            self.sahne.degisti.emit()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event); return

        # Tutamaca tıklandı mı? (scene koordinatında kontrol)
        scene_pos = event.scenePos()
        for yon, t in self._tutamaclar.items():
            if not t.isVisible(): continue
            t_scene = t.mapToScene(t.boundingRect().center())
            if (scene_pos - t_scene).manhattanLength() < TUTAMAC + 4:
                self._yb_yon = yon
                self._yb_bas = scene_pos
                self._yb_orijinal = (self.veri.x, self.veri.y,
                                     self.veri.w, self.veri.h)
                event.accept()
                return

        self._yb_yon = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._yb_yon is not None:
            delta = event.scenePos() - self._yb_bas
            ox, oy, ow, oh = self._yb_orijinal
            yon = self._yb_yon
            MIN_W, MIN_H = 40, 24
            nx, ny, nw, nh = ox, oy, ow, oh

            if "r" in yon: nw = max(MIN_W, ow + delta.x())
            if "b" in yon: nh = max(MIN_H, oh + delta.y())
            if "l" in yon:
                d = min(ow - MIN_W, delta.x())
                nx = ox + d; nw = ow - d
            if "t" in yon:
                d = min(oh - MIN_H, delta.y())
                ny = oy + d; nh = oh - d

            self.prepareGeometryChange()
            self.veri.x = nx; self.veri.y = ny
            self.veri.w = nw; self.veri.h = nh
            self.setPos(nx, ny)
            self._tutamac_guncelle()
            self.sahne.okları_guncelle()
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._yb_yon is not None:
            self._yb_yon = None
            self.sahne.degisti.emit()
            event.accept(); return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        metin, ok = QInputDialog.getMultiLineText(
            None, "Metni Düzenle", "Metin:", self.veri.metin)
        if ok:
            self.veri.metin = metin
            self.update()
            self.sahne.degisti.emit()


# ─── Ok Item ──────────────────────────────────────────────────────────────────
class OkItem(QGraphicsItem):
    def __init__(self, veri: OkVeri):
        super().__init__()
        self.veri = veri
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setZValue(-1)

    def _noktalar(self):
        """Ok çizgi noktalarını döner [(x,y), ...]"""
        x1, y1, x2, y2 = self.veri.x1, self.veri.y1, self.veri.x2, self.veri.y2
        if self.veri.tip == "lok":
            return [(x1, y1), (x2, y1), (x2, y2)]
        else:
            # Düz dik ok: en büyük eksen
            if abs(x2 - x1) >= abs(y2 - y1):
                return [(x1, y1), (x2, y1)]   # yatay
            else:
                return [(x1, y1), (x1, y2)]   # dikey

    def boundingRect(self):
        pts = self._noktalar()
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        margin = 12
        return QRectF(min(xs)-margin, min(ys)-margin,
                      max(xs)-min(xs)+margin*2,
                      max(ys)-min(ys)+margin*2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renk = RENK_PRIMARY if self.isSelected() else "#455A64"
        pen = QPen(QColor(renk), 1.8)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        pts = self._noktalar()
        # Çizgi
        for i in range(len(pts)-1):
            painter.drawLine(int(pts[i][0]), int(pts[i][1]),
                             int(pts[i+1][0]), int(pts[i+1][1]))

        # Ok başı (son noktaya)
        if len(pts) >= 2:
            ex, ey = pts[-1]
            px, py = pts[-2]
            dx = ex - px; dy = ey - py
            uzun = math.sqrt(dx*dx + dy*dy)
            if uzun > 0:
                ux = dx/uzun; uy = dy/uzun
                # Kapalı üçgen sadece ok başı
                ok_path = QPainterPath()
                ok_path.moveTo(ex, ey)
                ok_path.lineTo(ex - 11*ux - 5*uy,
                               ey - 11*uy + 5*ux)
                ok_path.lineTo(ex - 11*ux + 5*uy,
                               ey - 11*uy - 5*ux)
                ok_path.closeSubpath()
                painter.setBrush(QBrush(QColor(renk)))
                painter.drawPath(ok_path)

    def guncelle(self): self.update()


# ─── Sahne ────────────────────────────────────────────────────────────────────
class AkisSahne(QGraphicsScene):
    degisti = pyqtSignal()
    sekil_secildi = pyqtSignal(object)   # SekliVeri | None
    mod_otomatik_sec = pyqtSignal()

    def __init__(self):
        super().__init__(0, 0, CANVAS_W, CANVAS_H)
        self._mod = MOD_SEC
        self._sekil_items: dict[str, SekliItem] = {}
        self._ok_items: dict[str, OkItem] = {}
        self._sekil_verileri: list[SekliVeri] = []
        self._ok_verileri: list[OkVeri] = []
        self._geri_al: list = []
        self._ok_bas: QPointF | None = None
        self._gecici = None
        self._izgara = True
        self._pano: list[SekliVeri] = []   # kopyala/kes panosu
        self._kes_modda = False
        self.selectionChanged.connect(self._secim_degisti)

    # ── Arka plan ─────────────────────────────────────────────────────────────
    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor("#F8F9FA"))
        if self._izgara:
            painter.setPen(QPen(QColor("#E0E4E8"), 0.5))
            sol = int(rect.left()) - (int(rect.left()) % IZGARA)
            ust = int(rect.top())  - (int(rect.top())  % IZGARA)
            x = sol
            while x <= rect.right():
                painter.drawLine(x, int(rect.top()), x, int(rect.bottom())); x += IZGARA
            y = ust
            while y <= rect.bottom():
                painter.drawLine(int(rect.left()), y, int(rect.right()), y); y += IZGARA

        # Sütun kılavuzları
        for oran in SUTUN_ORANLARI[1:-1]:
            x = int(CANVAS_W * oran)
            painter.setPen(QPen(QColor("#B5C8E0"), 1.2, Qt.PenStyle.DashLine))
            painter.drawLine(x, 0, x, CANVAS_H)

        # Sütun başlıkları
        for i in range(4):
            x1 = int(CANVAS_W * SUTUN_ORANLARI[i])
            x2 = int(CANVAS_W * SUTUN_ORANLARI[i+1])
            painter.setPen(QPen(QColor("#7B9EC4")))
            f = QFont(FONT_AILESI, 9); f.setBold(True); painter.setFont(f)
            painter.drawText(QRectF(x1+4, 4, x2-x1-8, 22),
                             Qt.AlignmentFlag.AlignCenter, SUTUN_ADLARI[i])

    # ── Mod ───────────────────────────────────────────────────────────────────
    def set_mod(self, mod: str):
        self._mod = mod

    # ── Mouse ─────────────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event); return
        pos = event.scenePos()

        if self._mod == MOD_SEC:
            super().mousePressEvent(event); return

        if self._mod in (MOD_OK, MOD_LOK):
            self._ok_bas = pos
            from PyQt6.QtWidgets import QGraphicsLineItem
            self._gecici = QGraphicsLineItem(
                pos.x(), pos.y(), pos.x(), pos.y())
            self._gecici.setPen(QPen(QColor("#455A64"), 1.5,
                                     Qt.PenStyle.DashLine))
            self.addItem(self._gecici)
            return

        # Şekil ekle
        tip_map = {MOD_DKRT:  ("dikdortgen", 160, 52),
                   MOD_ELMAS: ("elmas",      140, 72),
                   MOD_OVAL:  ("oval",       130, 46),
                   MOD_METIN: ("metin",      160, 46)}
        if self._mod in tip_map:
            tip, w, h = tip_map[self._mod]
            x = round((pos.x()-w/2) / IZGARA) * IZGARA
            y = round((pos.y()-h/2) / IZGARA) * IZGARA
            self._durum_kaydet()
            v = SekliVeri(tip=tip, metin="Metin", x=x, y=y, w=w, h=h)
            self._sekil_ekle(v)
            self.clearSelection()
            self._sekil_items[v.id].setSelected(True)
            self._mod = MOD_SEC
            self.mod_otomatik_sec.emit()
            self.degisti.emit()

    def mouseMoveEvent(self, event):
        if self._gecici and self._ok_bas:
            p = event.scenePos()
            self._gecici.setLine(self._ok_bas.x(), self._ok_bas.y(),
                                 p.x(), p.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if (self._gecici and self._ok_bas and
                event.button() == Qt.MouseButton.LeftButton):
            bitis = event.scenePos()
            self.removeItem(self._gecici); self._gecici = None
            self._durum_kaydet()
            ok = OkVeri(x1=self._ok_bas.x(), y1=self._ok_bas.y(),
                        x2=bitis.x(), y2=bitis.y(),
                        tip="lok" if self._mod == MOD_LOK else "ok")
            self._ok_ekle(ok)
            self._ok_bas = None
            self.degisti.emit()
            return
        super().mouseReleaseEvent(event)

    # ── Öğe yönetimi ──────────────────────────────────────────────────────────
    def _sekil_ekle(self, v: SekliVeri):
        self._sekil_verileri.append(v)
        item = SekliItem(v, self)
        self.addItem(item)
        self._sekil_items[v.id] = item

    def _ok_ekle(self, v: OkVeri):
        self._ok_verileri.append(v)
        item = OkItem(v)
        self.addItem(item)
        self._ok_items[v.id] = item

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
        for item in list(self.selectedItems()):
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

    def kopyala(self):
        self._pano = [item.veri.kopya()
                      for item in self.selectedItems()
                      if isinstance(item, SekliItem)]
        self._kes_modda = False

    def kes(self):
        self._pano = [item.veri.kopya()
                      for item in self.selectedItems()
                      if isinstance(item, SekliItem)]
        self._kes_modda = True
        self.secili_sil()

    def yapistir(self):
        if not self._pano: return
        self._durum_kaydet()
        self.clearSelection()
        for v in self._pano:
            yeni = v.kopya()
            yeni.x += 20; yeni.y += 20
            self._sekil_ekle(yeni)
            self._sekil_items[yeni.id].setSelected(True)
        # Panoyu güncelle — bir sonraki yapıştırma için offset
        for v in self._pano:
            v.x += 20; v.y += 20
        self.degisti.emit()

    # ── Geri Al ───────────────────────────────────────────────────────────────
    def _durum_kaydet(self):
        d = {"sekiller": [s.to_dict() for s in self._sekil_verileri],
             "oklar":    [o.to_dict() for o in self._ok_verileri]}
        self._geri_al.append(d)
        if len(self._geri_al) > 50: self._geri_al.pop(0)

    def geri_al(self):
        if not self._geri_al: return
        self._yukle_durum(self._geri_al.pop())

    def _yukle_durum(self, d: dict):
        for item in list(self._sekil_items.values()): self.removeItem(item)
        for item in list(self._ok_items.values()):    self.removeItem(item)
        self._sekil_items.clear(); self._ok_items.clear()
        self._sekil_verileri.clear(); self._ok_verileri.clear()
        for sd in d["sekiller"]: self._sekil_ekle(SekliVeri.from_dict(sd))
        for od in d["oklar"]:    self._ok_ekle(OkVeri.from_dict(od))
        self.degisti.emit()

    # ── Serialize ─────────────────────────────────────────────────────────────
    def to_data(self):
        return {"sekiller": [s.to_dict() for s in self._sekil_verileri],
                "oklar":    [o.to_dict() for o in self._ok_verileri]}

    def yukle(self, d: dict):
        self._yukle_durum(d)

    def temizle(self):
        self._yukle_durum({"sekiller": [], "oklar": []})

    # ── PNG ───────────────────────────────────────────────────────────────────
    def png_render(self, dpi=200) -> bytes:
        import tempfile, os
        # Tüm item'ların bounding rect'ini hesapla
        rects = [item.mapToScene(item.boundingRect()).boundingRect()
                 for item in self.items()
                 if not isinstance(item, type(None))]
        if rects:
            min_x = min(r.left()   for r in rects)
            min_y = min(r.top()    for r in rects)
            max_x = max(r.right()  for r in rects)
            max_y = max(r.bottom() for r in rects)
            src = QRectF(min_x-20, min_y-20, max_x-min_x+40, max_y-min_y+40)
            src = src.intersected(QRectF(0, 0, CANVAS_W, CANVAS_H))
        else:
            src = QRectF(0, 0, CANVAS_W, CANVAS_H)

        sc = dpi / 96.0
        img = QImage(int(src.width()*sc), int(src.height()*sc),
                     QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.white)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(sc, sc)
        self.render(p, source=src)
        p.end()
        tmp = tempfile.mktemp(suffix=".png")
        img.save(tmp)
        with open(tmp, "rb") as f: data = f.read()
        os.unlink(tmp)
        return data

    def png_kaydet(self, dosya: str, dpi=200):
        with open(dosya, "wb") as f: f.write(self.png_render(dpi))


# ─── Canvas View ──────────────────────────────────────────────────────────────
class AkisCanvas(QGraphicsView):
    def __init__(self, sahne: AkisSahne, parent=None):
        super().__init__(sahne, parent)
        self._sahne = sahne
        self._pan_son = None
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("background:#F8F9FA;border:none;")
        self.fitInView(QRectF(0, 0, CANVAS_W, CANVAS_H),
                       Qt.AspectRatioMode.KeepAspectRatio)

    def set_mod(self, mod: str):
        self._sahne.set_mod(mod)
        if mod == MOD_SEC:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)

    def wheelEvent(self, event):
        f = 1.15 if event.angleDelta().y() > 0 else 0.87
        self.scale(f, f)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_son = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept(); return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan_son is not None:
            d = event.pos() - self._pan_son
            self._pan_son = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - d.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - d.y())
            event.accept(); return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_son = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept(); return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        s = self._sahne
        key = event.key()
        ctrl = event.modifiers() == Qt.KeyboardModifier.ControlModifier
        if key == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept(); return
        if key == Qt.Key.Key_Delete or key == Qt.Key.Key_Backspace:
            s.secili_sil(); return
        if ctrl and key == Qt.Key.Key_Z: s.geri_al(); return
        if ctrl and key == Qt.Key.Key_C: s.kopyala(); return
        if ctrl and key == Qt.Key.Key_X: s.kes(); return
        if ctrl and key == Qt.Key.Key_V: s.yapistir(); return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            mod = self._sahne._mod
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag
                             if mod == MOD_SEC else
                             QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().keyReleaseEvent(event)


# ─── Özellikler Paneli ────────────────────────────────────────────────────────
class OzelliklerPaneli(QWidget):
    degisti   = pyqtSignal(object)   # SekliVeri
    sil_iste  = pyqtSignal()
    kopyala   = pyqtSignal()
    kes       = pyqtSignal()
    yapistir  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._v: SekliVeri | None = None
        self._gun = False
        self.setFixedWidth(215)
        l = QVBoxLayout(self); l.setContentsMargins(10,10,10,10); l.setSpacing(7)

        lbl = QLabel("Özellikler")
        lbl.setStyleSheet(f"font-size:12px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        l.addWidget(lbl)

        self.lbl_bos = QLabel("Şekil seçilmedi")
        self.lbl_bos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_bos.setStyleSheet(f"font-size:11px;color:{RENK_YAZI_UCUNCUL};padding:24px 0;")
        l.addWidget(self.lbl_bos)

        self.pnl = QWidget(); pl = QVBoxLayout(self.pnl)
        pl.setContentsMargins(0,0,0,0); pl.setSpacing(6)

        # Metin
        pl.addWidget(self._lbl("Metin"))
        self.txt = QTextEdit(); self.txt.setMaximumHeight(68)
        self.txt.setStyleSheet(self._inp()); self.txt.textChanged.connect(self._m)
        pl.addWidget(self.txt)

        # Yatay hizalama
        pl.addWidget(self._lbl("Yatay Hizalama"))
        yw = QWidget(); yl = QHBoxLayout(yw); yl.setContentsMargins(0,0,0,0); yl.setSpacing(3)
        self._yg = QButtonGroup(self); self._yg.setExclusive(True)
        for ikon, val, tip in [("◀ Sol","sol","Sola"), ("Orta","orta","Ortala"), ("Sağ ▶","sag","Sağa")]:
            b = QPushButton(ikon); b.setFixedHeight(24); b.setCheckable(True)
            b.setStyleSheet(self._hbtn()); b.setToolTip(tip)
            b.clicked.connect(lambda _,v=val: self._yh(v))
            self._yg.addButton(b); yl.addWidget(b)
            setattr(self, f"by_{val}", b)
        pl.addWidget(yw)

        # Dikey hizalama
        pl.addWidget(self._lbl("Dikey Hizalama"))
        dw = QWidget(); dl = QHBoxLayout(dw); dl.setContentsMargins(0,0,0,0); dl.setSpacing(3)
        self._dg = QButtonGroup(self); self._dg.setExclusive(True)
        for ikon, val, tip in [("▲ Üst","ust","Üste"), ("Orta","orta","Ortala"), ("Alt ▼","alt","Alta")]:
            b = QPushButton(ikon); b.setFixedHeight(24); b.setCheckable(True)
            b.setStyleSheet(self._hbtn()); b.setToolTip(tip)
            b.clicked.connect(lambda _,v=val: self._dh(v))
            self._dg.addButton(b); dl.addWidget(b)
            setattr(self, f"bd_{val}", b)
        pl.addWidget(dw)

        # Boyut
        pl.addWidget(self._lbl("Genişlik × Yükseklik"))
        bw = QWidget(); bl = QHBoxLayout(bw); bl.setContentsMargins(0,0,0,0); bl.setSpacing(4)
        self.sw = QSpinBox(); self.sw.setRange(20,1200); self.sw.setStyleSheet(self._inp())
        self.sh = QSpinBox(); self.sh.setRange(15,900);  self.sh.setStyleSheet(self._inp())
        self.sw.valueChanged.connect(self._b); self.sh.valueChanged.connect(self._b)
        bl.addWidget(self.sw); bl.addWidget(self.sh); pl.addWidget(bw)

        # Konum
        pl.addWidget(self._lbl("X × Y"))
        kw = QWidget(); kl = QHBoxLayout(kw); kl.setContentsMargins(0,0,0,0); kl.setSpacing(4)
        self.sx = QSpinBox(); self.sx.setRange(0,1400); self.sx.setStyleSheet(self._inp())
        self.sy = QSpinBox(); self.sy.setRange(0,1000); self.sy.setStyleSheet(self._inp())
        self.sx.valueChanged.connect(self._k); self.sy.valueChanged.connect(self._k)
        kl.addWidget(self.sx); kl.addWidget(self.sy); pl.addWidget(kw)

        # Yazı boyutu
        pl.addWidget(self._lbl("Yazı Boyutu"))
        self.syb = QSpinBox(); self.syb.setRange(7,24); self.syb.setStyleSheet(self._inp())
        self.syb.valueChanged.connect(self._yb); pl.addWidget(self.syb)

        # Kenarlık rengi
        pl.addWidget(self._lbl("Kenarlık Rengi"))
        rw = QWidget(); rl = QHBoxLayout(rw); rl.setContentsMargins(0,0,0,0); rl.setSpacing(4)
        self._rbtnlar = {}
        for isim, renk in KENAR_RENKLERI.items():
            b = QPushButton(); b.setFixedSize(22,22); b.setCheckable(True)
            b.setToolTip(isim)
            b.setStyleSheet(f"QPushButton{{background:{renk};border:2px solid transparent;border-radius:11px;}}"
                            f"QPushButton:checked{{border-color:#1a5fa5;}}")
            b.clicked.connect(lambda _,r=renk: self._rc(r))
            rl.addWidget(b); self._rbtnlar[renk] = b
        pl.addWidget(rw)

        # Kenarlık stili
        pl.addWidget(self._lbl("Kenarlık Stili"))
        self.cbs = QComboBox(); self.cbs.addItems(list(KENAR_STILLERI.keys()))
        self.cbs.setStyleSheet(self._inp()); self.cbs.currentTextChanged.connect(self._ks)
        pl.addWidget(self.cbs)

        pl.addSpacing(4)
        # İşlem butonları
        for txt, sig, stil in [
            ("✕  Sil", self.sil_iste,  "background:#FADBD8;color:#C0392B;border:1px solid #F1948A;"),
            ("⧉  Kopyala", self.kopyala, f"background:{RENK_BG_IKINCIL};color:{RENK_YAZI_IKINCIL};border:1px solid {RENK_KENARLIK};"),
            ("✂  Kes",   self.kes,  f"background:{RENK_BG_IKINCIL};color:{RENK_YAZI_IKINCIL};border:1px solid {RENK_KENARLIK};"),
        ]:
            b = QPushButton(txt); b.setStyleSheet(
                f"QPushButton{{{stil}border-radius:5px;font-size:11px;padding:5px;}}"
                f"QPushButton:hover{{opacity:0.8;}}")
            b.clicked.connect(sig); pl.addWidget(b)
        pl.addStretch()

        l.addWidget(self.pnl)
        l.addStretch()
        self.pnl.setVisible(False)

    def _lbl(self, t):
        lb = QLabel(t)
        lb.setStyleSheet(f"font-size:10px;font-weight:bold;color:{RENK_YAZI_IKINCIL};")
        return lb

    def _inp(self): return (f"QSpinBox,QTextEdit,QComboBox{{border:1px solid {RENK_KENARLIK};"
                            f"border-radius:4px;padding:3px 6px;font-size:11px;"
                            f"background:{RENK_BG_BIRINCIL};}}")

    def _hbtn(self): return (f"QPushButton{{border:1px solid {RENK_KENARLIK};border-radius:4px;"
                             f"background:{RENK_BG_IKINCIL};font-size:10px;padding:2px;}}"
                             f"QPushButton:checked{{background:{RENK_PRIMARY_ACIK};"
                             f"border-color:{RENK_PRIMARY};color:{RENK_PRIMARY};font-weight:bold;}}"
                             f"QPushButton:hover{{background:{RENK_PRIMARY_ACIK};}}")

    def yukle(self, v: SekliVeri | None):
        self._v = v
        vis = v is not None
        self.lbl_bos.setVisible(not vis)
        self.pnl.setVisible(vis)
        if not v: return
        self._gun = True
        self.txt.setPlainText(v.metin)
        self.sw.setValue(int(v.w)); self.sh.setValue(int(v.h))
        self.sx.setValue(int(v.x)); self.sy.setValue(int(v.y))
        self.syb.setValue(v.yazi_boyut)
        for r, b in self._rbtnlar.items(): b.setChecked(r == v.kenar_renk)
        idx = self.cbs.findText(v.kenar_stil)
        if idx >= 0: self.cbs.setCurrentIndex(idx)
        for val in ("sol","orta","sag"): getattr(self,f"by_{val}").setChecked(val==v.yatay)
        for val in ("ust","orta","alt"): getattr(self,f"bd_{val}").setChecked(val==v.dikey)
        self._gun = False

    def _m(self):
        if self._gun or not self._v: return
        self._v.metin = self.txt.toPlainText(); self.degisti.emit(self._v)
    def _b(self):
        if self._gun or not self._v: return
        self._v.w = self.sw.value(); self._v.h = self.sh.value(); self.degisti.emit(self._v)
    def _k(self):
        if self._gun or not self._v: return
        self._v.x = self.sx.value(); self._v.y = self.sy.value(); self.degisti.emit(self._v)
    def _yb(self):
        if self._gun or not self._v: return
        self._v.yazi_boyut = self.syb.value(); self.degisti.emit(self._v)
    def _yh(self, val):
        if self._gun or not self._v: return
        self._v.yatay = val; self.degisti.emit(self._v)
    def _dh(self, val):
        if self._gun or not self._v: return
        self._v.dikey = val; self.degisti.emit(self._v)
    def _rc(self, renk):
        if self._gun or not self._v: return
        self._v.kenar_renk = renk
        for r,b in self._rbtnlar.items(): b.setChecked(r==renk)
        self.degisti.emit(self._v)
    def _ks(self, stil):
        if self._gun or not self._v: return
        self._v.kenar_stil = stil; self.degisti.emit(self._v)


# ─── Araç Çubuğu ──────────────────────────────────────────────────────────────
class AracCubugu(QFrame):
    mod_degisti   = pyqtSignal(str)
    geri_al_sig   = pyqtSignal()
    izgara_sig    = pyqtSignal(bool)
    zoom_in_sig   = pyqtSignal()
    zoom_out_sig  = pyqtSignal()
    zoom_fit_sig  = pyqtSignal()
    png_sig       = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setStyleSheet(f"QFrame{{background:{RENK_BG_BIRINCIL};"
                           f"border-bottom:1px solid {RENK_KENARLIK};}}")
        l = QHBoxLayout(self); l.setContentsMargins(10,0,10,0); l.setSpacing(3)

        self._mod_grup = QButtonGroup(self); self._mod_grup.setExclusive(True)

        araclar = [
            (MOD_SEC,  "↖", "Seç / Taşı"),
            (MOD_DKRT, "▭", "Dikdörtgen"),
            (MOD_ELMAS,"◇", "Elmas (Karar)"),
            (MOD_OVAL, "⬭", "Oval (Baş/Bitiş)"),
            (MOD_METIN,"T",  "Metin Kutusu"),
            (None, None, None),
            (MOD_OK,   "→", "Düz Ok (yatay/dikey)"),
            (MOD_LOK,  "⌐", "L-Ok (köşeli)"),
        ]
        for mod, ikon, tip in araclar:
            if mod is None:
                s = QFrame(); s.setFrameShape(QFrame.Shape.VLine)
                s.setStyleSheet(f"color:{RENK_KENARLIK};"); s.setFixedHeight(24)
                l.addWidget(s); continue
            b = QToolButton(); b.setText(ikon); b.setToolTip(tip)
            b.setCheckable(True); b.setFixedSize(34, 30)
            b.setStyleSheet(f"QToolButton{{border:1px solid transparent;border-radius:5px;"
                            f"font-size:13px;color:{RENK_YAZI_BIRINCIL};}}"
                            f"QToolButton:hover{{background:{RENK_PRIMARY_ACIK};}}"
                            f"QToolButton:checked{{background:{RENK_PRIMARY_ACIK};"
                            f"border-color:{RENK_PRIMARY};color:{RENK_PRIMARY};}}")
            if mod == MOD_SEC: b.setChecked(True)
            b.clicked.connect(lambda _, m=mod: self.mod_degisti.emit(m))
            self._mod_grup.addButton(b); l.addWidget(b)
            setattr(self, f"btn_{mod}", b)

        l.addSpacing(6)
        for lbl, sig, tip in [
            ("↩ Geri Al", self.geri_al_sig,  "Geri Al (Ctrl+Z)"),
            ("⊞ Izgara",  self.izgara_sig,    "Izgarayı Aç/Kapat"),
        ]:
            b = QPushButton(lbl); b.setFixedHeight(28); b.setToolTip(tip)
            b.setStyleSheet(self._bstil())
            if lbl == "⊞ Izgara":
                b.setCheckable(True); b.setChecked(True)
                b.toggled.connect(self.izgara_sig)
            else:
                b.clicked.connect(sig)
            l.addWidget(b)

        l.addStretch()

        # Zoom butonları — net etiketler
        for txt, sig, tip in [
            ("Yakınlaş +", self.zoom_in_sig,  "Yakınlaştır"),
            ("Uzaklaş −",  self.zoom_out_sig, "Uzaklaştır"),
            ("Tümü ⊡",    self.zoom_fit_sig,  "Tüm şemayı göster"),
        ]:
            b = QPushButton(txt); b.setFixedHeight(28); b.setToolTip(tip)
            b.setStyleSheet(self._bstil()); b.clicked.connect(sig)
            l.addWidget(b)

        l.addSpacing(6)
        bp = QPushButton("📷  PNG Aktar"); bp.setFixedHeight(28)
        bp.setToolTip("Akış şemasını PNG dosyası olarak kaydet")
        bp.setStyleSheet(f"QPushButton{{border:1px solid {RENK_PRIMARY};border-radius:5px;"
                         f"background:{RENK_PRIMARY_ACIK};color:{RENK_PRIMARY};"
                         f"font-size:11px;padding:0 10px;}}"
                         f"QPushButton:hover{{background:{RENK_PRIMARY};color:white;}}")
        bp.clicked.connect(self.png_sig); l.addWidget(bp)

    def _bstil(self): return (f"QPushButton{{border:1px solid {RENK_KENARLIK};border-radius:5px;"
                              f"background:{RENK_BG_IKINCIL};color:{RENK_YAZI_BIRINCIL};"
                              f"font-size:11px;padding:0 8px;}}"
                              f"QPushButton:hover{{background:{RENK_PRIMARY_ACIK};color:{RENK_PRIMARY};}}"
                              f"QPushButton:checked{{background:{RENK_PRIMARY_ACIK};"
                              f"border-color:{RENK_PRIMARY};color:{RENK_PRIMARY};}}")

    def sec_modunu_sec(self):
        if hasattr(self, f"btn_{MOD_SEC}"):
            getattr(self, f"btn_{MOD_SEC}").setChecked(True)


# ─── Sol Palet ────────────────────────────────────────────────────────────────
class SolPalet(QFrame):
    mod_sec = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(68)
        self.setStyleSheet(f"QFrame{{background:{RENK_BG_BIRINCIL};"
                           f"border-right:1px solid {RENK_KENARLIK};}}")
        l = QVBoxLayout(self); l.setContentsMargins(5,10,5,10); l.setSpacing(4)
        self._btnlar: list[QPushButton] = []

        def sep(txt):
            lb = QLabel(txt)
            lb.setStyleSheet(f"font-size:8px;color:{RENK_YAZI_UCUNCUL};"
                             f"padding:4px 0 2px 2px;")
            l.addWidget(lb)

        sep("ŞEKIL")
        for mod, ikon, ad in [
            (MOD_DKRT,  "▭", "İşlem"),
            (MOD_ELMAS, "◇", "Karar"),
            (MOD_OVAL,  "⬭", "Baş/Bitiş"),
            (MOD_METIN, "T", "Metin"),
        ]:
            b = self._btn(mod, ikon, ad); l.addWidget(b)

        sep("OK")
        for mod, ikon, ad in [
            (MOD_OK,  "→", "Düz Ok"),
            (MOD_LOK, "⌐", "L-Ok"),
        ]:
            b = self._btn(mod, ikon, ad); l.addWidget(b)

        l.addStretch()

    def _btn(self, mod, ikon, ad):
        b = QPushButton(f"{ikon}\n{ad}")
        b.setFixedSize(56, 48); b.setToolTip(ad); b.setCheckable(True)
        b.setStyleSheet(f"QPushButton{{border:1px solid {RENK_KENARLIK};border-radius:6px;"
                        f"background:{RENK_BG_IKINCIL};font-size:10px;"
                        f"color:{RENK_YAZI_BIRINCIL};text-align:center;}}"
                        f"QPushButton:hover{{background:{RENK_PRIMARY_ACIK};"
                        f"border-color:{RENK_PRIMARY};}}"
                        f"QPushButton:checked{{background:{RENK_PRIMARY_ACIK};"
                        f"border-color:{RENK_PRIMARY};color:{RENK_PRIMARY};}}")
        b.clicked.connect(lambda: self.mod_sec.emit(mod))
        self._btnlar.append(b)
        return b

    def temizle(self):
        for b in self._btnlar: b.setChecked(False)


# ─── Ana Dialog ───────────────────────────────────────────────────────────────
class AkisEditoruDialog(QDialog):
    kaydedildi = pyqtSignal(dict)

    def __init__(self, data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Proses Akış Şeması Editörü")
        self.setMinimumSize(1000, 650)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)

        # Başlık
        bf = QFrame()
        bf.setStyleSheet(f"background:{RENK_PRIMARY};")
        bf.setFixedHeight(38)
        bl = QHBoxLayout(bf); bl.setContentsMargins(14,0,14,0)
        t = QLabel("Proses Akış Şeması Editörü")
        t.setStyleSheet("font-size:13px;font-weight:bold;color:white;")
        bl.addWidget(t); bl.addStretch()
        ip = QLabel("Çift tıkla: metin  ·  Del: sil  ·  Ctrl+C/X/V: kopyala/kes/yapıştır  ·  "
                    "Ctrl+Z: geri al  ·  Orta fare: kaydır  ·  Boşluk: el modu")
        ip.setStyleSheet("font-size:10px;color:rgba(255,255,255,180);")
        bl.addWidget(ip)
        layout.addWidget(bf)

        # Araç çubuğu
        self._arac = AracCubugu()
        layout.addWidget(self._arac)

        # İçerik
        ic = QHBoxLayout(); ic.setContentsMargins(0,0,0,0); ic.setSpacing(0)
        self._palet = SolPalet()
        ic.addWidget(self._palet)

        self._sahne = AkisSahne()
        self._canvas = AkisCanvas(self._sahne)
        ic.addWidget(self._canvas, 1)

        pf = QFrame()
        pf.setStyleSheet(f"border-left:1px solid {RENK_KENARLIK};"
                         f"background:{RENK_BG_BIRINCIL};")
        pfl = QVBoxLayout(pf); pfl.setContentsMargins(0,0,0,0)
        self._ozellik = OzelliklerPaneli()
        scroll = QScrollArea(); scroll.setWidget(self._ozellik)
        scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        pfl.addWidget(scroll)
        ic.addWidget(pf)

        icw = QWidget(); icw.setLayout(ic)
        layout.addWidget(icw, 1)

        # Alt bar
        af = QFrame()
        af.setStyleSheet(f"background:{RENK_BG_IKINCIL};"
                         f"border-top:1px solid {RENK_KENARLIK};")
        af.setFixedHeight(34)
        al = QHBoxLayout(af); al.setContentsMargins(12,0,12,0); al.setSpacing(10)
        self.lbl_d = QLabel("Hazır")
        self.lbl_d.setStyleSheet(f"font-size:10px;color:{RENK_YAZI_UCUNCUL};")
        al.addWidget(self.lbl_d); al.addStretch()
        for txt, slot, stil in [
            ("İptal", self.reject,
             f"border:1px solid {RENK_KENARLIK};background:{RENK_BG_IKINCIL};"
             f"color:{RENK_YAZI_BIRINCIL};"),
            ("💾  Kaydet ve Kapat", self._kaydet,
             f"border:none;background:{RENK_PRIMARY};color:white;font-weight:bold;"),
        ]:
            b = QPushButton(txt); b.setFixedHeight(26)
            b.setStyleSheet(f"QPushButton{{{stil}border-radius:5px;"
                            f"font-size:11px;padding:0 14px;}}")
            b.clicked.connect(slot); al.addWidget(b)
        layout.addWidget(af)

        # Bağlantılar
        self._arac.mod_degisti.connect(self._mod)
        self._arac.geri_al_sig.connect(self._sahne.geri_al)
        self._arac.izgara_sig.connect(lambda a: (
            setattr(self._sahne, '_izgara', a), self._sahne.update()))
        self._arac.zoom_in_sig.connect(lambda: self._canvas.scale(1.2,1.2))
        self._arac.zoom_out_sig.connect(lambda: self._canvas.scale(0.83,0.83))
        self._arac.zoom_fit_sig.connect(lambda: self._canvas.fitInView(
            QRectF(0,0,CANVAS_W,CANVAS_H), Qt.AspectRatioMode.KeepAspectRatio))
        self._arac.png_sig.connect(self._png)
        self._palet.mod_sec.connect(self._mod)
        self._sahne.degisti.connect(lambda: self.lbl_d.setText("● Kaydedilmemiş değişiklik"))
        self._sahne.sekil_secildi.connect(self._ozellik.yukle)
        self._sahne.mod_otomatik_sec.connect(self._sec_mod)
        self._ozellik.degisti.connect(self._op_degisti)
        self._ozellik.sil_iste.connect(self._sahne.secili_sil)
        self._ozellik.kopyala.connect(self._sahne.kopyala)
        self._ozellik.kes.connect(self._sahne.kes)
        self._ozellik.yapistir.connect(self._sahne.yapistir)

        if data: self._sahne.yukle(data)
        self.showMaximized()

    def _mod(self, mod: str):
        self._canvas.set_mod(mod)

    def _sec_mod(self):
        self._canvas.set_mod(MOD_SEC)
        self._arac.sec_modunu_sec()
        self._palet.temizle()

    def _op_degisti(self, v: SekliVeri):
        sid = v.id
        if sid in self._sahne._sekil_items:
            item = self._sahne._sekil_items[sid]
            item.prepareGeometryChange()
            item.setPos(v.x, v.y)
            item._tutamac_guncelle()
            item.update()
        self._sahne.okları_guncelle()
        self._sahne.degisti.emit()

    def _png(self):
        dosya, _ = QFileDialog.getSaveFileName(
            self, "PNG Olarak Kaydet", "akis_semasi.png", "PNG (*.png)")
        if dosya:
            self._sahne.png_kaydet(dosya, dpi=200)
            QMessageBox.information(self, "Kaydedildi",
                                    f"Akış şeması kaydedildi:\n{dosya}")

    def _kaydet(self):
        self.kaydedildi.emit(self._sahne.to_data())
        self.accept()

    def get_data(self): return self._sahne.to_data()
    def png_binary(self, dpi=200): return self._sahne.png_render(dpi)


# ─── Ana Widget (Ana Pencere'ye gömülür) ─────────────────────────────────────
class AkisEditoruWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict = {"sekiller": [], "oklar": []}
        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(0)

        tb = QFrame()
        tb.setStyleSheet(f"background:{RENK_BG_BIRINCIL};"
                         f"border-bottom:1px solid {RENK_KENARLIK};")
        tb.setFixedHeight(46)
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(16,0,16,0); tbl.setSpacing(8)
        lbl = QLabel("Proses Akış Şeması")
        lbl.setStyleSheet(f"font-size:13px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        tbl.addWidget(lbl); tbl.addStretch()

        self.lbl_d = QLabel("Henüz çizilmedi")
        self.lbl_d.setStyleSheet(f"font-size:11px;color:{RENK_YAZI_UCUNCUL};")
        tbl.addWidget(self.lbl_d)

        btn = QPushButton("✏️  Editörü Aç")
        btn.setFixedHeight(30)
        btn.setStyleSheet(f"QPushButton{{background:{RENK_PRIMARY};color:white;border:none;"
                          f"border-radius:6px;font-size:12px;font-weight:bold;padding:0 14px;}}"
                          f"QPushButton:hover{{background:{RENK_PRIMARY_KOYU};}}")
        btn.clicked.connect(self._ac)
        tbl.addWidget(btn)
        l.addWidget(tb)

        self._onizleme = QLabel()
        self._onizleme.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._onizleme.setMinimumHeight(280)
        self._onizleme.setText("Akış şeması henüz oluşturulmadı.\n'Editörü Aç' butonu ile başlayın.")
        self._onizleme.setStyleSheet(f"background:#F8F9FA;border:1px dashed {RENK_KENARLIK};"
                                     f"color:{RENK_YAZI_UCUNCUL};font-size:12px;")
        l.addWidget(self._onizleme, 1)

    def _ac(self):
        dlg = AkisEditoruDialog(
            data=self._data if self._data.get("sekiller") else None,
            parent=self)
        dlg.kaydedildi.connect(self._al)
        dlg.exec()

    def _al(self, data: dict):
        self._data = data
        n = len(data.get("sekiller", []))
        m = len(data.get("oklar", []))
        if n > 0:
            self.lbl_d.setText(f"{n} şekil, {m} ok")
            self.lbl_d.setStyleSheet(
                f"font-size:11px;color:{RENK_PRIMARY};font-weight:bold;")
            self._onizleme_guncelle()
        self.degisti.emit()

    def _onizleme_guncelle(self):
        try:
            s = AkisSahne(); s._izgara = False; s.yukle(self._data)
            png = s.png_render(dpi=60)
            pix = QPixmap(); pix.loadFromData(png)
            if not pix.isNull():
                self._onizleme.setPixmap(pix.scaledToWidth(
                    min(self._onizleme.width()-20, pix.width()),
                    Qt.TransformationMode.SmoothTransformation))
        except Exception:
            pass

    def yukle(self, data: dict):
        self._data = data
        if data and data.get("sekiller"):
            self.lbl_d.setText(f"{len(data['sekiller'])} şekil")
            self._onizleme_guncelle()

    def to_data(self): return self._data

    def png_binary(self, dpi=200) -> bytes:
        s = AkisSahne(); s._izgara = False; s.yukle(self._data)
        return s.png_render(dpi)
