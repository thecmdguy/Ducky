import os
import json
import serial
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QDockWidget, QVBoxLayout, QTreeWidget,
    QTreeWidgetItem, QPushButton, QGroupBox, QMessageBox, QLabel,
    QFileDialog, QApplication, QInputDialog, QStyleFactory, QTabWidget,
    QStackedWidget, QToolBar,
)
from PySide6.QtGui import QIcon, QFont, QDesktopServices, QAction
from PySide6.QtCore import Qt, Slot, QUrl, QSize

from ducky_app.core.config_manager import ConfigManager
from ducky_app.core.session_manager import SessionManager
from ducky_app.ui.dialogs import ConnectionDialog, SettingsDialog
from ducky_app.ui.icons import get_tool_icon
from ducky_app.ui.widgets import (
    BaseTerminalWidget, SubnetCalculatorWidget, NetworkPerformanceMonitorWidget,
    PortScannerWidget, NotepadWidget, TopologyMapperWidget, VulnerabilityScannerWidget,
    PasswordCheckerWidget, HashToolWidget, ConnectedDevicesWidget,
    DnsLookupWidget, WhoisWidget, HttpHeadersWidget, SslCheckerWidget,
    MxLookupWidget, BlacklistCheckWidget, IpInfoWidget, SmtpTestWidget,
    WakeOnLanWidget, MacVendorWidget, DnsPropagationWidget, ArpRouteTableWidget,
)
from ducky_app.ui.themes import DARK_THEME_QSS, LIGHT_THEME_QSS


class DuckyMainWindow(QMainWindow):
    def __init__(self, icon_path="", parent=None):
        super().__init__(parent)

        self.setWindowTitle("Ducky — Network & Security Toolkit")
        self.setGeometry(100, 100, 1400, 860)
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.config_manager = ConfigManager()
        self.session_manager = SessionManager(self.config_manager)
        QApplication.instance().setStyle(QStyleFactory.create("Fusion"))

        self._tool_actions: list[QAction] = []

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self._create_left_panel()
        self._create_central_content_area()
        self._create_top_toolbar()
        self._create_notepad_dock()
        self._create_menu_bar()
        self._create_status_bar()

        self._load_tree_structure()
        self.apply_current_settings()

    # ------------------------------------------------------------------
    #  Left panel — sessions only
    # ------------------------------------------------------------------
    def _create_left_panel(self):
        self.left_dock = QDockWidget("Sessions", self)
        self.left_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.left_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.new_connection_btn = QPushButton("＋  New Terminal Tab…")
        self.new_connection_btn.clicked.connect(self._open_new_terminal_dialog)
        layout.addWidget(self.new_connection_btn)

        self.sessions_group_box = QGroupBox("Saved Sessions")
        sessions_layout = QVBoxLayout(self.sessions_group_box)
        sessions_layout.setContentsMargins(4, 4, 4, 4)
        self.session_tree = QTreeWidget()
        self.session_tree.setHeaderHidden(True)
        self.session_tree.itemDoubleClicked.connect(self._on_session_tree_item_clicked)
        sessions_layout.addWidget(self.session_tree)
        layout.addWidget(self.sessions_group_box, 1)

        self.toggle_notes_button = QPushButton("Toggle Notes")
        self.toggle_notes_button.setCheckable(True)
        self.toggle_notes_button.clicked.connect(self._toggle_notepad_visibility)
        layout.addWidget(self.toggle_notes_button)

        self.donate_button = QPushButton("Support the Developer")
        self.donate_button.setObjectName("donateButton")
        self.donate_button.clicked.connect(self._open_donation_link)
        layout.addWidget(self.donate_button)

        self.left_dock.setWidget(panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

    # ------------------------------------------------------------------
    #  Central content stack
    # ------------------------------------------------------------------
    def _create_central_content_area(self):
        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)

        # Terminals (always index 0)
        self.terminal_tab_widget = QTabWidget()
        self.terminal_tab_widget.setTabsClosable(True)
        self.terminal_tab_widget.setMovable(True)
        self.terminal_tab_widget.tabCloseRequested.connect(self.close_terminal_tab)
        self.content_stack.addWidget(self.terminal_tab_widget)

        # ── Network & Diagnostics ──────────────────────────────────────
        self.monitor_widget  = NetworkPerformanceMonitorWidget()
        self.ping_widget     = self.monitor_widget          # alias (shares widget)
        self.dns_widget      = DnsLookupWidget()
        self.mx_widget       = MxLookupWidget()
        self.whois_widget    = WhoisWidget()
        self.port_widget     = PortScannerWidget()
        self.ipinfo_widget   = IpInfoWidget()

        # ── Network Analysis ───────────────────────────────────────────
        self.topology_widget = TopologyMapperWidget()
        self.devices_widget  = ConnectedDevicesWidget()
        self.subnet_widget   = SubnetCalculatorWidget()
        self.http_widget     = HttpHeadersWidget()
        self.ssl_widget      = SslCheckerWidget()
        self.smtp_widget     = SmtpTestWidget()

        # ── Security ───────────────────────────────────────────────────
        self.blacklist_widget = BlacklistCheckWidget()
        self.cve_widget       = VulnerabilityScannerWidget()
        self.password_widget  = PasswordCheckerWidget()
        self.hash_widget      = HashToolWidget()

        # ── Utilities ──────────────────────────────────────────────────
        self.wol_widget         = WakeOnLanWidget()
        self.macvendor_widget   = MacVendorWidget()
        self.propagation_widget = DnsPropagationWidget()
        self.arptable_widget    = ArpRouteTableWidget()

        for w in (
            self.monitor_widget,
            self.dns_widget, self.mx_widget, self.whois_widget,
            self.port_widget, self.ipinfo_widget,
            self.topology_widget, self.devices_widget, self.subnet_widget,
            self.http_widget, self.ssl_widget, self.smtp_widget,
            self.blacklist_widget, self.cve_widget, self.password_widget,
            self.hash_widget,
            self.wol_widget, self.macvendor_widget,
            self.propagation_widget, self.arptable_widget,
        ):
            self.content_stack.addWidget(w)

    # ------------------------------------------------------------------
    #  Top toolbar — all tools with SVG icons
    # ------------------------------------------------------------------
    def _create_top_toolbar(self):
        tb = QToolBar("Tools", self)
        tb.setObjectName("mainToolbar")
        tb.setIconSize(QSize(36, 36))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)

        def tool(icon_name, label, widget, tb=tb):
            act = QAction(get_tool_icon(icon_name, 36), label, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked=False, a=act, w=widget: self._activate_tool(a, w))
            tb.addAction(act)
            self._tool_actions.append(act)
            return act

        def sep():
            tb.addSeparator()

        # ── Network Diagnostics
        tool('monitor',   'Network Monitor',  self.monitor_widget)
        tool('ping',      'Ping',             self.monitor_widget)
        tool('traceroute','Traceroute',        self.monitor_widget)
        sep()

        # ── DNS & Email
        tool('dns',  'DNS Lookup',   self.dns_widget)
        tool('mx',   'MX Lookup',    self.mx_widget)
        tool('smtp', 'SMTP Test',    self.smtp_widget)
        tool('whois','Whois',        self.whois_widget)
        sep()

        # ── Network & IP
        tool('port',   'Port Scanner',  self.port_widget)
        tool('ipinfo', 'IP Info',        self.ipinfo_widget)
        tool('subnet', 'Subnet Calc',    self.subnet_widget)
        sep()

        # ── Website / Analysis
        tool('http',     'HTTP Headers', self.http_widget)
        tool('ssl',      'SSL Inspector',self.ssl_widget)
        tool('topology', 'Topology Map', self.topology_widget)
        tool('devices',  'Device Scan',  self.devices_widget)
        sep()

        # ── Security
        tool('blacklist', 'Blacklist',  self.blacklist_widget)
        tool('cve',       'CVE Scan',   self.cve_widget)
        tool('password',  'Passwords',  self.password_widget)
        tool('hash',      'Hash Tool',  self.hash_widget)
        sep()

        # ── Utilities
        tool('wol',         'Wake-on-LAN',   self.wol_widget)
        tool('macvendor',   'MAC Vendor',     self.macvendor_widget)
        tool('propagation', 'DNS Propagate',  self.propagation_widget)
        tool('arptable',    'ARP/Routes',     self.arptable_widget)

    def _activate_tool(self, action: QAction, widget: QWidget):
        for a in self._tool_actions:
            a.setChecked(False)
        action.setChecked(True)
        self.content_stack.setCurrentWidget(widget)
        self.statusBar().showMessage(f"Tool: {action.text()}")

    # ------------------------------------------------------------------
    #  Notepad dock
    # ------------------------------------------------------------------
    def _create_notepad_dock(self):
        self.notepad_dock = QDockWidget("Scratchpad Notes", self)
        self.notepad_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.notepad_widget = NotepadWidget(self.config_manager)
        self.notepad_dock.setWidget(self.notepad_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.notepad_dock)
        self.notepad_dock.setVisible(False)
        self.notepad_dock.visibilityChanged.connect(self._update_notepad_menu_action_state)

    # ------------------------------------------------------------------
    #  Menu bar
    # ------------------------------------------------------------------
    def _create_menu_bar(self):
        mb = self.menuBar()
        file_menu = mb.addMenu("&File")
        file_menu.addAction("New Terminal Tab…", self._open_new_terminal_dialog)
        self.save_session_action = file_menu.addAction("Save Current Tab As…", self._save_current_session)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        view_menu = mb.addMenu("&View")
        self.toggle_notepad_action = view_menu.addAction("Toggle Scratchpad Notes")
        self.toggle_notepad_action.setCheckable(True)
        self.toggle_notepad_action.triggered.connect(self._toggle_notepad_visibility)

        settings_menu = mb.addMenu("&Settings")
        settings_menu.addAction("Preferences…", self._open_settings_dialog)

        help_menu = mb.addMenu("&Help")
        help_menu.addAction("About", self._show_about_dialog)
        help_menu.addAction("Donate…", self._open_donation_link)

    def _create_status_bar(self):
        self.statusBar().showMessage("Ready — select a tool from the toolbar above")

    # ------------------------------------------------------------------
    #  Session tree population
    # ------------------------------------------------------------------
    def _load_tree_structure(self):
        self.session_tree.clear()
        root = QTreeWidgetItem(self.session_tree, ["Saved Sessions"])
        root.setData(
            0, Qt.ItemDataRole.UserRole,
            {"type": "folder", "path": self.session_manager.get_session_dir(), "is_root": True}
        )
        self._populate_sessions(root)
        self.session_tree.expandItem(root)

    def _populate_sessions(self, parent_item):
        path = parent_item.data(0, Qt.ItemDataRole.UserRole)["path"]
        try:
            for entry in sorted(os.listdir(path)):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    fi = QTreeWidgetItem(parent_item, [entry])
                    fi.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "path": full_path})
                    self._populate_sessions(fi)
                elif entry.endswith(".json"):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        if "log_path" in meta and os.path.exists(meta["log_path"]):
                            si = QTreeWidgetItem(parent_item, [meta["name"]])
                            si.setData(0, Qt.ItemDataRole.UserRole,
                                       {"type": "session", "name": meta["name"],
                                        "log_path": meta["log_path"]})
                    except Exception:
                        pass
        except FileNotFoundError:
            pass

    # ------------------------------------------------------------------
    #  Terminal tab management
    # ------------------------------------------------------------------
    def add_terminal_tab(self, terminal_widget, name):
        idx = self.terminal_tab_widget.addTab(terminal_widget, name)
        self.terminal_tab_widget.setCurrentIndex(idx)
        terminal_widget.apply_settings(self.config_manager._config)
        terminal_widget.setFocus()
        self.content_stack.setCurrentWidget(self.terminal_tab_widget)
        for a in self._tool_actions:
            a.setChecked(False)

    def close_terminal_tab(self, index):
        widget = self.terminal_tab_widget.widget(index)
        if isinstance(widget, BaseTerminalWidget):
            widget.disconnect_from_target()
        self.terminal_tab_widget.removeTab(index)
        widget.deleteLater()

    # ------------------------------------------------------------------
    #  Slots
    # ------------------------------------------------------------------
    @Slot(bool)
    def _update_notepad_menu_action_state(self, visible: bool):
        self.toggle_notepad_action.setChecked(visible)
        self.toggle_notes_button.setChecked(visible)

    @Slot()
    def _toggle_notepad_visibility(self):
        self.notepad_dock.setVisible(not self.notepad_dock.isVisible())

    @Slot(QTreeWidgetItem, int)
    def _on_session_tree_item_clicked(self, item: QTreeWidgetItem, _col: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "session":
            return
        log_content = self.session_manager.load_session_log(data["log_path"])
        terminal = BaseTerminalWidget(self.config_manager)
        terminal.load_log_for_display(log_content)
        self.add_terminal_tab(terminal, data["name"])

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
        current = self.terminal_tab_widget.currentWidget()
        if not isinstance(current, BaseTerminalWidget):
            QMessageBox.warning(self, "Save Session", "Please select a terminal tab to save.")
            return
        log_data = current.get_current_log_data()
        if not log_data:
            QMessageBox.warning(self, "Save Session", "No data in the current terminal to save.")
            return
        folder = QFileDialog.getExistingDirectory(
            self, "Select Save Location", self.session_manager.get_session_dir()
        )
        if not folder:
            return
        name, ok = QInputDialog.getText(self, "Save Session", "Enter session name:")
        if ok and name:
            meta = current.get_current_session_metadata()
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
        if dialog.exec():
            self.config_manager.save_config()

    @Slot()
    def _open_donation_link(self):
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/thecmdguy"))

    @Slot()
    def _show_about_dialog(self):
        QMessageBox.about(self, "About Ducky", """
        <h2>Ducky — Network &amp; Security Toolkit</h2>
        <p>Version 1.5</p>
        <p>DNS &bull; MX &bull; DNS Propagation &bull; Whois &bull; SMTP &bull; Port Scan &bull;
        SSL &bull; HTTP Headers &bull; Blacklist &bull; IP Info &bull; CVE Scan &bull;
        Password &bull; Hash &bull; Topology &bull; Wake-on-LAN &bull; MAC Vendor &bull; ARP/Routes</p>
        <p><a href='https://github.com/thecmdguy/Ducky'>GitHub</a> &nbsp;&bull;&nbsp;
        <a href='https://ko-fi.com/thecmdguy'>Support on Ko-fi</a></p>
        """)

    # ------------------------------------------------------------------
    #  Theme / settings
    # ------------------------------------------------------------------
    def apply_current_settings(self):
        theme = self.config_manager.get_setting("app_theme")
        app = QApplication.instance()
        app.setFont(QFont("Segoe UI", 10))
        app.setStyleSheet(DARK_THEME_QSS if theme == "dark" else LIGHT_THEME_QSS)
        settings_dict = self.config_manager._config

        for i in range(self.content_stack.count()):
            w = self.content_stack.widget(i)
            if isinstance(w, QTabWidget):
                for j in range(w.count()):
                    if tab := w.widget(j):
                        if hasattr(tab, 'apply_settings'):
                            tab.apply_settings(settings_dict)
            elif hasattr(w, 'apply_settings'):
                w.apply_settings(settings_dict)

        if self.session_manager.base_session_dir != self.config_manager.get_setting("session_folder"):
            self.session_manager.base_session_dir = self.config_manager.get_setting("session_folder")
            os.makedirs(self.session_manager.base_session_dir, exist_ok=True)
            self._load_tree_structure()

    def closeEvent(self, event):
        for i in range(self.terminal_tab_widget.count()):
            w = self.terminal_tab_widget.widget(i)
            if isinstance(w, BaseTerminalWidget):
                w.disconnect_from_target()
        self.notepad_widget.save_and_stop()
        self.config_manager.save_config()
        event.accept()
