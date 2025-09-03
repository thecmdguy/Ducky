import os
import json
import shutil
import serial
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QDockWidget, QVBoxLayout, QTreeWidget,
    QTreeWidgetItem, QPushButton, QGroupBox, QMessageBox, QMenu,
    QFileDialog, QApplication, QInputDialog, QStyleFactory, QSplashScreen, QTabWidget,
    QStackedWidget
)
from PySide6.QtGui import QIcon, QPixmap, QColor, QFont, QPainter
from PySide6.QtCore import Qt, Slot, QPoint

from ducky_app.core.config_manager import ConfigManager
from ducky_app.core.session_manager import SessionManager
from ducky_app.ui.dialogs import ConnectionDialog, SettingsDialog
from ducky_app.ui.widgets import (
    BaseTerminalWidget, SubnetCalculatorWidget, NetworkPerformanceMonitorWidget,
    PortScannerWidget, NotepadWidget, TopologyMapperWidget, VulnerabilityScannerWidget,
    PasswordCheckerWidget, HashToolWidget
)
from ducky_app.ui.themes import DARK_THEME_QSS, LIGHT_THEME_QSS
from ducky_app.utils.helpers import check_dependencies

class DuckyMainWindow(QMainWindow):
    def __init__(self, icon_path="", parent=None):
        super().__init__(parent)
        self.initialized_successfully = False
        app = QApplication.instance()
        splash = self._create_splash_screen()
        if not check_dependencies(splash):
            splash.close()
            return
        
        self.setWindowTitle("Ducky: Ultimate Networking & Security Tool")
        self.setGeometry(100, 100, 1200, 800)
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.config_manager = ConfigManager()
        self.session_manager = SessionManager(self.config_manager)
        app.setStyle(QStyleFactory.create("Fusion"))
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self._create_left_panel()
        self._create_central_content_area()
        self._create_notepad_dock()
        self._create_menu_bar()
        self._create_status_bar()

        self._load_tree_structure()
        self.apply_current_settings()
        
        splash.finish(self)
        self.initialized_successfully = True

    def _create_splash_screen(self):
        splash_image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'splash.png')
        
        splash = None
        if os.path.exists(splash_image_path):
            splash_pixmap = QPixmap(splash_image_path)
            splash = QSplashScreen(splash_pixmap)
            splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            splash.setStyleSheet("QLabel { color: white; }") # Set status text color
        else:
            splash = QSplashScreen()
            splash.showMessage("Loading...", Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)

        status_font = QFont("Sans Serif", 10)
        splash.setFont(status_font)

        splash.show()
        QApplication.instance().processEvents()
        return splash

    def _create_left_panel(self):
        self.left_dock = QDockWidget("Ducky Functions", self)
        self.left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        panel_widget = QWidget()
        layout = QVBoxLayout(panel_widget)
        
        self.connections_group_box = QGroupBox("Connections")
        connections_layout = QVBoxLayout(self.connections_group_box)
        self.new_connection_btn = QPushButton("New Terminal Tab...")
        self.new_connection_btn.clicked.connect(self._open_new_terminal_dialog)
        connections_layout.addWidget(self.new_connection_btn)
        layout.addWidget(self.connections_group_box)
        layout.addSpacing(10)

        self.sessions_group_box = QGroupBox("Saved Sessions")
        sessions_layout = QVBoxLayout(self.sessions_group_box)
        self.session_tree = QTreeWidget()
        self.session_tree.setHeaderHidden(True)
        self.session_tree.itemDoubleClicked.connect(self._on_session_tree_item_clicked)
        sessions_layout.addWidget(self.session_tree)
        layout.addWidget(self.sessions_group_box)
        
        self.tools_group_box = QGroupBox("Tools")
        tools_layout = QVBoxLayout(self.tools_group_box)
        self.tools_tree = QTreeWidget()
        self.tools_tree.setHeaderHidden(True)
        self.tools_tree.itemClicked.connect(self._on_tool_tree_item_clicked)
        tools_layout.addWidget(self.tools_tree)
        layout.addWidget(self.tools_group_box)
        layout.addStretch(1)

        self.toggle_notes_button = QPushButton("Toggle Notes")
        self.toggle_notes_button.setCheckable(True)
        self.toggle_notes_button.clicked.connect(self._toggle_notepad_visibility)
        layout.addWidget(self.toggle_notes_button)
        
        self.left_dock.setWidget(panel_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

    def _create_central_content_area(self):
        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)

        self.terminal_tab_widget = QTabWidget()
        self.terminal_tab_widget.setTabsClosable(True)
        self.terminal_tab_widget.setMovable(True)
        self.terminal_tab_widget.tabCloseRequested.connect(self.close_terminal_tab)
        self.content_stack.addWidget(self.terminal_tab_widget)

        self.subnet_widget = SubnetCalculatorWidget()
        self.monitor_widget = NetworkPerformanceMonitorWidget()
        self.scanner_widget = PortScannerWidget()
        self.topology_widget = TopologyMapperWidget()
        self.cve_scanner_widget = VulnerabilityScannerWidget()
        self.password_widget = PasswordCheckerWidget()
        self.hash_widget = HashToolWidget()

        self.content_stack.addWidget(self.subnet_widget)
        self.content_stack.addWidget(self.monitor_widget)
        self.content_stack.addWidget(self.scanner_widget)
        self.content_stack.addWidget(self.topology_widget)
        self.content_stack.addWidget(self.cve_scanner_widget)
        self.content_stack.addWidget(self.password_widget)
        self.content_stack.addWidget(self.hash_widget)

    def _create_notepad_dock(self):
        self.notepad_dock = QDockWidget("Scratchpad Notes", self)
        self.notepad_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.notepad_widget = NotepadWidget(self.config_manager)
        self.notepad_dock.setWidget(self.notepad_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.notepad_dock)
        self.notepad_dock.setVisible(False)
        self.notepad_dock.visibilityChanged.connect(self._update_notepad_menu_action_state)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        serial_menu = file_menu.addMenu("Terminal")
        serial_menu.addAction("New Tab (Serial/SSH/Telnet)", self._open_new_terminal_dialog)
        self.save_session_action = serial_menu.addAction("Save Current Tab As...", self._save_current_session)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        view_menu = menu_bar.addMenu("&View")
        self.toggle_notepad_action = view_menu.addAction("Toggle Scratchpad Notes")
        self.toggle_notepad_action.setCheckable(True)
        self.toggle_notepad_action.triggered.connect(self._toggle_notepad_visibility)
        settings_menu = menu_bar.addMenu("&Settings")
        settings_menu.addAction("Preferences...", self._open_settings_dialog)
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("About", self._show_about_dialog)

    def _create_status_bar(self):
        self.statusBar().showMessage("Ready")

    def _load_tree_structure(self):
        self.session_tree.clear()
        self.tools_tree.clear()
        
        sessions_root = QTreeWidgetItem(self.session_tree, ["Saved Sessions"])
        sessions_root.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "path": self.session_manager.get_session_dir(), "is_root": True})
        self._populate_sessions(sessions_root)
        self.session_tree.expandItem(sessions_root)
        
        self._add_tool_item(self.tools_tree, "Terminal", {"type": "view", "widget": self.terminal_tab_widget})

        net_tools_item = self._add_tool_item(self.tools_tree, "Network Tools", {"type": "category"})
        self._add_tool_item(net_tools_item, "Subnet Calculator", {"type": "view", "widget": self.subnet_widget})
        self._add_tool_item(net_tools_item, "Network Monitor", {"type": "view", "widget": self.monitor_widget})
        self._add_tool_item(net_tools_item, "Port Scanner", {"type": "view", "widget": self.scanner_widget})
        self._add_tool_item(net_tools_item, "Topology Mapper", {"type": "view", "widget": self.topology_widget})

        sec_tools_item = self._add_tool_item(self.tools_tree, "Security Tools", {"type": "category"})
        self._add_tool_item(sec_tools_item, "Vulnerability Scanner", {"type": "view", "widget": self.cve_scanner_widget})
        self._add_tool_item(sec_tools_item, "Password Checker", {"type": "view", "widget": self.password_widget})
        self._add_tool_item(sec_tools_item, "Hash Calculator", {"type": "view", "widget": self.hash_widget})
        
        self.tools_tree.expandAll()

    def _add_tool_item(self, parent, name, data):
        item = QTreeWidgetItem(parent, [name])
        item.setData(0, Qt.ItemDataRole.UserRole, data)
        return item

    def _populate_sessions(self, parent_item):
        path = parent_item.data(0, Qt.ItemDataRole.UserRole)["path"]
        try:
            for entry in sorted(os.listdir(path)):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    folder_item = QTreeWidgetItem(parent_item, [entry])
                    folder_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "path": full_path})
                    self._populate_sessions(folder_item)
                elif entry.endswith(".json"):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f: meta = json.load(f)
                        if "log_path" in meta and os.path.exists(meta["log_path"]):
                            session_item = QTreeWidgetItem(parent_item, [meta["name"]])
                            session_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "session", "name": meta["name"], "log_path": meta["log_path"]})
                    except Exception: pass
        except FileNotFoundError: pass

    def add_terminal_tab(self, terminal_widget, name):
        index = self.terminal_tab_widget.addTab(terminal_widget, name)
        self.terminal_tab_widget.setCurrentIndex(index)
        terminal_widget.apply_settings(self.config_manager._config)
        terminal_widget.setFocus()
        self.content_stack.setCurrentWidget(self.terminal_tab_widget)

    def close_terminal_tab(self, index):
        widget = self.terminal_tab_widget.widget(index)
        if isinstance(widget, BaseTerminalWidget):
            widget.disconnect_from_target()
        self.terminal_tab_widget.removeTab(index)
        widget.deleteLater()

    @Slot(bool)
    def _update_notepad_menu_action_state(self, visible: bool):
        self.toggle_notepad_action.setChecked(visible)
        self.toggle_notes_button.setChecked(visible)

    @Slot()
    def _toggle_notepad_visibility(self):
        self.notepad_dock.setVisible(not self.notepad_dock.isVisible())

    @Slot(QTreeWidgetItem, int)
    def _on_session_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "session": return
        log_content = self.session_manager.load_session_log(data["log_path"])
        terminal = BaseTerminalWidget(self.config_manager)
        terminal.load_log_for_display(log_content)
        self.add_terminal_tab(terminal, data["name"])

    @Slot(QTreeWidgetItem, int)
    def _on_tool_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data.get("type") == "view":
            self.content_stack.setCurrentWidget(data["widget"])

    @Slot()
    def _open_new_terminal_dialog(self):
        dialog = ConnectionDialog(self.config_manager, self)
        if dialog.exec():
            settings = dialog.get_settings()
            if settings:
                terminal = BaseTerminalWidget(self.config_manager)
                success, tab_name = terminal.connect_to_target(settings)
                if success:
                    self.add_terminal_tab(terminal, tab_name)

    @Slot()
    def _save_current_session(self):
        if self.content_stack.currentWidget() is not self.terminal_tab_widget:
            QMessageBox.warning(self, "Save Session", "Please select a terminal tab to save.")
            return
            
        current_terminal = self.terminal_tab_widget.currentWidget()
        if not isinstance(current_terminal, BaseTerminalWidget):
            QMessageBox.warning(self, "Save Session", "There are no open terminal tabs to save.")
            return

        log_data = current_terminal.get_current_log_data()
        if not log_data: 
            QMessageBox.warning(self, "Save Session", "No data in the current terminal to save.")
            return
        
        folder = QFileDialog.getExistingDirectory(self, "Select Save Location", self.session_manager.get_session_dir())
        if not folder: return
        name, ok = QInputDialog.getText(self, "Save Session", "Enter session name:")
        if ok and name:
            meta = current_terminal.get_current_session_metadata()
            success, msg = self.session_manager.save_session(folder, name, log_data, meta)
            if success:
                QMessageBox.information(self, "Success", f"Session saved to {msg}")
                self._load_tree_structure()
            else:
                QMessageBox.critical(self, "Error", msg)

    @Slot()
    def _open_settings_dialog(self):
        dialog = SettingsDialog(self.config_manager, self)
        dialog.settings_changed.connect(self.apply_current_settings)
        dialog.exec()

    @Slot()
    def _show_about_dialog(self):
        QMessageBox.about(self, "About Ducky", "<h2>Ducky: Ultimate Networking & Security Tool</h2><p>Version 1.5</p>")

    def apply_current_settings(self):
        theme = self.config_manager.get_setting("app_theme")
        QApplication.instance().setStyleSheet(DARK_THEME_QSS if theme == "dark" else LIGHT_THEME_QSS)
        settings_dict = self.config_manager._config

        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if isinstance(widget, QTabWidget):
                for j in range(widget.count()):
                    if tab_content := widget.widget(j):
                        if hasattr(tab_content, 'apply_settings'):
                            tab_content.apply_settings(settings_dict)
            elif hasattr(widget, 'apply_settings'):
                widget.apply_settings(settings_dict)
        
        if self.session_manager.base_session_dir != self.config_manager.get_setting("session_folder"):
             self.session_manager.base_session_dir = self.config_manager.get_setting("session_folder")
             os.makedirs(self.session_manager.base_session_dir, exist_ok=True)
             self._load_tree_structure()

    def closeEvent(self, event):
        for i in range(self.terminal_tab_widget.count()):
            widget = self.terminal_tab_widget.widget(i)
            if isinstance(widget, BaseTerminalWidget):
                widget.disconnect_from_target()
        
        self.notepad_widget.save_and_stop()
        self.config_manager.save_config()
        event.accept()