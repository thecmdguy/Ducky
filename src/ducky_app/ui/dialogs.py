import serial
import serial.tools.list_ports
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QLineEdit, QFileDialog, QColorDialog, QFontDialog, QStackedWidget, QWidget,
    QFormLayout
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Signal, Slot
from ducky_app.core.config_manager import ConfigManager

class ConnectionDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Connection")
        self.config_manager = config_manager
        
        self.layout = QVBoxLayout(self)
        
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["SSH", "Telnet", "Serial"])
        self.layout.addWidget(self.protocol_combo)
        
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        self.ssh_page = self._create_ssh_telnet_page("SSH")
        self.telnet_page = self._create_ssh_telnet_page("Telnet")
        self.serial_page = self._create_serial_page()
        
        self.stack.addWidget(self.ssh_page)
        self.stack.addWidget(self.telnet_page)
        self.stack.addWidget(self.serial_page)

        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addStretch()
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_layout)

        self.protocol_combo.currentIndexChanged.connect(self.stack.setCurrentIndex)
        self.connect_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.setMinimumWidth(400)

    def _create_serial_page(self):
        page = QWidget()
        layout = QFormLayout(page)
        self.com_port_combo = QComboBox()
        self.com_port_combo.addItems([p.device for p in serial.tools.list_ports.comports()] or ["No COM Ports Found"])
        self.baud_rate_combo = QComboBox()
        self.baud_rate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_rate_combo.setCurrentText(str(self.config_manager.get_setting("default_baudrate")))
        layout.addRow("COM Port:", self.com_port_combo)
        layout.addRow("Baud Rate:", self.baud_rate_combo)
        return page

    def _create_ssh_telnet_page(self, protocol_name):
        page = QWidget()
        layout = QFormLayout(page)
        
        host_input = QLineEdit()
        host_input.setPlaceholderText("e.g., 192.168.1.1")
        port_input = QLineEdit()
        
        layout.addRow("Host:", host_input)
        layout.addRow("Port:", port_input)
        
        if protocol_name == "SSH":
            port_input.setText("22")
            user_input = QLineEdit("root")
            pass_input = QLineEdit()
            pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addRow("Username:", user_input)
            layout.addRow("Password:", pass_input)
        else:
            port_input.setText("23")
        
        return page
        
    def get_settings(self):
        protocol = self.protocol_combo.currentText().lower()
        settings = {"type": protocol}
        
        current_page = self.stack.currentWidget()
        form_layout = current_page.layout()

        if protocol == "serial":
            if self.com_port_combo.currentText() == "No COM Ports Found": return None
            settings["port"] = self.com_port_combo.currentText()
            settings["baudrate"] = int(self.baud_rate_combo.currentText())
            settings["bytesize"] = 8; settings["parity"] = 'N'; settings["stopbits"] = 1; settings["timeout"] = 0
        
        elif protocol in ["ssh", "telnet"]:
            settings["host"] = form_layout.itemAt(1).widget().text()
            settings["port"] = int(form_layout.itemAt(3).widget().text() or 0)
            if not settings["host"] or not settings["port"]: return None

            if protocol == "ssh":
                settings["username"] = form_layout.itemAt(5).widget().text()
                settings["password"] = form_layout.itemAt(7).widget().text()
                if not settings["username"]: return None
        
        return settings

class SettingsDialog(QDialog):
    settings_changed = Signal()
    def __init__(self, config_manager, parent=None):
        super().__init__(parent); self.setWindowTitle("Application Settings"); self.setGeometry(100, 100, 450, 350); self.config_manager = config_manager
        self._temp_settings = {key: self.config_manager.get_setting(key) for key in ["terminal_bg_color", "terminal_font_color", "terminal_font_family", "terminal_font_size", "session_folder", "app_theme"]}
        layout = QVBoxLayout(self); layout.addWidget(QLabel("<h3>Terminal Appearance</h3>")); self.btn_bg_color = QPushButton("Choose Background Color"); self.btn_font_color = QPushButton("Choose Font Color")
        self.btn_font = QPushButton("Choose Font"); layout.addWidget(self.btn_bg_color); layout.addWidget(self.btn_font_color); layout.addWidget(self.btn_font)
        layout.addWidget(QLabel("<h3>Application Theme</h3>")); theme_layout = QHBoxLayout(); theme_layout.addWidget(QLabel("Theme:")); self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"]); self.theme_combo.setCurrentText(self._temp_settings["app_theme"].capitalize()); theme_layout.addWidget(self.theme_combo); theme_layout.addStretch(); layout.addLayout(theme_layout)
        layout.addWidget(QLabel("<h3>Session Management</h3>")); folder_layout = QHBoxLayout(); folder_layout.addWidget(QLabel("Session Folder:")); self.session_folder_edit = QLineEdit(self._temp_settings["session_folder"])
        self.session_folder_edit.setReadOnly(True); self.btn_browse_folder = QPushButton("Browse"); folder_layout.addWidget(self.session_folder_edit); folder_layout.addWidget(self.btn_browse_folder); layout.addLayout(folder_layout)
        button_layout = QHBoxLayout(); self.btn_save = QPushButton("Apply"); self.btn_cancel = QPushButton("Cancel"); button_layout.addStretch(); button_layout.addWidget(self.btn_save); button_layout.addWidget(self.btn_cancel); layout.addLayout(button_layout)
        self.btn_bg_color.clicked.connect(self._choose_bg_color); self.btn_font_color.clicked.connect(self._choose_font_color); self.btn_font.clicked.connect(self._choose_font)
        self.btn_browse_folder.clicked.connect(self._browse_session_folder); self.theme_combo.currentTextChanged.connect(self._on_theme_changed); self.btn_save.clicked.connect(self._save_settings); self.btn_cancel.clicked.connect(self.reject)
    @Slot()
    def _choose_bg_color(self):
        color = QColorDialog.getColor(QColor(self._temp_settings['terminal_bg_color']), self)
        if color.isValid(): self._temp_settings['terminal_bg_color'] = color.name()
    @Slot()
    def _choose_font_color(self):
        color = QColorDialog.getColor(QColor(self._temp_settings['terminal_font_color']), self)
        if color.isValid(): self._temp_settings['terminal_font_color'] = color.name()
    @Slot()
    def _choose_font(self):
        font, ok = QFontDialog.getFont(QFont(self._temp_settings['terminal_font_family'], self._temp_settings['terminal_font_size']), self)
        if ok: self._temp_settings['terminal_font_family'] = font.family(); self._temp_settings['terminal_font_size'] = font.pointSize()
    @Slot(str)
    def _on_theme_changed(self, theme_name: str): self._temp_settings["app_theme"] = theme_name.lower()
    @Slot()
    def _browse_session_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Session Folder", self._temp_settings["session_folder"])
        if folder: self._temp_settings["session_folder"] = folder; self.session_folder_edit.setText(folder)
    @Slot()
    def _save_settings(self):
        for key, value in self._temp_settings.items(): self.config_manager.set_setting(key, value)
        self.settings_changed.emit(); self.accept()