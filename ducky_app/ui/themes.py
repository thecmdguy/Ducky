# ducky_app/ui/themes.py

DUCKY_YELLOW = "#fec301"
DUCKY_YELLOW_HOVER = "#e6b100"
DUCKY_YELLOW_PRESSED = "#d1a800"

DARK_THEME_QSS = f"""
QWidget {{
    background-color: #2e3436; color: #d3d7cf;
    selection-background-color: {DUCKY_YELLOW}; selection-color: black;
}}
QMainWindow, QMenuBar, QStatusBar {{ background-color: #2e3436; color: #d3d7cf; }}
QMenuBar::item:selected {{ background-color: {DUCKY_YELLOW}; color: black; }}
QMenu {{ background-color: #2e3436; color: #d3d7cf; border: 1px solid #454d50; }}
QMenu::item:selected {{ background-color: {DUCKY_YELLOW}; color: black; }}
QDockWidget {{ background-color: #3b4042; color: #d3d7cf; border: 1px solid #454d50; }}
QDockWidget::title {{ background: #454d50; padding-left: 5px; color: #d3d7cf; }}
QTextEdit, QLineEdit, QComboBox, QSpinBox, QFontComboBox, QTableWidget {{
    background-color: #3b4042; border: 1px solid #454d50; color: #d3d7cf;
    padding: 3px; selection-background-color: {DUCKY_YELLOW};
}}
QPushButton {{
    background-color: {DUCKY_YELLOW}; color: black; border: none;
    padding: 5px 10px; border-radius: 3px;
}}
QPushButton:hover {{ background-color: {DUCKY_YELLOW_HOVER}; }}
QPushButton:pressed {{ background-color: {DUCKY_YELLOW_PRESSED}; }}
QPushButton:disabled {{ background-color: #555; color: #aaa; }}
QToolBar {{ background-color: #3b4042; border: none; spacing: 5px; }}
QToolButton {{
    background-color: #3b4042; border: 1px solid #454d50;
    border-radius: 3px; padding: 4px; color: #d3d7cf;
}}
QToolButton:hover {{ background-color: #454d50; }}
QToolButton:pressed {{ background-color: #555c60; }}
QToolButton:checked {{ background-color: {DUCKY_YELLOW}; color: black; }}
QTreeWidget {{
    background-color: #3b4042; border: 1px solid #454d50;
    border-radius: 4px; color: #d3d7cf;
}}
QTreeWidget::item:selected {{ background-color: {DUCKY_YELLOW}; color: black; }}
QGroupBox {{
    background-color: #3b4042; border: 1px solid #454d50;
    border-radius: 4px; margin-top: 2ex; color: #d3d7cf;
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    padding: 0 3px; background-color: #3b4042;
    color: {DUCKY_YELLOW}; margin-left: 5px;
}}
QHeaderView::section {{
    background-color: #454d50; color: #d3d7cf;
    padding: 4px; border: 1px solid #2e3436;
}}
QScrollBar:vertical, QScrollBar:horizontal {{
    border: 1px solid #454d50; background: #3b4042;
    width: 10px; height: 10px; margin: 0px;
}}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: {DUCKY_YELLOW}; min-height: 20px; min-width: 20px;
}}
QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page {{ border: none; background: none; }}
QTabWidget::pane {{
    border-top: 2px solid #454d50;
}}
QTabBar::tab {{
    background: #3b4042;
    border: 1px solid #454d50;
    border-bottom-color: #3b4042;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 8ex;
    padding: 4px 8px;
}}
QTabBar::tab:selected, QTabBar::tab:hover {{
    background: #454d50;
}}
QTabBar::tab:selected {{
    border-color: #454d50;
    border-bottom-color: #454d50;
}}
QTabBar::tab:!selected {{
    margin-top: 2px;
}}
"""

LIGHT_THEME_QSS = """
QWidget {
    background-color: #F0F0F0; color: #333333;
    selection-background-color: #1E90FF; selection-color: white;
}
QMainWindow, QMenuBar, QStatusBar, QDockWidget::title, QHeaderView::section {
    background-color: #E0E0E0; color: #333333;
}
QMenuBar::item:selected, QMenu::item:selected { background-color: #1E90FF; color: white; }
QMenu { background-color: #FFFFFF; color: #333333; border: 1px solid #CCCCCC; }
QDockWidget { background-color: #F8F8F8; color: #333333; border: 1px solid #CCCCCC; }
QTextEdit, QLineEdit, QComboBox, QSpinBox, QFontComboBox, QTreeWidget, QTableWidget {
    background-color: #FFFFFF; border: 1px solid #CCCCCC; color: #333333;
    padding: 3px; selection-background-color: #1E90FF; border-radius: 4px;
}
QPushButton, QToolButton:checked, QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background-color: #1E90FF; color: white;
}
QPushButton { border: none; padding: 5px 10px; border-radius: 3px; }
QPushButton:hover { background-color: #1C86EE; }
QPushButton:pressed { background-color: #1874CD; }
QPushButton:disabled { background-color: #AAAAAA; color: #EEEEEE; }
QToolBar { background-color: #E0E0E0; border: none; spacing: 5px; }
QToolButton {
    background-color: #E0E0E0; border: 1px solid #CCCCCC;
    border-radius: 3px; padding: 4px; color: #333333;
}
QToolButton:hover { background-color: #CCCCCC; }
QToolButton:pressed { background-color: #AAAAAA; }
QTreeWidget::item:selected { background-color: #1E90FF; color: white; }
QGroupBox {
    background-color: #F8F8F8; border: 1px solid #CCCCCC;
    border-radius: 4px; margin-top: 2ex; color: #333333;
}
QGroupBox::title {
    subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px;
    background-color: #F8F8F8; color: #1E90FF; margin-left: 5px;
}
QScrollBar:vertical, QScrollBar:horizontal {
    border: 1px solid #CCCCCC; background: #F8F8F8;
    width: 10px; height: 10px; margin: 0px;
}
QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page { border: none; background: none; }
QTabWidget::pane { border-top: 2px solid #CCCCCC; }
QTabBar::tab {
    background: #E0E0E0; border: 1px solid #CCCCCC; border-bottom: none;
    border-top-left-radius: 4px; border-top-right-radius: 4px;
    min-width: 8ex; padding: 4px 8px;
}
QTabBar::tab:selected, QTabBar::tab:hover { background: #F8F8F8; }
QTabBar::tab:!selected { margin-top: 2px; }
"""