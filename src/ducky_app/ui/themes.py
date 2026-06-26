DUCKY_YELLOW       = "#fec301"
DUCKY_YELLOW_HOVER = "#e6b100"
DUCKY_YELLOW_DARK  = "#b8960a"   # for use on light backgrounds

# ---------------------------------------------------------------------------
#  DARK THEME  —  Modern Minimal
#  bg: #1a1d23  |  surface: #22262e  |  border: #2e333d  |  accent: #fec301
# ---------------------------------------------------------------------------
DARK_THEME_QSS = f"""

* {{
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
    outline: none;
}}

QWidget {{
    background-color: #1a1d23;
    color: #e2e8f0;
    selection-background-color: {DUCKY_YELLOW};
    selection-color: #111111;
}}

/* ── Menu bar ─────────────────────────────────────────────────────────── */
QMainWindow {{ background-color: #1a1d23; }}

QMenuBar {{
    background-color: #1a1d23;
    color: #e2e8f0;
    border-bottom: 1px solid #2e333d;
    padding: 2px 0;
}}
QMenuBar::item {{
    padding: 4px 10px;
    border-radius: 4px;
    background: transparent;
}}
QMenuBar::item:selected {{
    background-color: {DUCKY_YELLOW};
    color: #111111;
}}
QMenu {{
    background-color: #22262e;
    color: #e2e8f0;
    border: 1px solid #2e333d;
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 28px 6px 12px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {DUCKY_YELLOW};
    color: #111111;
}}
QMenu::separator {{
    height: 1px;
    background: #2e333d;
    margin: 4px 8px;
}}

QStatusBar {{
    background-color: #1a1d23;
    color: #8892a0;
    border-top: 1px solid #2e333d;
    font-size: 9pt;
}}

/* ── Dock panels ──────────────────────────────────────────────────────── */
QDockWidget {{
    background-color: #22262e;
    color: #e2e8f0;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}
QDockWidget::title {{
    background-color: #1a1d23;
    color: #8892a0;
    padding: 7px 10px;
    border-bottom: 1px solid #2e333d;
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Text / input fields ──────────────────────────────────────────────── */
QTextEdit, QPlainTextEdit {{
    background-color: #22262e;
    border: 1px solid #2e333d;
    border-radius: 6px;
    color: #e2e8f0;
    padding: 4px;
    selection-background-color: {DUCKY_YELLOW};
    selection-color: #111111;
}}
QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {DUCKY_YELLOW};
}}

QLineEdit {{
    background-color: #22262e;
    border: 1px solid #2e333d;
    border-radius: 5px;
    color: #e2e8f0;
    padding: 5px 9px;
    selection-background-color: {DUCKY_YELLOW};
    selection-color: #111111;
}}
QLineEdit:focus     {{ border-color: {DUCKY_YELLOW}; }}
QLineEdit:read-only {{ background-color: #1a1d23; color: #8892a0; }}

QComboBox {{
    background-color: #22262e;
    border: 1px solid #2e333d;
    border-radius: 5px;
    color: #e2e8f0;
    padding: 4px 9px;
    min-height: 24px;
}}
QComboBox:focus       {{ border-color: {DUCKY_YELLOW}; }}
QComboBox::drop-down  {{ border: none; width: 20px; }}
QComboBox::down-arrow {{ image: none; }}
QComboBox QAbstractItemView {{
    background-color: #22262e;
    border: 1px solid #2e333d;
    border-radius: 5px;
    color: #e2e8f0;
    selection-background-color: {DUCKY_YELLOW};
    selection-color: #111111;
    padding: 2px;
}}

QSpinBox, QFontComboBox {{
    background-color: #22262e;
    border: 1px solid #2e333d;
    border-radius: 5px;
    color: #e2e8f0;
    padding: 4px 7px;
}}
QSpinBox:focus, QFontComboBox:focus {{ border-color: {DUCKY_YELLOW}; }}
QSpinBox::up-button, QSpinBox::down-button {{
    background: #2e333d;
    border: none;
    width: 16px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: #3a4150; }}

/* ── Buttons ──────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {DUCKY_YELLOW};
    color: #111111;
    border: none;
    padding: 6px 16px;
    border-radius: 5px;
    font-weight: 600;
}}
QPushButton:hover    {{ background-color: {DUCKY_YELLOW_HOVER}; }}
QPushButton:pressed  {{ background-color: #c8a000; }}
QPushButton:disabled {{ background-color: #2e333d; color: #8892a0; }}

QPushButton#donateButton {{
    background-color: {DUCKY_YELLOW};
    color: #111111;
    border: none;
    padding: 8px 18px;
    border-radius: 5px;
    font-weight: 700;
}}
QPushButton#donateButton:hover   {{ background-color: {DUCKY_YELLOW_HOVER}; }}
QPushButton#donateButton:pressed {{ background-color: #c8a000; }}

/* ── Toolbar ──────────────────────────────────────────────────────────── */
QToolBar {{
    background-color: #22262e;
    border: none;
    border-bottom: 1px solid #2e333d;
    spacing: 4px;
    padding: 3px 6px;
}}
QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 7px;
    color: #e2e8f0;
}}
QToolButton:hover   {{ background-color: #2e333d; }}
QToolButton:pressed {{ background-color: #353c47; }}
QToolButton:checked {{ background-color: {DUCKY_YELLOW}; color: #111111; }}

/* ── Tree widget (sidebar) ────────────────────────────────────────────── */
QTreeWidget {{
    background-color: #22262e;
    border: none;
    color: #e2e8f0;
    outline: none;
    show-decoration-selected: 1;
}}
QTreeWidget::item {{
    padding: 4px 6px;
    border-radius: 4px;
    min-height: 24px;
}}
QTreeWidget::item:hover    {{ background-color: #2e333d; }}
QTreeWidget::item:selected {{ background-color: {DUCKY_YELLOW}; color: #111111; }}
QTreeWidget::branch        {{ background-color: #22262e; }}

/* ── Table widget ─────────────────────────────────────────────────────── */
QTableWidget {{
    background-color: #22262e;
    border: 1px solid #2e333d;
    border-radius: 6px;
    color: #e2e8f0;
    gridline-color: #2e333d;
    outline: none;
}}
QTableWidget::item          {{ padding: 5px 8px; }}
QTableWidget::item:selected {{ background-color: {DUCKY_YELLOW}; color: #111111; }}
QTableWidget::item:hover    {{ background-color: #2e333d; }}

/* ── Group box ────────────────────────────────────────────────────────── */
QGroupBox {{
    background-color: #22262e;
    border: 1px solid #2e333d;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    margin-left: 10px;
    color: {DUCKY_YELLOW};
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}

/* ── Table / tree header ──────────────────────────────────────────────── */
QHeaderView::section {{
    background-color: #1a1d23;
    color: #8892a0;
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid #2e333d;
    border-right: 1px solid #2e333d;
    font-size: 8pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}}

/* ── Scrollbars ───────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: #3a4150;
    border-radius: 4px;
    min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{ background: {DUCKY_YELLOW}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: #3a4150;
    border-radius: 4px;
    min-width: 32px;
}}
QScrollBar::handle:horizontal:hover {{ background: {DUCKY_YELLOW}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}

/* ── Tab widget ───────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid #2e333d;
    border-top: none;
    background: #22262e;
    border-radius: 0 0 6px 6px;
}}
QTabBar::tab {{
    background: transparent;
    color: #8892a0;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 7px 16px;
    margin-right: 2px;
    font-weight: 500;
}}
QTabBar::tab:hover    {{ color: #e2e8f0; background: #22262e; }}
QTabBar::tab:selected {{ color: {DUCKY_YELLOW}; border-bottom: 2px solid {DUCKY_YELLOW}; background: #22262e; }}
QTabBar::tab:!selected {{ margin-top: 2px; }}

/* ── Progress bar ─────────────────────────────────────────────────────── */
QProgressBar {{
    background-color: #2e333d;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {DUCKY_YELLOW};
    border-radius: 4px;
}}

/* ── Misc ─────────────────────────────────────────────────────────────── */
QSplitter::handle {{ background: #2e333d; width: 1px; height: 1px; }}
QLabel            {{ color: #e2e8f0; background: transparent; }}
"""


# ---------------------------------------------------------------------------
#  LIGHT THEME  —  Modern Minimal
#  bg: #f0f4f8  |  surface: #ffffff  |  border: #e2e8f0  |  accent: #fec301
# ---------------------------------------------------------------------------
LIGHT_THEME_QSS = f"""

* {{
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
    outline: none;
}}

QWidget {{
    background-color: #f0f4f8;
    color: #1a202c;
    selection-background-color: {DUCKY_YELLOW};
    selection-color: #111111;
}}

/* ── Menu bar ─────────────────────────────────────────────────────────── */
QMainWindow {{ background-color: #f0f4f8; }}

QMenuBar {{
    background-color: #ffffff;
    color: #1a202c;
    border-bottom: 1px solid #e2e8f0;
    padding: 2px 0;
}}
QMenuBar::item {{
    padding: 4px 10px;
    border-radius: 4px;
    background: transparent;
}}
QMenuBar::item:selected {{ background-color: {DUCKY_YELLOW}; color: #111111; }}
QMenu {{
    background-color: #ffffff;
    color: #1a202c;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{ padding: 6px 28px 6px 12px; border-radius: 4px; }}
QMenu::item:selected {{ background-color: {DUCKY_YELLOW}; color: #111111; }}
QMenu::separator {{ height: 1px; background: #e2e8f0; margin: 4px 8px; }}

QStatusBar {{
    background-color: #ffffff;
    color: #718096;
    border-top: 1px solid #e2e8f0;
    font-size: 9pt;
}}

/* ── Dock panels ──────────────────────────────────────────────────────── */
QDockWidget {{
    background-color: #ffffff;
    color: #1a202c;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}
QDockWidget::title {{
    background-color: #f0f4f8;
    color: #718096;
    padding: 7px 10px;
    border-bottom: 1px solid #e2e8f0;
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Text / input fields ──────────────────────────────────────────────── */
QTextEdit, QPlainTextEdit {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    color: #1a202c;
    padding: 4px;
    selection-background-color: {DUCKY_YELLOW};
    selection-color: #111111;
}}
QTextEdit:focus, QPlainTextEdit:focus {{ border-color: {DUCKY_YELLOW}; }}

QLineEdit {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    color: #1a202c;
    padding: 5px 9px;
    selection-background-color: {DUCKY_YELLOW};
    selection-color: #111111;
}}
QLineEdit:focus     {{ border-color: {DUCKY_YELLOW}; }}
QLineEdit:read-only {{ background-color: #f0f4f8; color: #718096; }}

QComboBox {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    color: #1a202c;
    padding: 4px 9px;
    min-height: 24px;
}}
QComboBox:focus       {{ border-color: {DUCKY_YELLOW}; }}
QComboBox::drop-down  {{ border: none; width: 20px; }}
QComboBox::down-arrow {{ image: none; }}
QComboBox QAbstractItemView {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    color: #1a202c;
    selection-background-color: {DUCKY_YELLOW};
    selection-color: #111111;
    padding: 2px;
}}

QSpinBox, QFontComboBox {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    color: #1a202c;
    padding: 4px 7px;
}}
QSpinBox:focus, QFontComboBox:focus {{ border-color: {DUCKY_YELLOW}; }}
QSpinBox::up-button, QSpinBox::down-button {{
    background: #f0f4f8;
    border: none;
    width: 16px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: #e2e8f0; }}

/* ── Buttons ──────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {DUCKY_YELLOW};
    color: #111111;
    border: none;
    padding: 6px 16px;
    border-radius: 5px;
    font-weight: 600;
}}
QPushButton:hover    {{ background-color: {DUCKY_YELLOW_HOVER}; }}
QPushButton:pressed  {{ background-color: #c8a000; }}
QPushButton:disabled {{ background-color: #e2e8f0; color: #a0aec0; }}

QPushButton#donateButton {{
    background-color: {DUCKY_YELLOW};
    color: #111111;
    border: none;
    padding: 8px 18px;
    border-radius: 5px;
    font-weight: 700;
}}
QPushButton#donateButton:hover   {{ background-color: {DUCKY_YELLOW_HOVER}; }}
QPushButton#donateButton:pressed {{ background-color: #c8a000; }}

/* ── Toolbar ──────────────────────────────────────────────────────────── */
QToolBar {{
    background-color: #ffffff;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    spacing: 4px;
    padding: 3px 6px;
}}
QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 7px;
    color: #1a202c;
}}
QToolButton:hover   {{ background-color: #f0f4f8; border-color: #e2e8f0; }}
QToolButton:pressed {{ background-color: #e2e8f0; }}
QToolButton:checked {{ background-color: {DUCKY_YELLOW}; color: #111111; }}

/* ── Tree widget (sidebar) ────────────────────────────────────────────── */
QTreeWidget {{
    background-color: #ffffff;
    border: none;
    color: #1a202c;
    outline: none;
    show-decoration-selected: 1;
}}
QTreeWidget::item {{
    padding: 4px 6px;
    border-radius: 4px;
    min-height: 24px;
}}
QTreeWidget::item:hover    {{ background-color: #f0f4f8; }}
QTreeWidget::item:selected {{ background-color: {DUCKY_YELLOW}; color: #111111; }}
QTreeWidget::branch        {{ background-color: #ffffff; }}

/* ── Table widget ─────────────────────────────────────────────────────── */
QTableWidget {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    color: #1a202c;
    gridline-color: #e2e8f0;
    outline: none;
}}
QTableWidget::item          {{ padding: 5px 8px; }}
QTableWidget::item:selected {{ background-color: {DUCKY_YELLOW}; color: #111111; }}
QTableWidget::item:hover    {{ background-color: #f0f4f8; }}

/* ── Group box ────────────────────────────────────────────────────────── */
QGroupBox {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    margin-left: 10px;
    color: {DUCKY_YELLOW_DARK};
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}

/* ── Table / tree header ──────────────────────────────────────────────── */
QHeaderView::section {{
    background-color: #f0f4f8;
    color: #718096;
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    font-size: 8pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}}

/* ── Scrollbars ───────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: #cbd5e0;
    border-radius: 4px;
    min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{ background: {DUCKY_YELLOW}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: #cbd5e0;
    border-radius: 4px;
    min-width: 32px;
}}
QScrollBar::handle:horizontal:hover {{ background: {DUCKY_YELLOW}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}

/* ── Tab widget ───────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid #e2e8f0;
    border-top: none;
    background: #ffffff;
    border-radius: 0 0 6px 6px;
}}
QTabBar::tab {{
    background: transparent;
    color: #718096;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 7px 16px;
    margin-right: 2px;
    font-weight: 500;
}}
QTabBar::tab:hover    {{ color: #1a202c; }}
QTabBar::tab:selected {{ color: {DUCKY_YELLOW_DARK}; border-bottom: 2px solid {DUCKY_YELLOW}; background: #ffffff; }}
QTabBar::tab:!selected {{ margin-top: 2px; }}

/* ── Progress bar ─────────────────────────────────────────────────────── */
QProgressBar {{
    background-color: #e2e8f0;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {DUCKY_YELLOW};
    border-radius: 4px;
}}

/* ── Misc ─────────────────────────────────────────────────────────────── */
QSplitter::handle {{ background: #e2e8f0; width: 1px; height: 1px; }}
QLabel            {{ color: #1a202c; background: transparent; }}
"""
