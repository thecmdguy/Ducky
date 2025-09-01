import os
import json
import shutil
import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QDockWidget, QVBoxLayout, QTreeWidget,
    QTreeWidgetItem, QStackedWidget, QPushButton, QGroupBox, QMessageBox, QMenu,
    QFileDialog, QApplication, QInputDialog, QStyleFactory, QSplashScreen
)
from PySide6.QtGui import QIcon, QPixmap, QColor, QFont
from PySide6.QtCore import Qt, Slot, QPoint

from ducky_app.core.config_manager import ConfigManager
from ducky_app.core.session_manager import SessionManager
from ducky_app.ui.dialogs import SettingsDialog
from ducky_app.ui.widgets import (
    SerialTerminalWidget, SubnetCalculatorWidget, NetworkPerformanceMonitorWidget,
    PortScannerWidget, NotepadWidget
)
from ducky_app.ui.themes import DARK_THEME_QSS, LIGHT_THEME_QSS
from ducky_app.utils.helpers import check_dependencies

class DuckyMainWindow(QMainWindow):
    def __init__(self, icon_path=""):
        super().__init__()
        self.initialized_successfully = False

        # --- Splash Screen & Dependency Check ---
        app = QApplication.instance()
        splash = self._create_splash_screen()
        if not check_dependencies(splash):
            splash.close()
            return # Stop initialization if dependencies are missing
        
        # --- Main Initialization ---
        self.setWindowTitle("Ducky: Ultimate Networking Tool")
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
        """Creates and shows a splash screen immediately."""
        splash_pix = QPixmap(400, 200)
        splash_pix.fill(QColor("#fec301")) # Ducky Yellow
        splash = QSplashScreen(splash_pix)
        splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint) 
        splash.setFont(QFont("Sans Serif", 12))
        splash.show()
        QApplication.instance().processEvents() # Ensure it's drawn
        return splash

    def _create_left_panel(self):
        self.left_dock = QDockWidget("Ducky Functions", self)
        self.left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        panel_widget = QWidget()
        layout = QVBoxLayout(panel_widget)

        self.toggle_notes_button = QPushButton("Toggle Notes")
        self.toggle_notes_button.setCheckable(True)
        self.toggle_notes_button.clicked.connect(self._toggle_notepad_visibility)
        layout.addWidget(self.toggle_notes_button)
        layout.addSpacing(10)

        self.sessions_group_box = QGroupBox("Sessions")
        sessions_layout = QVBoxLayout(self.sessions_group_box)
        self.session_tree = QTreeWidget()
        self.session_tree.setHeaderHidden(True)
        self.session_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.session_tree.itemClicked.connect(self._on_session_tree_item_clicked)
        self.session_tree.customContextMenuRequested.connect(self._open_session_tree_context_menu)
        sessions_layout.addWidget(self.session_tree)
        layout.addWidget(self.sessions_group_box)
        layout.addSpacing(10)

        self.tools_group_box = QGroupBox("Tools")
        tools_layout = QVBoxLayout(self.tools_group_box)
        self.tools_tree = QTreeWidget()
        self.tools_tree.setHeaderHidden(True)
        self.tools_tree.itemClicked.connect(self._on_tool_tree_item_clicked)
        tools_layout.addWidget(self.tools_tree)
        layout.addWidget(self.tools_group_box)
        layout.addStretch()

        self.left_dock.setWidget(panel_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

    def _create_central_content_area(self):
        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)

        self.serial_widget = SerialTerminalWidget(self.config_manager)
        self.subnet_widget = SubnetCalculatorWidget()
        self.monitor_widget = NetworkPerformanceMonitorWidget()
        self.scanner_widget = PortScannerWidget()
        
        self.content_stack.addWidget(self.serial_widget)
        self.content_stack.addWidget(self.subnet_widget)
        self.content_stack.addWidget(self.monitor_widget)
        self.content_stack.addWidget(self.scanner_widget)

        self.serial_widget.serial_connected.connect(self._update_session_save_menu)

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
        serial_menu = file_menu.addMenu("Serial")
        serial_menu.addAction("Open Port...", self.serial_widget._open_serial_dialog)
        self.close_port_action = serial_menu.addAction("Close Port", self.serial_widget._disconnect_serial)
        self.save_session_action = serial_menu.addAction("Save Session As...", self._save_current_session)
        self._update_session_save_menu(False)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        tools_menu = menu_bar.addMenu("&Tools")
        tools_menu.addAction("Serial Terminal").triggered.connect(lambda: self.content_stack.setCurrentWidget(self.serial_widget))
        tools_menu.addAction("Subnet Calculator").triggered.connect(lambda: self.content_stack.setCurrentWidget(self.subnet_widget))
        tools_menu.addAction("Network Monitor").triggered.connect(lambda: self.content_stack.setCurrentWidget(self.monitor_widget))
        tools_menu.addAction("Port Scanner").triggered.connect(lambda: self.content_stack.setCurrentWidget(self.scanner_widget))

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

        serial_root = QTreeWidgetItem(self.session_tree, ["Serial Sessions"])
        serial_root.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "path": self.session_manager.get_session_dir(), "is_root": True})
        serial_root.setExpanded(True)
        self._populate_sessions(serial_root, self.session_manager.get_session_dir())

        self._add_tool_item("Connect Serial", {"type": "action", "action": "open_serial"})
        self._add_tool_item("Subnet Calculator", {"type": "tool", "widget": self.subnet_widget})
        self._add_tool_item("Network Monitor", {"type": "tool", "widget": self.monitor_widget})
        self._add_tool_item("Port Scanner", {"type": "tool", "widget": self.scanner_widget})
        self.tools_tree.expandAll()

    def _add_tool_item(self, name, data):
        item = QTreeWidgetItem(self.tools_tree, [name])
        item.setData(0, Qt.ItemDataRole.UserRole, data)

    def _populate_sessions(self, parent_item, path):
        try:
            for entry in sorted(os.listdir(path)):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    folder_item = QTreeWidgetItem(parent_item, [entry])
                    folder_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "path": full_path})
                    self._populate_sessions(folder_item, full_path)
                elif entry.endswith(".json"):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        if "log_path" in meta and os.path.exists(meta["log_path"]):
                            session_item = QTreeWidgetItem(parent_item, [meta["name"]])
                            session_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "session", "log_path": meta["log_path"], "meta_path": full_path})
                    except Exception as e:
                        print(f"Could not load session meta: {entry}, error: {e}")
        except FileNotFoundError:
            print(f"Session directory not found: {path}")

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
        if not data: return
        if data.get("type") == "session":
            log_content = self.session_manager.load_session_log(data["log_path"])
            self.serial_widget.load_log_for_display(log_content)
            self.content_stack.setCurrentWidget(self.serial_widget)
        elif data.get("type") == "folder":
            item.setExpanded(not item.isExpanded())

    @Slot(QPoint)
    def _open_session_tree_context_menu(self, position):
        item = self.session_tree.itemAt(position)
        menu = QMenu(self)
        data = item.data(0, Qt.ItemDataRole.UserRole) if item else None

        if data:
            if data["type"] == "folder":
                menu.addAction("New Folder...", lambda: self._create_new_folder(item))
                if not data.get("is_root"):
                    menu.addAction("Rename Folder...", lambda: self._rename_tree_item(item))
                    menu.addAction("Delete Folder", lambda: self._delete_tree_item(item))
            elif data["type"] == "session":
                menu.addAction("Rename Session...", lambda: self._rename_tree_item(item))
                menu.addAction("Delete Session", lambda: self._delete_tree_item(item))
        else: # Clicked on empty space
             serial_root = self.session_tree.topLevelItem(0)
             if serial_root:
                 menu.addAction("New Folder in Root...", lambda: self._create_new_folder(serial_root))

        menu.exec(self.session_tree.mapToGlobal(position))

    def _create_new_folder(self, parent_item):
        path = parent_item.data(0, Qt.ItemDataRole.UserRole)["path"]
        name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and name:
            success, msg = self.session_manager.create_session_folder(path, name)
            if success: 
                self._load_tree_structure()
            else: 
                QMessageBox.warning(self, "Error", msg)

    def _rename_tree_item(self, item):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        try:
            if data['type'] == 'folder':
                old_name = os.path.basename(data['path'])
                new_name, ok = QInputDialog.getText(self, f"Rename Folder", f"Enter new name for '{old_name}':", text=old_name)
                if not (ok and new_name and new_name != old_name): return
                os.rename(data['path'], os.path.join(os.path.dirname(data['path']), new_name))
            elif data['type'] == 'session':
                with open(data['meta_path'], 'r', encoding='utf-8') as f: meta = json.load(f)
                old_name = meta['name']
                new_name, ok = QInputDialog.getText(self, f"Rename Session", f"Enter new name for '{old_name}':", text=old_name)
                if not (ok and new_name and new_name != old_name): return
                meta['name'] = new_name
                with open(data['meta_path'], 'w', encoding='utf-8') as f: json.dump(meta, f, indent=4)
            self._load_tree_structure()
        except Exception as e:
            QMessageBox.critical(self, "Rename Error", f"Could not rename item: {e}")
        
    def _delete_tree_item(self, item):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        name = item.text(0)
        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to permanently delete '{name}'?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if data['type'] == 'folder':
                    shutil.rmtree(data['path'])
                elif data['type'] == 'session':
                    os.remove(data['log_path'])
                    os.remove(data['meta_path'])
                self._load_tree_structure()
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Could not delete item: {e}")

    @Slot(QTreeWidgetItem, int)
    def _on_tool_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data: return
        if data.get("type") == "tool":
            self.content_stack.setCurrentWidget(data["widget"])
        elif data.get("type") == "action" and data["action"] == "open_serial":
            self.content_stack.setCurrentWidget(self.serial_widget)
            self.serial_widget._open_serial_dialog()

    @Slot(bool)
    def _update_session_save_menu(self, is_connected: bool):
        self.save_session_action.setEnabled(is_connected)
        self.close_port_action.setEnabled(is_connected)
        if is_connected: self.content_stack.setCurrentWidget(self.serial_widget)

    @Slot()
    def _save_current_session(self):
        log_data = self.serial_widget.get_current_log_data()
        if not log_data: 
            QMessageBox.warning(self, "Save Session", "No data to save.")
            return
        
        folder = QFileDialog.getExistingDirectory(self, "Select Save Location", self.session_manager.get_session_dir())
        if not folder: return

        name, ok = QInputDialog.getText(self, "Save Session", "Enter session name:")
        if ok and name:
            meta = self.serial_widget.get_current_session_metadata()
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
        QMessageBox.about(self, "About Ducky", "<h2>Ducky: Ultimate Networking Tool</h2><p>Version 1.0. A multi-tool for network engineers.</p>")

    def apply_current_settings(self):
        theme = self.config_manager.get_setting("app_theme")
        QApplication.instance().setStyleSheet(DARK_THEME_QSS if theme == "dark" else LIGHT_THEME_QSS)
        
        settings_dict = self.config_manager._config
        for widget in [self.serial_widget, self.subnet_widget, self.monitor_widget, self.scanner_widget]:
            widget.apply_settings(settings_dict)
        
        if self.session_manager.base_session_dir != self.config_manager.get_setting("session_folder"):
             self.session_manager.base_session_dir = self.config_manager.get_setting("session_folder")
             os.makedirs(self.session_manager.base_session_dir, exist_ok=True)
             self._load_tree_structure()

    def closeEvent(self, event):
        self.serial_widget._disconnect_serial()
        if self.monitor_widget.tool_thread: self.monitor_widget._stop_network_tool()
        if self.scanner_widget.scan_thread: self.scanner_widget._stop_port_scan()
        self.notepad_widget.save_and_stop()
        self.config_manager.save_config()
        event.accept()