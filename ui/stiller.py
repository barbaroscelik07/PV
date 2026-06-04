"""
PV-DOC — Stil Sabitleri
Tüm renk, font ve stil tanımları buradadır.
"""

# Ana renkler
RENK_PRIMARY = "#185FA5"
RENK_PRIMARY_KOYU = "#0C447C"
RENK_PRIMARY_ACIK = "#E6F1FB"
RENK_PRIMARY_ORTA = "#B5D4F4"

RENK_YESIL = "#3B6D11"
RENK_YESIL_BG = "#EAF3DE"
RENK_TURUNCU = "#633806"
RENK_TURUNCU_BG = "#FAEEDA"
RENK_KIRMIZI = "#A32D2D"
RENK_KIRMIZI_BG = "#FCEBEB"

RENK_BG_BIRINCIL = "#FFFFFF"
RENK_BG_IKINCIL = "#F8F8F8"
RENK_BG_UCUNCUL = "#F2F2F2"

RENK_YAZI_BIRINCIL = "#1A1A1A"
RENK_YAZI_IKINCIL = "#555555"
RENK_YAZI_UCUNCUL = "#999999"

RENK_KENARLIK = "#E0E0E0"
RENK_KENARLIK_KOYU = "#C8C8C8"

FONT_AILESI = "Arial"
FONT_BOYUT_KUCUK = 9
FONT_BOYUT_NORMAL = 11
FONT_BOYUT_ORTA = 12
FONT_BOYUT_BUYUK = 13
FONT_BOYUT_BASLIK = 15

ANA_STIL = f"""
QMainWindow {{
    background-color: {RENK_BG_UCUNCUL};
}}

QWidget {{
    font-family: {FONT_AILESI};
    font-size: {FONT_BOYUT_NORMAL}px;
    color: {RENK_YAZI_BIRINCIL};
}}

QLabel {{
    color: {RENK_YAZI_BIRINCIL};
    background-color: transparent;
}}

QLineEdit {{
    border: 1px solid {RENK_KENARLIK};
    border-radius: 6px;
    padding: 4px 8px;
    background-color: {RENK_BG_BIRINCIL};
    color: {RENK_YAZI_BIRINCIL};
    font-size: {FONT_BOYUT_NORMAL}px;
    min-height: 28px;
}}
QLineEdit:focus {{
    border: 1px solid {RENK_PRIMARY};
}}
QLineEdit:disabled {{
    background-color: {RENK_BG_IKINCIL};
    color: {RENK_YAZI_UCUNCUL};
}}

QTextEdit, QPlainTextEdit {{
    border: 1px solid {RENK_KENARLIK};
    border-radius: 6px;
    padding: 5px 8px;
    background-color: {RENK_BG_BIRINCIL};
    color: {RENK_YAZI_BIRINCIL};
    font-size: {FONT_BOYUT_NORMAL}px;
}}
QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {RENK_PRIMARY};
}}

QComboBox {{
    border: 1px solid {RENK_KENARLIK};
    border-radius: 6px;
    padding: 4px 8px;
    background-color: {RENK_BG_BIRINCIL};
    color: {RENK_YAZI_BIRINCIL};
    font-size: {FONT_BOYUT_NORMAL}px;
    min-height: 28px;
}}
QComboBox:focus {{
    border: 1px solid {RENK_PRIMARY};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    border: 1px solid {RENK_KENARLIK};
    border-radius: 4px;
    background-color: {RENK_BG_BIRINCIL};
    selection-background-color: {RENK_PRIMARY_ACIK};
    selection-color: {RENK_PRIMARY_KOYU};
}}

QSpinBox {{
    border: 1px solid {RENK_KENARLIK};
    border-radius: 6px;
    padding: 4px 8px;
    background-color: {RENK_BG_BIRINCIL};
    font-size: {FONT_BOYUT_NORMAL}px;
    min-height: 28px;
}}
QSpinBox:focus {{
    border: 1px solid {RENK_PRIMARY};
}}

QCheckBox {{
    font-size: {FONT_BOYUT_NORMAL}px;
    color: {RENK_YAZI_BIRINCIL};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border: 1px solid {RENK_KENARLIK};
    border-radius: 3px;
    background-color: {RENK_BG_BIRINCIL};
}}
QCheckBox::indicator:checked {{
    background-color: {RENK_PRIMARY};
    border-color: {RENK_PRIMARY};
    image: none;
}}
QCheckBox::indicator:checked {{
    background-color: {RENK_PRIMARY};
    border-color: {RENK_PRIMARY};
}}

QPushButton {{
    border: 1px solid {RENK_KENARLIK};
    border-radius: 6px;
    padding: 5px 14px;
    background-color: {RENK_BG_BIRINCIL};
    color: {RENK_YAZI_IKINCIL};
    font-size: {FONT_BOYUT_NORMAL}px;
    font-family: {FONT_AILESI};
    min-height: 28px;
}}
QPushButton:hover {{
    background-color: {RENK_BG_IKINCIL};
    border-color: {RENK_KENARLIK_KOYU};
}}
QPushButton:pressed {{
    background-color: {RENK_BG_UCUNCUL};
}}
QPushButton:disabled {{
    color: {RENK_YAZI_UCUNCUL};
    border-color: {RENK_KENARLIK};
}}

QPushButton#btnPrimary {{
    background-color: {RENK_PRIMARY};
    border-color: {RENK_PRIMARY};
    color: white;
    font-weight: bold;
}}
QPushButton#btnPrimary:hover {{
    background-color: {RENK_PRIMARY_KOYU};
    border-color: {RENK_PRIMARY_KOYU};
}}

QPushButton#btnDanger {{
    background-color: {RENK_KIRMIZI_BG};
    border-color: {RENK_KIRMIZI};
    color: {RENK_KIRMIZI};
}}
QPushButton#btnDanger:hover {{
    background-color: {RENK_KIRMIZI};
    color: white;
}}

QPushButton#btnLink {{
    border: none;
    background: transparent;
    color: {RENK_PRIMARY};
    padding: 3px 6px;
    text-decoration: underline;
    min-height: 20px;
}}
QPushButton#btnLink:hover {{
    color: {RENK_PRIMARY_KOYU};
}}

QTabWidget::pane {{
    border: 1px solid {RENK_KENARLIK};
    border-radius: 0 6px 6px 6px;
    background-color: {RENK_BG_BIRINCIL};
}}
QTabBar::tab {{
    border: 1px solid {RENK_KENARLIK};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 6px 14px;
    font-size: {FONT_BOYUT_NORMAL}px;
    color: {RENK_YAZI_IKINCIL};
    background-color: {RENK_BG_IKINCIL};
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {RENK_BG_BIRINCIL};
    color: {RENK_PRIMARY};
    font-weight: bold;
    border-color: {RENK_KENARLIK};
}}
QTabBar::tab:hover:!selected {{
    background-color: {RENK_BG_BIRINCIL};
}}

QTableWidget {{
    border: 1px solid {RENK_KENARLIK};
    border-radius: 6px;
    gridline-color: {RENK_KENARLIK};
    background-color: {RENK_BG_BIRINCIL};
    font-size: {FONT_BOYUT_NORMAL}px;
    alternate-background-color: {RENK_BG_IKINCIL};
}}
QTableWidget::item {{
    padding: 3px 6px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {RENK_PRIMARY_ACIK};
    color: {RENK_PRIMARY_KOYU};
}}
QHeaderView::section {{
    background-color: {RENK_BG_IKINCIL};
    border: none;
    border-right: 1px solid {RENK_KENARLIK};
    border-bottom: 1px solid {RENK_KENARLIK};
    padding: 5px 8px;
    font-size: {FONT_BOYUT_KUCUK}px;
    font-weight: bold;
    color: {RENK_YAZI_IKINCIL};
}}

QScrollBar:vertical {{
    border: none;
    background: {RENK_BG_IKINCIL};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {RENK_KENARLIK_KOYU};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {RENK_YAZI_UCUNCUL};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    border: none;
    background: {RENK_BG_IKINCIL};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {RENK_KENARLIK_KOYU};
    border-radius: 4px;
    min-width: 20px;
}}

QSplitter::handle {{
    background-color: {RENK_KENARLIK};
    width: 1px;
}}

QGroupBox {{
    border: 1px solid {RENK_KENARLIK};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 8px;
    font-size: {FONT_BOYUT_NORMAL}px;
    font-weight: bold;
    color: {RENK_YAZI_IKINCIL};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: {RENK_PRIMARY};
}}

QFrame#cardFrame {{
    background-color: {RENK_BG_BIRINCIL};
    border: 1px solid {RENK_KENARLIK};
    border-radius: 10px;
}}

QFrame#sectionHeader {{
    background-color: {RENK_BG_IKINCIL};
    border: none;
    border-bottom: 1px solid {RENK_KENARLIK};
    border-radius: 0px;
}}

QListWidget {{
    border: 1px solid {RENK_KENARLIK};
    border-radius: 6px;
    background-color: {RENK_BG_BIRINCIL};
    font-size: {FONT_BOYUT_NORMAL}px;
    outline: none;
}}
QListWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid {RENK_KENARLIK};
}}
QListWidget::item:selected {{
    background-color: {RENK_PRIMARY_ACIK};
    color: {RENK_PRIMARY_KOYU};
}}
QListWidget::item:hover {{
    background-color: {RENK_BG_IKINCIL};
}}

QStatusBar {{
    background-color: {RENK_BG_BIRINCIL};
    border-top: 1px solid {RENK_KENARLIK};
    font-size: {FONT_BOYUT_KUCUK}px;
    color: {RENK_YAZI_UCUNCUL};
}}

QToolTip {{
    background-color: {RENK_YAZI_BIRINCIL};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: {FONT_BOYUT_KUCUK}px;
}}

QMessageBox {{
    background-color: {RENK_BG_BIRINCIL};
}}
"""


def get_kart_stil() -> str:
    return f"""
        background-color: {RENK_BG_BIRINCIL};
        border: 1px solid {RENK_KENARLIK};
        border-radius: 10px;
    """


def get_baslik_stil() -> str:
    return f"""
        background-color: {RENK_BG_IKINCIL};
        border-bottom: 1px solid {RENK_KENARLIK};
        padding: 8px 14px;
    """


def get_badge_stil(renk: str = "blue") -> str:
    renkler = {
        "blue": (RENK_PRIMARY_ACIK, RENK_PRIMARY_KOYU),
        "green": (RENK_YESIL_BG, RENK_YESIL),
        "orange": (RENK_TURUNCU_BG, RENK_TURUNCU),
        "red": (RENK_KIRMIZI_BG, RENK_KIRMIZI),
    }
    bg, fg = renkler.get(renk, renkler["blue"])
    return f"""
        background-color: {bg};
        color: {fg};
        border-radius: 8px;
        padding: 2px 8px;
        font-size: {FONT_BOYUT_KUCUK}px;
    """
