# -*- coding: utf-8 -*-
"""界面主题:取自三虎的配色——白毛、深灰虎纹、橙色眼睛、金色铃铛、粉色肉垫。
样式使用 Qt 原生样式表(QSS),属于 Qt Widgets 的原生机制,不涉及网页技术。"""
INK = '#2B2D36'
STRIPE = '#3B3E48'
BG = '#F6F4F0'
CARD = '#FFFFFF'
LINE = '#E7E3DC'
SUB = '#7C808C'
ACCENT = '#E8571E'
ACCENT2 = '#F08A3C'
GOLD = '#F2C230'
PINK = '#F2A7A0'
GREEN = '#4FA36B'
BLUE = '#5B8DEF'

QSS = f"""
* {{ font-size: 13px; color: {INK}; }}
QWidget#root, QDialog {{ background: {BG}; }}
QWidget#sidebar {{ background: {INK}; }}
QWidget#sidebar QLabel {{ color: #FFFFFF; }}
QLabel#brand {{ font-size: 17px; font-weight: 700; color: #FFFFFF; }}
QLabel#brandSub {{ color: #A9ADB8; font-size: 11px; }}
QPushButton#nav {{ text-align: left; padding: 10px 16px; border: none; border-radius: 10px;
    color: #C9CCD4; background: transparent; font-size: 14px; }}
QPushButton#nav:hover {{ background: {STRIPE}; color: #FFFFFF; }}
QPushButton#nav:checked {{ background: {ACCENT}; color: #FFFFFF; font-weight: 600; }}
QLabel#h1 {{ font-size: 22px; font-weight: 700; }}
QLabel#h2 {{ font-size: 15px; font-weight: 600; }}
QLabel#sub {{ color: {SUB}; }}
QLabel#big {{ font-size: 44px; font-weight: 700; }}
QFrame#card {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 14px; }}
QFrame#row {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 12px; }}
QFrame#row:hover {{ border-color: {ACCENT2}; }}
QLineEdit, QSpinBox, QTimeEdit, QDateEdit, QComboBox {{ background: #FFFFFF; border: 1px solid {LINE};
    border-radius: 9px; padding: 7px 10px; selection-background-color: {ACCENT2}; min-height: 20px; }}
QLineEdit:focus, QSpinBox:focus, QTimeEdit:focus, QDateEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down, QDateEdit::drop-down {{ border: none; width: 22px; }}
QTimeEdit::up-button, QTimeEdit::down-button, QSpinBox::up-button, QSpinBox::down-button {{ width: 0; border: none; }}
QLabel#avatar {{ background: #FFFFFF; border-radius: 22px; }}
QComboBox QAbstractItemView {{ background: #FFFFFF; border: 1px solid {LINE}; selection-background-color: {ACCENT2};
    selection-color: #FFFFFF; outline: 0; }}
QPushButton {{ background: #FFFFFF; border: 1px solid {LINE}; border-radius: 9px; padding: 8px 16px; }}
QPushButton:hover {{ border-color: {ACCENT2}; color: {ACCENT}; }}
QPushButton:pressed {{ background: #FBEDE4; }}
QPushButton#primary {{ background: {ACCENT}; border: 1px solid {ACCENT}; color: #FFFFFF; font-weight: 600; }}
QPushButton#primary:hover {{ background: {ACCENT2}; border-color: {ACCENT2}; color: #FFFFFF; }}
QPushButton#primary:disabled {{ background: #E9C9B8; border-color: #E9C9B8; }}
QPushButton#ghost {{ border: none; background: transparent; color: {SUB}; padding: 4px 8px; }}
QPushButton#ghost:hover {{ color: {ACCENT}; }}
QPushButton#chip {{ border-radius: 14px; padding: 6px 14px; background: #FFFFFF; }}
QPushButton#chip:checked {{ background: {INK}; color: #FFFFFF; border-color: {INK}; }}
QPushButton#fmt {{ border-radius: 10px; padding: 10px 6px; font-weight: 600; min-width: 62px; }}
QPushButton#fmt:hover {{ background: {ACCENT}; color: #FFFFFF; border-color: {ACCENT}; }}
QCheckBox {{ spacing: 8px; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #D6D2CA; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QListWidget {{ background: #FFFFFF; border: 1px solid {LINE}; border-radius: 10px; padding: 4px; outline: 0; }}
QListWidget::item {{ padding: 8px; border-radius: 7px; }}
QListWidget::item:selected {{ background: {ACCENT2}; color: #FFFFFF; }}
QMenu {{ background: #FFFFFF; border: 2px solid {INK}; border-radius: 12px; padding: 6px; }}
QMenu::item {{ padding: 8px 26px 8px 14px; border-radius: 8px; color: {INK}; font-size: 13px; }}
QMenu::item:selected {{ background: {ACCENT}; color: #FFFFFF; }}
QMenu::separator {{ height: 1px; background: {LINE}; margin: 5px 8px; }}
QToolTip {{ background: {INK}; color: #FFFFFF; border: none; padding: 4px 8px; }}
QCalendarWidget QWidget {{ alternate-background-color: {BG}; }}
"""
