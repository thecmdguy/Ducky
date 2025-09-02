import serial
import serial.tools.list_ports
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QLineEdit, QFileDialog, QColorDialog, QFontDialog
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Signal, Slot
from ducky_app.core.config_manager import ConfigManager


class SerialConfigDialog(QDialog):
    # ... (the __init__ method and other methods are correct)
    def __init__(self, current_settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Serial Port Settings")
        self.setMinimumWidth(350)
        self.settings = current_settings
        layout = QVBoxLayout(self)

        self.port_combo_widget = QComboBox()
        self.baud_combo_widget = QComboBox()
        self.data_combo_widget = QComboBox()
        self.parity_combo_widget = QComboBox()
        self.stop_combo_widget = QComboBox()

        # Controls setup
        self._add_combo_row(layout, "Port:", self.port_combo_widget, self._get_ports(), self.settings.get('port'))
        self._add_combo_row(layout, "Baud Rate:", self.baud_combo_widget, ["9600", "19200", "38400", "57600", "115200"], str(self.settings.get('baudrate', 9600)))
        self._add_combo_row(layout, "Data Bits:", self.data_combo_widget, ["8", "7", "6", "5"], str(self.settings.get('bytesize', 8))) # Use bytesize as default key
        self._add_combo_row(layout, "Parity:", self.parity_combo_widget, ["None", "Even", "Odd", "Mark", "Space"], self._parity_to_str(self.settings.get('parity', serial.PARITY_NONE)))
        self._add_combo_row(layout, "Stop Bits:", self.stop_combo_widget, ["1", "1.5", "2"], self._stopbits_to_str(self.settings.get('stopbits', serial.STOPBITS_ONE)))

        # Buttons
        self.ok_button = QPushButton("Connect")
        self.cancel_button = QPushButton("Cancel")
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        if not self._get_ports():
            self.port_combo_widget.addItem("No COM Ports Found")
            self.port_combo_widget.setEnabled(False)
            self.ok_button.setEnabled(False)

    def _add_combo_row(self, parent_layout, label_text, combo_widget, items, current_text):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        combo_widget.addItems(items)
        if current_text in items:
            combo_widget.setCurrentText(current_text)
        layout.addWidget(combo_widget)
        parent_layout.addLayout(layout)

    def _get_ports(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def _parity_to_str(self, p):
        return {serial.PARITY_NONE: "None", serial.PARITY_EVEN: "Even", serial.PARITY_ODD: "Odd", serial.PARITY_MARK: "Mark", serial.PARITY_SPACE: "Space"}.get(p, "None")
    
    def _stopbits_to_str(self, s):
        return {serial.STOPBITS_ONE: "1", serial.STOPBITS_ONE_POINT_FIVE: "1.5", serial.STOPBITS_TWO: "2"}.get(s, "1")

    # --- THIS IS THE METHOD TO FIX ---
    def get_settings(self):
        parity_map = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD, "Mark": serial.PARITY_MARK, "Space": serial.PARITY_SPACE}
        stopbits_map = {"1": serial.STOPBITS_ONE, "1.5": serial.STOPBITS_ONE_POINT_FIVE, "2": serial.STOPBITS_TWO}
        
        return {
            "port": self.port_combo_widget.currentText(),
            "baudrate": int(self.baud_combo_widget.currentText()),
            "bytesize": int(self.data_combo_widget.currentText()), # <-- CHANGED from 'databits' to 'bytesize'
            "parity": parity_map.get(self.parity_combo_widget.currentText()),
            "stopbits": stopbits_map.get(self.stop_combo_widget.currentText()),
        }

# ... (The SettingsDialog class is correct and unchanged)
class SettingsDialog(QDialog):
    """Dialog for customizing application appearance."""
    settings_changed = Signal()

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setGeometry(100, 100, 450, 350)
        self.config_manager = config_manager
        
        self._temp_settings = {key: self.config_manager.get_setting(key) for key in [
            "terminal_bg_color", "terminal_font_color", "terminal_font_family", 
            "terminal_font_size", "session_folder", "app_theme"
        ]}

        layout = QVBoxLayout(self)

        # Terminal Appearance
        layout.addWidget(QLabel("<h3>Terminal Appearance</h3>"))
        self.btn_bg_color = QPushButton("Choose Background Color")
        self.btn_font_color = QPushButton("Choose Font Color")
        self.btn_font = QPushButton("Choose Font")
        layout.addWidget(self.btn_bg_color)
        layout.addWidget(self.btn_font_color)
        layout.addWidget(self.btn_font)

        # Application Theme
        layout.addWidget(QLabel("<h3>Application Theme</h3>"))
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(self._temp_settings["app_theme"].capitalize())
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        # Session Folder
        layout.addWidget(QLabel("<h3>Session Management</h3>"))
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Session Folder:"))
        self.session_folder_edit = QLineEdit(self._temp_settings["session_folder"])
        self.session_folder_edit.setReadOnly(True)
        self.btn_browse_folder = QPushButton("Browse")
        folder_layout.addWidget(self.session_folder_edit)
        folder_layout.addWidget(self.btn_browse_folder)
        layout.addLayout(folder_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.btn_save = QPushButton("Apply")
        self.btn_cancel = QPushButton("Cancel")
        button_layout.addStretch()
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)

        # Connections
        self.btn_bg_color.clicked.connect(self._choose_bg_color)
        self.btn_font_color.clicked.connect(self._choose_font_color)
        self.btn_font.clicked.connect(self._choose_font)
        self.btn_browse_folder.clicked.connect(self._browse_session_folder)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        self.btn_save.clicked.connect(self._save_settings)
        self.btn_cancel.clicked.connect(self.reject)

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
        if ok:
            self._temp_settings['terminal_font_family'] = font.family()
            self._temp_settings['terminal_font_size'] = font.pointSize()

    @Slot(str)
    def _on_theme_changed(self, theme_name: str):
        self._temp_settings["app_theme"] = theme_name.lower()

    @Slot()
    def _browse_session_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Session Folder", self._temp_settings["session_folder"])
        if folder:
            self._temp_settings["session_folder"] = folder
            self.session_folder_edit.setText(folder)

    @Slot()
    def _save_settings(self):
        for key, value in self._temp_settings.items():
            self.config_manager.set_setting(key, value)
        self.settings_changed.emit()
        self.accept()