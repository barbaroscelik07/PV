"""
PV-DOC — Proses Akış Şeması Editörü
Sadece Dikdörtgen + Düz Ok + L-Ok
4 sütun kılavuzlu serbest canvas
"""

import math
import uuid
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsPathItem, QGraphicsLineItem,
    QSizePolicy, QToolButton, QButtonGroup, QComboBox, QSpinBox,
    QTextEdit, QInputDialog, QApplication, QMessageBox,
    QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QFont, QPainter, QPolygonF,
    QPainterPath, QImage, QPixmap, QKeySequence
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
SUTUN_ORANLARI = [0.0, 0.22, 0.50, 0.72, 1.0]
SUTUN_ADLARI = [
    "Başlangıç Maddeleri",
    "Proses Adımı",
    "IPK Testleri",
    "Rutin / Val. Testleri",
]
MOD_SEC  = "sec"
MOD_DKRT = "dikdortgen"
MOD_OK   = "ok"
MOD_LOK  = "lok"

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
TUT = 8  # tutamaç boyutu

# ─── Veri ─────────────────────────────────────────────────────────────────────
class SekliVeri:
    def __init__(self, metin="", x=100.0, y=100.0, w=160.0, h=52.0,
                 kenar_renk="#1A1A1A", kenar_stil="Düz", yazi_boyut=11,
                 yatay="orta", dikey="orta", sid=None):
        self.id = sid or str(uuid.uuid4())[:8]
        self.metin = metin
        self.x = x;  self.y = y
        self.w = w;  self.h = h
        self.kenar_renk = kenar_renk
        self.kenar_stil = kenar_stil
        self.yazi_boyut = yazi_boyut
        self.yatay = yatay
        self.dikey = dikey

    def to_dict(self): return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d):
        s = cls(); s.__dict__.update(d); return s

    def kopya(self):
        d = self.to_dict(); d["id"] = str(uuid.uuid4())[:8]
        return SekliVeri.from_dict(d)


class OkVeri:
    def __init__(self, x1=0.0, y1=0.0, x2=0.0, y2=0.0, tip="ok", oid=None):
        self.id  = oid or str(uuid.uuid4())[:8]
        self.x1  = x1;  self.y1 = y1
        self.x2  = x2;  self.y2 = y2
        self.tip = tip   # "ok"=düz dik, "lok"=L-şekil

    def to_dict(self): return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d):
        o = cls(); o.__dict__.update(d); return o

    def kopya(self):
        d = self.to_dict(); d["id"] = str(uuid.uuid4())[:8]
        return OkVeri.from_dict(d)


# ─── Tutamaç ──────────────────────────────────────────────────────────────────
class Tutamac(QGraphicsRectItem):
    CURSOR = {
        "tl": Qt.CursorShape.SizeFDiagCursor,
        "tr": Qt.CursorShape.SizeBDiagCursor,
        "bl": Qt.CursorShape.SizeBDiagCursor,
        "br": Qt.CursorShape.SizeFDiagCursor,
        "t":  Qt.CursorShape.SizeVerCursor,
        "b":  Qt.CursorShape.SizeVerCursor,
        "l":  Qt.CursorShape.SizeHorCursor,
        "r":  Qt.CursorShape.SizeHorCursor,
    }

    def __init__(self, yon: str, parent: QGraphicsItem):
        super().__init__(-TUT/2, -TUT/2, TUT, TUT, parent)
        self.yon = yon
        self.setBrush(QBrush(QColor("#1a5fa5")))
        self.setPen(QPen(QColor("white"), 1.5))
        self.setZValue(200)
        self.setVisible(False)
        self.setCursor(self.CURSOR.get(yon, Qt.CursorShape.SizeAllCursor))
        # Tutamaç kendisi hareket etmesin
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

    def guncelle(self, w, h):
        poz = {
            "tl": (0,   0  ), "t":  (w/2, 0  ), "tr": (w,   0  ),
            "l":  (0,   h/2),                    "r":  (w,   h/2),
            "bl": (0,   h  ), "b":  (w/2, h  ), "br": (w,   h  ),
        }
        self.setPos(*poz[self.yon])


# ─── Şekil Item ───────────────────────────────────────────────────────────────
class SekliItem(QGraphicsItem):
    def __init__(self, veri: SekliVeri, sahne: 'AkisSahne'):
        super().__init__()
        self.veri   = veri
        self.sahne  = sahne
        self._yon   = None           # aktif tutamaç yönü
        self._yb_bas    = None       # yeniden boyutlandırma başlangıcı (scene)
        self._yb_orig   = None       # (x,y,w,h) başlangıç değerleri
        self._tutamaclar: dict[str, Tutamac] = {}

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

    def _tutamac_guncelle(self):
        for t in self._tutamaclar.values():
            t.guncelle(self.veri.w, self.veri.h)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        stil = KENAR_STILLERI.get(self.veri.kenar_stil, Qt.PenStyle.SolidLine)
        kalinlik = 2.5 if self.isSelected() else 1.5
        renk = RENK_PRIMARY if self.isSelected() else self.veri.kenar_renk
        painter.setPen(QPen(QColor(renk), kalinlik, stil))
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRoundedRect(QRectF(0, 0, self.veri.w, self.veri.h), 6, 6)

        # Metin
        painter.setPen(QPen(QColor(self.veri.kenar_renk)))
        painter.setFont(QFont(FONT_AILESI, self.veri.yazi_boyut))
        yf = {"sol": Qt.AlignmentFlag.AlignLeft,
              "orta": Qt.AlignmentFlag.AlignHCenter,
              "sag":  Qt.AlignmentFlag.AlignRight
              }.get(self.veri.yatay, Qt.AlignmentFlag.AlignHCenter)
        df = {"ust":  Qt.AlignmentFlag.AlignTop,
              "orta": Qt.AlignmentFlag.AlignVCenter,
              "alt":  Qt.AlignmentFlag.AlignBottom
              }.get(self.veri.dikey, Qt.AlignmentFlag.AlignVCenter)
        painter.drawText(
            QRectF(6, 4, self.veri.w-12, self.veri.h-8),
            yf | df | Qt.TextFlag.TextWordWrap,
            self.veri.metin)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            show = bool(value)
            if show:
                self._tutamac_guncelle()
            for t in self._tutamaclar.values():
                t.setVisible(show)
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.veri.x = self.pos().x()
            self.veri.y = self.pos().y()
            self.sahne.okları_guncelle()
            self.sahne.degisti.emit()
        return super().itemChange(change, value)

    def _tutamac_yukle(self, scene_pos) -> str | None:
        """scene_pos yakınında tutamaç var mı? Varsa yönü döner."""
        for yon, t in self._tutamaclar.items():
            if not t.isVisible():
                continue
            # Tutacın merkezi — parent item koordinatından sahneye dönüştür
            t_scene = self.mapToScene(t.pos())
            dist = (scene_pos - t_scene).manhattanLength()
            if dist < TUT * 2 + 8:   # zoom toleransı için daha geniş alan
                return yon
        return None

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event); return
        yon = self._tutamac_yukle(event.scenePos())
        if yon:
            self._yon = yon
            self._yb_bas  = event.scenePos()
            self._yb_orig = (self.veri.x, self.veri.y,
                             self.veri.w, self.veri.h)
            # Taşımayı engelle — boyutlandırma yapılıyor
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            event.accept()
            return
        self._yon = None
        # Taşımayı aç
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._yon:
            delta = event.scenePos() - self._yb_bas
            ox, oy, ow, oh = self._yb_orig
            nx, ny, nw, nh = ox, oy, ow, oh
            MIN_W, MIN_H = 40, 24
            yon = self._yon
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
            event.accept(); return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._yon:
            self._yon = None
            # Taşımayı geri aç
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
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
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setZValue(-1)
        self._bas_pos = None   # taşıma için

    def _noktalar(self):
        x1, y1, x2, y2 = self.veri.x1, self.veri.y1, self.veri.x2, self.veri.y2
        if self.veri.tip == "lok":
            return [(x1, y1), (x2, y1), (x2, y2)]
        # Düz dik ok: büyük eksende git
        if abs(x2 - x1) >= abs(y2 - y1):
            return [(x1, y1), (x2, y1)]
        else:
            return [(x1, y1), (x1, y2)]

    def boundingRect(self):
        pts = self._noktalar()
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        m = 14
        return QRectF(min(xs)-m, min(ys)-m,
                      max(xs)-min(xs)+m*2,
                      max(ys)-min(ys)+m*2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renk = RENK_PRIMARY if self.isSelected() else "#455A64"
        painter.setPen(QPen(QColor(renk), 2.0,
                            Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        pts = self._noktalar()
        for i in range(len(pts) - 1):
            painter.drawLine(
                QPointF(pts[i][0], pts[i][1]),
                QPointF(pts[i+1][0], pts[i+1][1]))

        # Ok başı (sadece üçgen — ayrı path)
        if len(pts) >= 2:
            ex, ey = pts[-1]; px, py = pts[-2]
            dx = ex - px; dy = ey - py
            u  = math.sqrt(dx*dx + dy*dy)
            if u > 0:
                ux = dx/u; uy = dy/u
                p = QPainterPath()
                p.moveTo(ex, ey)
                p.lineTo(ex - 12*ux - 5*uy, ey - 12*uy + 5*ux)
                p.lineTo(ex - 12*ux + 5*uy, ey - 12*uy - 5*ux)
                p.closeSubpath()
                painter.setBrush(QBrush(QColor(renk)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPath(p)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._bas_pos = event.scenePos()
            self._orig = (self.veri.x1, self.veri.y1,
                          self.veri.x2, self.veri.y2)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._bas_pos:
            d = event.scenePos() - self._bas_pos
            ox1, oy1, ox2, oy2 = self._orig
            self.veri.x1 = ox1 + d.x(); self.veri.y1 = oy1 + d.y()
            self.veri.x2 = ox2 + d.x(); self.veri.y2 = oy2 + d.y()
            self.prepareGeometryChange()
            self.update()
            event.accept(); return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._bas_pos:
            self._bas_pos = None
            scene = self.scene()
            if scene: scene.degisti.emit()
        super().mouseReleaseEvent(event)

    def guncelle(self):
        self.prepareGeometryChange()
        self.update()


# ─── Sahne ────────────────────────────────────────────────────────────────────
class AkisSahne(QGraphicsScene):
    degisti          = pyqtSignal()
    sekil_secildi    = pyqtSignal(object)
    mod_otomatik_sec = pyqtSignal()

    def __init__(self):
        super().__init__(0, 0, CANVAS_W, CANVAS_H)
        self._mod             = MOD_SEC
        self._sekil_items: dict[str, SekliItem] = {}
        self._ok_items:    dict[str, OkItem]    = {}
        self._sekil_verileri: list[SekliVeri]   = []
        self._ok_verileri:    list[OkVeri]      = []
        self._geri_al: list  = []
        self._ok_bas: QPointF | None = None
        self._gecici: QGraphicsLineItem | None  = None
        self._pano_sekiller: list[SekliVeri] = []
        self._pano_oklar:    list[OkVeri]    = []
        self.selectionChanged.connect(self._secim_degisti)

    # ── Arka plan ─────────────────────────────────────────────────────────────
    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor("#FAFAFA"))
        # Sütun kılavuzları
        for oran in SUTUN_ORANLARI[1:-1]:
            x = int(CANVAS_W * oran)
            painter.setPen(QPen(QColor("#C5D8EE"), 1.2, Qt.PenStyle.DashLine))
            painter.drawLine(x, 0, x, CANVAS_H)
        # Sütun başlıkları
        for i in range(4):
            x1 = int(CANVAS_W * SUTUN_ORANLARI[i])
            x2 = int(CANVAS_W * SUTUN_ORANLARI[i+1])
            painter.setPen(QPen(QColor("#7B9EC4")))
            f = QFont(FONT_AILESI, 9); f.setBold(True); painter.setFont(f)
            painter.drawText(QRectF(x1+4, 4, x2-x1-8, 22),
                             Qt.AlignmentFlag.AlignCenter,
                             SUTUN_ADLARI[i])

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
            self._gecici = QGraphicsLineItem(pos.x(), pos.y(), pos.x(), pos.y())
            self._gecici.setPen(QPen(QColor("#455A64"), 1.5, Qt.PenStyle.DashLine))
            self.addItem(self._gecici)
            return

        if self._mod == MOD_DKRT:
            w, h = 160, 52
            x = round((pos.x() - w/2) / 20) * 20
            y = round((pos.y() - h/2) / 20) * 20
            self._durum_kaydet()
            v = SekliVeri(metin="Metin", x=x, y=y, w=w, h=h)
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
        if (self._gecici and self._ok_bas
                and event.button() == Qt.MouseButton.LeftButton):
            bitis = event.scenePos()
            self.removeItem(self._gecici); self._gecici = None
            self._durum_kaydet()
            ok = OkVeri(x1=self._ok_bas.x(), y1=self._ok_bas.y(),
                        x2=bitis.x(), y2=bitis.y(),
                        tip="lok" if self._mod == MOD_LOK else "ok")
            self._ok_ekle(ok)
            self._ok_bas = None
            self.degisti.emit(); return
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
        sec = self.selectedItems()
        if sec and isinstance(sec[0], SekliItem):
            self.sekil_secildi.emit(sec[0].veri)
        else:
            self.sekil_secildi.emit(None)

    def secili_sil(self):
        self._durum_kaydet()
        for item in list(self.selectedItems()):
            if isinstance(item, SekliItem):
                self._sekil_verileri = [v for v in self._sekil_verileri
                                        if v.id != item.veri.id]
                del self._sekil_items[item.veri.id]
                self.removeItem(item)
            elif isinstance(item, OkItem):
                self._ok_verileri = [v for v in self._ok_verileri
                                     if v.id != item.veri.id]
                del self._ok_items[item.veri.id]
                self.removeItem(item)
        self.degisti.emit()

    def kopyala(self):
        self._pano_sekiller = [i.veri.kopya() for i in self.selectedItems()
                               if isinstance(i, SekliItem)]
        self._pano_oklar    = [i.veri.kopya() for i in self.selectedItems()
                               if isinstance(i, OkItem)]

    def kes(self):
        self.kopyala()
        self.secili_sil()

    def yapistir(self):
        if not self._pano_sekiller and not self._pano_oklar: return
        self._durum_kaydet()
        self.clearSelection()
        id_map = {}
        for v in self._pano_sekiller:
            yeni = v.kopya(); yeni.x += 20; yeni.y += 20
            id_map[v.id] = yeni.id
            self._sekil_ekle(yeni)
            self._sekil_items[yeni.id].setSelected(True)
        for v in self._pano_oklar:
            yeni = v.kopya()
            yeni.x1 += 20; yeni.y1 += 20
            yeni.x2 += 20; yeni.y2 += 20
            self._ok_ekle(yeni)
        # Panoyu offset et
        for v in self._pano_sekiller: v.x += 20; v.y += 20
        for v in self._pano_oklar:    v.x1 += 20; v.y1 += 20; v.x2 += 20; v.y2 += 20
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
        for sd in d.get("sekiller", []): self._sekil_ekle(SekliVeri.from_dict(sd))
        for od in d.get("oklar",    []): self._ok_ekle(OkVeri.from_dict(od))
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
        # Sadece şekil ve ok item'larını al (tutamaçları hariç tut)
        items = [item for item in self.items()
                 if isinstance(item, (SekliItem, OkItem))]
        if items:
            rects = [item.mapToScene(item.boundingRect()).boundingRect()
                     for item in items]
            min_x = min(r.left()   for r in rects) - 40
            min_y = min(r.top()    for r in rects) - 40
            max_x = max(r.right()  for r in rects) + 40
            max_y = max(r.bottom() for r in rects) + 40
            src = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
        else:
            src = QRectF(0, 0, CANVAS_W, CANVAS_H)

        sc = dpi / 96.0
        img = QImage(max(1, int(src.width() * sc)),
                     max(1, int(src.height() * sc)),
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
        self._sahne   = sahne
        self._pan_mod = False
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
        self.setStyleSheet("background:#FAFAFA;border:none;")
        self.fitInView(QRectF(0, 0, CANVAS_W, CANVAS_H),
                       Qt.AspectRatioMode.KeepAspectRatio)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_mod(self, mod: str):
        self._sahne.set_mod(mod)
        if mod == MOD_SEC:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)

    # Zoom
    def wheelEvent(self, event):
        f = 1.15 if event.angleDelta().y() > 0 else 0.87
        self.scale(f, f)

    # Klavye
    def keyPressEvent(self, event):
        s = self._sahne
        key  = event.key()
        ctrl = event.modifiers() == Qt.KeyboardModifier.ControlModifier

        # Boşluk → pan modu
        if key == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._pan_mod = True
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept(); return

        if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            s.secili_sil(); return
        if ctrl and key == Qt.Key.Key_Z: s.geri_al(); return
        if ctrl and key == Qt.Key.Key_C: s.kopyala(); return
        if ctrl and key == Qt.Key.Key_X: s.kes();     return
        if ctrl and key == Qt.Key.Key_V: s.yapistir(); return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self._pan_mod = False
            mod = self._sahne._mod
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag
                             if mod == MOD_SEC else
                             QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().keyReleaseEvent(event)


# ─── Özellikler Paneli ────────────────────────────────────────────────────────
class OzelliklerPaneli(QWidget):
    degisti  = pyqtSignal(object)
    sil_iste = pyqtSignal()
    kopyala  = pyqtSignal()
    kes_iste = pyqtSignal()
    yapistir = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._v   = None
        self._gun = False
        self.setMinimumWidth(200)

        l = QVBoxLayout(self)
        l.setContentsMargins(10, 10, 10, 10); l.setSpacing(6)

        t = QLabel("Özellikler")
        t.setStyleSheet(f"font-size:12px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        l.addWidget(t)

        self.lbl_bos = QLabel("Şekil seçilmedi")
        self.lbl_bos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_bos.setStyleSheet(
            f"font-size:11px;color:{RENK_YAZI_UCUNCUL};padding:16px 0;")
        l.addWidget(self.lbl_bos)

        self.pnl = QWidget()
        pl = QVBoxLayout(self.pnl)
        pl.setContentsMargins(0, 0, 0, 0); pl.setSpacing(5)

        # Metin
        pl.addWidget(self._lbl("Metin"))
        self.txt = QTextEdit(); self.txt.setFixedHeight(64)
        self.txt.setStyleSheet(self._inp())
        self.txt.textChanged.connect(self._m)
        pl.addWidget(self.txt)

        # Yatay hizalama
        pl.addWidget(self._lbl("Yatay"))
        yw = QWidget(); yl = QHBoxLayout(yw)
        yl.setContentsMargins(0,0,0,0); yl.setSpacing(2)
        self._yg = QButtonGroup(self); self._yg.setExclusive(True)
        for ikon, val in [("Sol","sol"),("Orta","orta"),("Sağ","sag")]:
            b = QPushButton(ikon); b.setFixedHeight(24); b.setCheckable(True)
            b.setStyleSheet(self._hbtn())
            b.clicked.connect(lambda _, v=val: self._yh(v))
            self._yg.addButton(b); yl.addWidget(b)
            setattr(self, f"by_{val}", b)
        pl.addWidget(yw)

        # Dikey hizalama
        pl.addWidget(self._lbl("Dikey"))
        dw = QWidget(); dl = QHBoxLayout(dw)
        dl.setContentsMargins(0,0,0,0); dl.setSpacing(2)
        self._dg = QButtonGroup(self); self._dg.setExclusive(True)
        for ikon, val in [("Üst","ust"),("Orta","orta"),("Alt","alt")]:
            b = QPushButton(ikon); b.setFixedHeight(24); b.setCheckable(True)
            b.setStyleSheet(self._hbtn())
            b.clicked.connect(lambda _, v=val: self._dh(v))
            self._dg.addButton(b); dl.addWidget(b)
            setattr(self, f"bd_{val}", b)
        pl.addWidget(dw)

        # Boyut
        pl.addWidget(self._lbl("Genişlik × Yükseklik"))
        bw = QWidget(); bl = QHBoxLayout(bw)
        bl.setContentsMargins(0,0,0,0); bl.setSpacing(3)
        self.sw = QSpinBox(); self.sw.setRange(20, 1200); self.sw.setStyleSheet(self._inp())
        self.sh = QSpinBox(); self.sh.setRange(15, 900);  self.sh.setStyleSheet(self._inp())
        self.sw.valueChanged.connect(self._b)
        self.sh.valueChanged.connect(self._b)
        bl.addWidget(self.sw); bl.addWidget(self.sh)
        pl.addWidget(bw)

        # Konum
        pl.addWidget(self._lbl("X × Y"))
        kw = QWidget(); kl = QHBoxLayout(kw)
        kl.setContentsMargins(0,0,0,0); kl.setSpacing(3)
        self.sx = QSpinBox(); self.sx.setRange(0, 1400); self.sx.setStyleSheet(self._inp())
        self.sy = QSpinBox(); self.sy.setRange(0, 1000); self.sy.setStyleSheet(self._inp())
        self.sx.valueChanged.connect(self._k)
        self.sy.valueChanged.connect(self._k)
        kl.addWidget(self.sx); kl.addWidget(self.sy)
        pl.addWidget(kw)

        # Yazı boyutu
        pl.addWidget(self._lbl("Yazı Boyutu"))
        self.syb = QSpinBox(); self.syb.setRange(7, 24)
        self.syb.setStyleSheet(self._inp())
        self.syb.valueChanged.connect(self._yb)
        pl.addWidget(self.syb)

        # Kenarlık rengi
        pl.addWidget(self._lbl("Kenarlık Rengi"))
        rw = QWidget(); rl = QHBoxLayout(rw)
        rl.setContentsMargins(0,0,0,0); rl.setSpacing(3)
        self._rbtn = {}
        for isim, renk in KENAR_RENKLERI.items():
            b = QPushButton(); b.setFixedSize(24, 24); b.setCheckable(True)
            b.setToolTip(isim)
            b.setStyleSheet(
                f"QPushButton{{background:{renk};border:2px solid transparent;"
                f"border-radius:12px;}}"
                f"QPushButton:checked{{border-color:#1a5fa5;}}")
            b.clicked.connect(lambda _, r=renk: self._rc(r))
            rl.addWidget(b); self._rbtn[renk] = b
        pl.addWidget(rw)

        # Kenarlık stili
        pl.addWidget(self._lbl("Kenarlık Stili"))
        self.cbs = QComboBox()
        self.cbs.addItems(list(KENAR_STILLERI.keys()))
        self.cbs.setStyleSheet(self._inp())
        self.cbs.currentTextChanged.connect(self._ks)
        pl.addWidget(self.cbs)

        pl.addSpacing(6)

        # Aksiyon butonları
        for txt, sig, stil in [
            ("✕  Sil (Del)",      self.sil_iste,
             f"background:#FADBD8;color:#C0392B;border:1px solid #F1948A;"),
            ("⧉  Kopyala (Ctrl+C)", self.kopyala,
             f"background:{RENK_BG_IKINCIL};color:{RENK_YAZI_IKINCIL};border:1px solid {RENK_KENARLIK};"),
            ("✂  Kes (Ctrl+X)",   self.kes_iste,
             f"background:{RENK_BG_IKINCIL};color:{RENK_YAZI_IKINCIL};border:1px solid {RENK_KENARLIK};"),
            ("⎘  Yapıştır (Ctrl+V)", self.yapistir,
             f"background:{RENK_BG_IKINCIL};color:{RENK_YAZI_IKINCIL};border:1px solid {RENK_KENARLIK};"),
        ]:
            b = QPushButton(txt)
            b.setStyleSheet(
                f"QPushButton{{{stil}border-radius:5px;"
                f"font-size:11px;padding:5px;}}"
                f"QPushButton:hover{{opacity:0.8;}}")
            b.clicked.connect(sig)
            pl.addWidget(b)

        pl.addStretch()
        l.addWidget(self.pnl)
        l.addStretch()
        self.pnl.setVisible(False)

    # ── Yardımcılar ───────────────────────────────────────────────────────────
    def _lbl(self, t):
        lb = QLabel(t)
        lb.setStyleSheet(
            f"font-size:10px;font-weight:bold;color:{RENK_YAZI_IKINCIL};")
        return lb

    def _inp(self):
        return (f"QSpinBox,QTextEdit,QComboBox{{"
                f"border:1px solid {RENK_KENARLIK};border-radius:4px;"
                f"padding:3px 6px;font-size:11px;"
                f"background:{RENK_BG_BIRINCIL};}}")

    def _hbtn(self):
        return (f"QPushButton{{border:1px solid {RENK_KENARLIK};border-radius:4px;"
                f"background:{RENK_BG_IKINCIL};font-size:10px;padding:2px;}}"
                f"QPushButton:checked{{background:{RENK_PRIMARY_ACIK};"
                f"border-color:{RENK_PRIMARY};color:{RENK_PRIMARY};font-weight:bold;}}"
                f"QPushButton:hover{{background:{RENK_PRIMARY_ACIK};}}")

    # ── Yükle ─────────────────────────────────────────────────────────────────
    def yukle(self, v):
        self._v = v
        vis = isinstance(v, SekliVeri)
        self.lbl_bos.setVisible(not vis)
        self.pnl.setVisible(vis)
        if not vis: return
        self._gun = True
        self.txt.setPlainText(v.metin)
        self.sw.setValue(int(v.w));  self.sh.setValue(int(v.h))
        self.sx.setValue(int(v.x));  self.sy.setValue(int(v.y))
        self.syb.setValue(v.yazi_boyut)
        for r, b in self._rbtn.items():
            b.setChecked(r == v.kenar_renk)
        idx = self.cbs.findText(v.kenar_stil)
        if idx >= 0: self.cbs.setCurrentIndex(idx)
        for val in ("sol","orta","sag"):
            getattr(self, f"by_{val}").setChecked(val == v.yatay)
        for val in ("ust","orta","alt"):
            getattr(self, f"bd_{val}").setChecked(val == v.dikey)
        self._gun = False

    # ── Slot'lar ──────────────────────────────────────────────────────────────
    def _emit(self):
        if not self._gun and self._v:
            self.degisti.emit(self._v)

    def _m(self):
        if self._gun or not self._v: return
        self._v.metin = self.txt.toPlainText(); self._emit()

    def _b(self):
        if self._gun or not self._v: return
        self._v.w = self.sw.value(); self._v.h = self.sh.value(); self._emit()

    def _k(self):
        if self._gun or not self._v: return
        self._v.x = self.sx.value(); self._v.y = self.sy.value(); self._emit()

    def _yb(self):
        if self._gun or not self._v: return
        self._v.yazi_boyut = self.syb.value(); self._emit()

    def _yh(self, val):
        if self._gun or not self._v: return
        self._v.yatay = val; self._emit()

    def _dh(self, val):
        if self._gun or not self._v: return
        self._v.dikey = val; self._emit()

    def _rc(self, renk):
        if self._gun or not self._v: return
        self._v.kenar_renk = renk
        for r, b in self._rbtn.items(): b.setChecked(r == renk)
        self._emit()

    def _ks(self, stil):
        if self._gun or not self._v: return
        self._v.kenar_stil = stil; self._emit()


# ─── Ana Dialog ───────────────────────────────────────────────────────────────
class AkisEditoruDialog(QDialog):
    kaydedildi = pyqtSignal(dict)

    def __init__(self, data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Proses Akış Şeması Editörü — PV-DOC")
        self.setMinimumSize(900, 600)
        self.resize(1200, 750)
        self.setModal(True)
        # Normal pencere — kullanıcı küçültüp büyütebilir
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinMaxButtonsHint |
            Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        # ── Başlık çubuğu ─────────────────────────────────────────────────────
        bf = QFrame()
        bf.setStyleSheet(f"background:{RENK_PRIMARY};")
        bf.setFixedHeight(36)
        bl = QHBoxLayout(bf); bl.setContentsMargins(14, 0, 14, 0)
        tl = QLabel("Proses Akış Şeması Editörü")
        tl.setStyleSheet("font-size:13px;font-weight:bold;color:white;")
        bl.addWidget(tl); bl.addStretch()
        ip = QLabel(
            "Çift tıkla: metin  ·  Del: sil  ·  "
            "Ctrl+C/X/V: kopyala/kes/yapıştır  ·  "
            "Ctrl+Z: geri al  ·  Boşluk+sürükle: gezin  ·  Tekerlek: zoom")
        ip.setStyleSheet("font-size:10px;color:rgba(255,255,255,180);")
        bl.addWidget(ip)
        layout.addWidget(bf)

        # ── Araç çubuğu ───────────────────────────────────────────────────────
        tb = QFrame()
        tb.setFixedHeight(42)
        tb.setStyleSheet(
            f"background:{RENK_BG_BIRINCIL};"
            f"border-bottom:1px solid {RENK_KENARLIK};")
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(10, 0, 10, 0); tbl.setSpacing(3)

        self._mod_grup = QButtonGroup(self); self._mod_grup.setExclusive(True)
        araclar = [
            (MOD_SEC,  "↖ Seç",       "Seç / Taşı"),
            (MOD_DKRT, "▭ Dikdörtgen","Dikdörtgen ekle"),
            (MOD_OK,   "→ Düz Ok",    "Düz ok çiz (yatay veya dikey)"),
            (MOD_LOK,  "⌐ L-Ok",      "L-şekilli ok çiz"),
        ]
        for mod, ikon, tip in araclar:
            b = QToolButton(); b.setText(ikon); b.setToolTip(tip)
            b.setCheckable(True); b.setFixedHeight(30); b.setMinimumWidth(80)
            b.setStyleSheet(
                f"QToolButton{{border:1px solid {RENK_KENARLIK};border-radius:5px;"
                f"font-size:11px;color:{RENK_YAZI_BIRINCIL};padding:0 6px;}}"
                f"QToolButton:hover{{background:{RENK_PRIMARY_ACIK};}}"
                f"QToolButton:checked{{background:{RENK_PRIMARY_ACIK};"
                f"border-color:{RENK_PRIMARY};color:{RENK_PRIMARY};"
                f"font-weight:bold;}}")
            if mod == MOD_SEC: b.setChecked(True)
            b.clicked.connect(lambda _, m=mod: self._mod(m))
            self._mod_grup.addButton(b); tbl.addWidget(b)
            setattr(self, f"btn_{mod}", b)

        tbl.addSpacing(8)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color:{RENK_KENARLIK};"); sep.setFixedHeight(24)
        tbl.addWidget(sep); tbl.addSpacing(8)

        for txt, slot, tip in [
            ("↩ Geri Al",    self._geri_al, "Geri Al (Ctrl+Z)"),
        ]:
            b = QPushButton(txt); b.setFixedHeight(30); b.setToolTip(tip)
            b.setStyleSheet(self._bstil()); b.clicked.connect(slot)
            tbl.addWidget(b)

        tbl.addStretch()

        for txt, slot, tip in [
            ("Yakınlaş +",  lambda: self._canvas.scale(1.2, 1.2),   "Yakınlaştır"),
            ("Uzaklaş −",   lambda: self._canvas.scale(0.83, 0.83), "Uzaklaştır"),
            ("Tümünü Göster", self._tumu_goster, "Tüm şemayı göster"),
        ]:
            b = QPushButton(txt); b.setFixedHeight(30); b.setToolTip(tip)
            b.setStyleSheet(self._bstil()); b.clicked.connect(slot)
            tbl.addWidget(b)

        tbl.addSpacing(8)
        bp = QPushButton("📷  PNG Aktar"); bp.setFixedHeight(30)
        bp.setStyleSheet(
            f"QPushButton{{border:1px solid {RENK_PRIMARY};"
            f"border-radius:5px;background:{RENK_PRIMARY_ACIK};"
            f"color:{RENK_PRIMARY};font-size:11px;padding:0 12px;}}"
            f"QPushButton:hover{{background:{RENK_PRIMARY};color:white;}}")
        bp.clicked.connect(self._png)
        tbl.addWidget(bp)
        layout.addWidget(tb)

        # ── İçerik ────────────────────────────────────────────────────────────
        ic = QHBoxLayout(); ic.setContentsMargins(0, 0, 0, 0); ic.setSpacing(0)

        # Canvas
        self._sahne = AkisSahne()
        self._canvas = AkisCanvas(self._sahne)
        ic.addWidget(self._canvas, 1)

        # Sağ panel — scroll içinde
        pf = QFrame()
        pf.setStyleSheet(
            f"border-left:1px solid {RENK_KENARLIK};"
            f"background:{RENK_BG_BIRINCIL};")
        pfl = QVBoxLayout(pf); pfl.setContentsMargins(0, 0, 0, 0)
        self._ozellik = OzelliklerPaneli()
        scroll = QScrollArea()
        scroll.setWidget(self._ozellik)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(230)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        pfl.addWidget(scroll)
        ic.addWidget(pf)

        icw = QWidget(); icw.setLayout(ic)
        layout.addWidget(icw, 1)

        # ── Alt bar ───────────────────────────────────────────────────────────
        af = QFrame()
        af.setFixedHeight(34)
        af.setStyleSheet(
            f"background:{RENK_BG_IKINCIL};"
            f"border-top:1px solid {RENK_KENARLIK};")
        al = QHBoxLayout(af); al.setContentsMargins(12, 0, 12, 0); al.setSpacing(8)
        self.lbl_d = QLabel("Hazır")
        self.lbl_d.setStyleSheet(
            f"font-size:10px;color:{RENK_YAZI_UCUNCUL};")
        al.addWidget(self.lbl_d); al.addStretch()

        for txt, slot, stil in [
            ("İptal", self.reject,
             f"border:1px solid {RENK_KENARLIK};background:{RENK_BG_IKINCIL};"
             f"color:{RENK_YAZI_BIRINCIL};"),
            ("💾  Kaydet ve Kapat", self._kaydet,
             f"border:none;background:{RENK_PRIMARY};color:white;font-weight:bold;"),
        ]:
            b = QPushButton(txt); b.setFixedHeight(26)
            b.setStyleSheet(
                f"QPushButton{{{stil}border-radius:5px;"
                f"font-size:11px;padding:0 14px;}}")
            b.clicked.connect(slot); al.addWidget(b)
        layout.addWidget(af)

        # ── Bağlantılar ───────────────────────────────────────────────────────
        self._sahne.degisti.connect(
            lambda: self.lbl_d.setText("● Kaydedilmemiş değişiklik"))
        self._sahne.sekil_secildi.connect(self._ozellik.yukle)
        self._sahne.mod_otomatik_sec.connect(self._sec_mod)
        self._ozellik.degisti.connect(self._op_degisti)
        self._ozellik.sil_iste.connect(self._sahne.secili_sil)
        self._ozellik.kopyala.connect(self._sahne.kopyala)
        self._ozellik.kes_iste.connect(self._sahne.kes)
        self._ozellik.yapistir.connect(self._sahne.yapistir)

        if data: self._sahne.yukle(data)
        self.showMaximized()

    def _bstil(self):
        return (f"QPushButton{{border:1px solid {RENK_KENARLIK};border-radius:5px;"
                f"background:{RENK_BG_IKINCIL};color:{RENK_YAZI_BIRINCIL};"
                f"font-size:11px;padding:0 8px;}}"
                f"QPushButton:hover{{background:{RENK_PRIMARY_ACIK};"
                f"color:{RENK_PRIMARY};}}")

    def _mod(self, mod: str):
        self._canvas.set_mod(mod)

    def _sec_mod(self):
        self._canvas.set_mod(MOD_SEC)
        if hasattr(self, f"btn_{MOD_SEC}"):
            getattr(self, f"btn_{MOD_SEC}").setChecked(True)

    def _geri_al(self):
        self._sahne.geri_al()

    def _tumu_goster(self):
        self._canvas.fitInView(
            QRectF(0, 0, CANVAS_W, CANVAS_H),
            Qt.AspectRatioMode.KeepAspectRatio)

    def _op_degisti(self, v: SekliVeri):
        if v.id in self._sahne._sekil_items:
            item = self._sahne._sekil_items[v.id]
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
            QMessageBox.information(
                self, "Kaydedildi",
                f"Akış şeması başarıyla kaydedildi:\n{dosya}")

    def _kaydet(self):
        self.kaydedildi.emit(self._sahne.to_data())
        self.accept()

    def get_data(self):    return self._sahne.to_data()
    def png_binary(self, dpi=200): return self._sahne.png_render(dpi)


# ─── Ana Widget (Ana Pencere'ye gömülür) ─────────────────────────────────────
class AkisEditoruWidget(QWidget):
    degisti = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict = {"sekiller": [], "oklar": []}
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0); l.setSpacing(0)

        tb = QFrame()
        tb.setFixedHeight(46)
        tb.setStyleSheet(
            f"background:{RENK_BG_BIRINCIL};"
            f"border-bottom:1px solid {RENK_KENARLIK};")
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(16, 0, 16, 0); tbl.setSpacing(8)
        lbl = QLabel("Proses Akış Şeması")
        lbl.setStyleSheet(
            f"font-size:13px;font-weight:bold;color:{RENK_YAZI_BIRINCIL};")
        tbl.addWidget(lbl); tbl.addStretch()

        self.lbl_d = QLabel("Henüz çizilmedi")
        self.lbl_d.setStyleSheet(
            f"font-size:11px;color:{RENK_YAZI_UCUNCUL};")
        tbl.addWidget(self.lbl_d)

        btn = QPushButton("✏️  Editörü Aç")
        btn.setFixedHeight(30)
        btn.setStyleSheet(
            f"QPushButton{{background:{RENK_PRIMARY};color:white;border:none;"
            f"border-radius:6px;font-size:12px;font-weight:bold;padding:0 14px;}}"
            f"QPushButton:hover{{background:{RENK_PRIMARY_KOYU};}}")
        btn.clicked.connect(self._ac)
        tbl.addWidget(btn)
        l.addWidget(tb)

        self._onizleme = QLabel()
        self._onizleme.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._onizleme.setMinimumHeight(260)
        self._onizleme.setText(
            "Akış şeması henüz oluşturulmadı.\n'Editörü Aç' butonu ile başlayın.")
        self._onizleme.setStyleSheet(
            f"background:#F8F9FA;border:1px dashed {RENK_KENARLIK};"
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
        m = len(data.get("oklar",    []))
        if n > 0:
            self.lbl_d.setText(f"{n} şekil, {m} ok")
            self.lbl_d.setStyleSheet(
                f"font-size:11px;color:{RENK_PRIMARY};font-weight:bold;")
            self._onizleme_guncelle()
        self.degisti.emit()

    def _onizleme_guncelle(self):
        try:
            s = AkisSahne()
            s.yukle(self._data)
            png = s.png_render(dpi=72)
            pix = QPixmap(); pix.loadFromData(png)
            if not pix.isNull():
                scaled = pix.scaledToWidth(
                    min(self._onizleme.width() - 20, pix.width()),
                    Qt.TransformationMode.SmoothTransformation)
                self._onizleme.setPixmap(scaled)
        except Exception:
            pass

    def yukle(self, data: dict):
        self._data = data
        if data and data.get("sekiller"):
            n = len(data["sekiller"])
            self.lbl_d.setText(f"{n} şekil")
            self.lbl_d.setStyleSheet(
                f"font-size:11px;color:{RENK_PRIMARY};font-weight:bold;")
            self._onizleme_guncelle()

    def to_data(self) -> dict:
        return self._data

    def png_binary(self, dpi=200) -> bytes:
        s = AkisSahne()
        s.yukle(self._data)
        return s.png_render(dpi)
