import os
import ipaddress
import psutil
import socket
import serial
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
    QLabel, QToolBar, QFontComboBox, QSpinBox, QMessageBox, QFileDialog,
    QColorDialog
)
from PySide6.QtGui import (
    QPalette, QColor, QFont, QIcon, QAction, QTextCharFormat, QTextCursor, QBrush
)
from PySide6.QtCore import Signal, Slot, QTimer
from ducky_app.core.config_manager import ConfigManager
from ducky_app.core.workers import SerialReaderThread, NetworkToolThread
from ducky_app.ui.dialogs import SerialConfigDialog

class BaseNetworkingToolWidget(QWidget):
    """Base class for networking tools with a consistent output display."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.layout().addWidget(self.output_text)

    @Slot(dict)
    def apply_settings(self, settings: dict):
        palette = self.output_text.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(settings.get("terminal_bg_color", "#282C34")))
        palette.setColor(QPalette.ColorRole.Text, QColor(settings.get("terminal_font_color", "#ABB2BF")))
        self.output_text.setPalette(palette)
        self.output_text.setFont(QFont(settings.get("terminal_font_family", "Monospace"), settings.get("terminal_font_size", 10)))

class SerialTerminalWidget(BaseNetworkingToolWidget):
    """Widget for serial port communication."""
    serial_connected = Signal(bool)

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.serial_port = None
        self.reader_thread = None
        self.current_log_data = ""
        self._current_serial_settings = {
            "port": None, "baudrate": self.config_manager.get_setting("default_baudrate"),
            "databits": 8, "parity": serial.PARITY_NONE, "stopbits": serial.STOPBITS_ONE, "timeout":0
        }

        main_layout = self.layout()
        control_layout = QHBoxLayout()
        self.port_label = QLabel("Port: N/A")
        self.baud_label = QLabel("Baud: N/A")
        self.connect_btn = QPushButton("Open Port")
        self.disconnect_btn = QPushButton("Close Port")
        control_layout.addWidget(self.port_label)
        control_layout.addWidget(self.baud_label)
        control_layout.addStretch(1)
        control_layout.addWidget(self.connect_btn)
        control_layout.addWidget(self.disconnect_btn)
        main_layout.insertLayout(0, control_layout)

        command_layout = QHBoxLayout() 
        self.command_input = QLineEdit()
        self.send_btn = QPushButton("Send")
        command_layout.addWidget(self.command_input)
        command_layout.addWidget(self.send_btn)
        main_layout.insertLayout(1, command_layout)

        self.connect_btn.clicked.connect(self._open_serial_dialog)
        self.disconnect_btn.clicked.connect(self._disconnect_serial)
        self.command_input.returnPressed.connect(self._send_command)
        self.send_btn.clicked.connect(self._send_command)

        self.update_port_info()
        self._set_terminal_active(False)

    def update_port_info(self):
        port = self._current_serial_settings.get("port") or "N/A"
        baud = self._current_serial_settings.get("baudrate") if port != "N/A" else "N/A"
        self.port_label.setText(f"Port: {port}")
        self.baud_label.setText(f"Baud: {baud}")

    def _set_terminal_active(self, active: bool):
        self.output_text.setReadOnly(not active)
        self.command_input.setEnabled(active)
        self.send_btn.setEnabled(active)
        self.connect_btn.setEnabled(not active)
        self.disconnect_btn.setEnabled(active)

    @Slot()
    def _open_serial_dialog(self):
        if self.serial_port and self.serial_port.is_open:
            self._disconnect_serial()
        dialog = SerialConfigDialog(self._current_serial_settings, self)
        if dialog.exec():
            self._current_serial_settings.update(dialog.get_settings())
            self.update_port_info()
            self._connect_serial()

    @Slot()
    def _connect_serial(self):
        if self.reader_thread and self.reader_thread.isRunning(): self.reader_thread.stop()
        if self.serial_port and self.serial_port.is_open: self.serial_port.close()

        settings = self._current_serial_settings
        if not settings["port"] or settings["port"] == "No COM Ports Found":
            QMessageBox.warning(self, "Serial Error", "No valid COM port selected.")
            return

        try:
            self.serial_port = serial.Serial(**settings)
            self.clear_terminal()
            self.output_text.append(f"--- Connected to {settings['port']} @ {settings['baudrate']} bps ---")
            self.serial_connected.emit(True)
            self._set_terminal_active(True)

            self.reader_thread = SerialReaderThread(self.serial_port)
            self.reader_thread.data_received.connect(self._handle_data_received)
            self.reader_thread.connection_lost.connect(self._handle_connection_lost)
            self.reader_thread.start()
        except serial.SerialException as e:
            QMessageBox.critical(self, "Serial Connection Error", f"Failed to open port: {e}")
            self._set_terminal_active(False)

    @Slot()
    def _disconnect_serial(self):
        if self.reader_thread and self.reader_thread.isRunning(): self.reader_thread.stop()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.output_text.append("--- Disconnected ---")
        self.serial_port = None
        self.serial_connected.emit(False)
        self._set_terminal_active(False)

    @Slot(str)
    def _handle_connection_lost(self, error_msg):
        self.output_text.append(f"--- Connection Lost: {error_msg} ---")
        self._disconnect_serial()

    @Slot(bytes)
    def _handle_data_received(self, data: bytes):
        decoded_data = data.decode('utf-8', errors='replace')
        self.output_text.insertPlainText(decoded_data)
        self.current_log_data += decoded_data
        self.output_text.verticalScrollBar().setValue(self.output_text.verticalScrollBar().maximum())

    @Slot()
    def _send_command(self):
        if self.serial_port and self.serial_port.is_open:
            command = self.command_input.text() + "\r\n"
            self.serial_port.write(command.encode('utf-8'))
            self.output_text.insertPlainText(f"[SENT] {command}")
            self.current_log_data += f"[SENT] {command}"
            self.command_input.clear()

    def get_current_log_data(self): return self.current_log_data
    def get_current_session_metadata(self):
        if self.serial_port:
            return { "port": self.serial_port.port, "baudrate": self.serial_port.baudrate }
        return {}
    def clear_terminal(self):
        self.output_text.clear()
        self.current_log_data = ""
    def load_log_for_display(self, log_content):
        self.clear_terminal()
        self.output_text.setPlainText(log_content)
        self._set_terminal_active(False)

class SubnetCalculatorWidget(BaseNetworkingToolWidget):
    """Widget for performing subnet calculations."""
    def __init__(self, parent=None):
        super().__init__(parent)
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("IP Address/CIDR:"))
        self.ip_input = QLineEdit("192.168.1.0/24")
        self.calculate_btn = QPushButton("Calculate")
        input_layout.addWidget(self.ip_input)
        input_layout.addWidget(self.calculate_btn)
        self.layout().insertLayout(0, input_layout)
        self.calculate_btn.clicked.connect(self._calculate_subnet)

    @Slot()
    def _calculate_subnet(self):
        self.output_text.clear()
        try:
            network = ipaddress.ip_network(self.ip_input.text().strip(), strict=False)
            hosts = list(network.hosts())
            output = [
                f"--- Subnet Calculation for {network.with_prefixlen} ---",
                f"Network Address: {network.network_address}",
                f"Subnet Mask: {network.netmask}",
                f"Broadcast Address: {network.broadcast_address}",
                f"Usable Host Range: {hosts[0]} - {hosts[-1]}" if hosts else "N/A",
                f"Total Addresses: {network.num_addresses}",
                f"Usable Hosts: {len(hosts)}",
            ]
            self.output_text.setPlainText("\n".join(output))
        except ValueError as e:
            self.output_text.setPlainText(f"Error: {e}")

class NetworkPerformanceMonitorWidget(BaseNetworkingToolWidget):
    """Widget for monitoring local network performance."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tool_thread = None
        control_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Local Info")
        self.target_input = QLineEdit("google.com")
        self.ping_btn = QPushButton("Ping")
        self.traceroute_btn = QPushButton("Traceroute")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(QLabel("Target:"))
        control_layout.addWidget(self.target_input)
        control_layout.addWidget(self.ping_btn)
        control_layout.addWidget(self.traceroute_btn)
        control_layout.addWidget(self.stop_btn)
        self.layout().insertLayout(0, control_layout)

        self.refresh_btn.clicked.connect(self._refresh_local_info)
        self.ping_btn.clicked.connect(lambda: self._start_network_tool("ping"))
        self.traceroute_btn.clicked.connect(lambda: self._start_network_tool("traceroute"))
        self.stop_btn.clicked.connect(self._stop_network_tool)
        self._refresh_local_info()

    @Slot()
    def _refresh_local_info(self):
        self.output_text.clear()
        mem = psutil.virtual_memory()
        net_io = psutil.net_io_counters()
        output = [
            "--- Local System and Network Information ---",
            f"CPU Usage: {psutil.cpu_percent(interval=0.1)}%",
            f"Memory Usage: {mem.percent}% ({mem.used/1024**3:.2f}GB / {mem.total/1024**3:.2f}GB)",
            "\n--- Network I/O ---",
            f"Bytes Sent: {net_io.bytes_sent/1024**2:.2f} MB",
            f"Bytes Recv: {net_io.bytes_recv/1024**2:.2f} MB"
        ]
        self.output_text.setPlainText("\n".join(output))

    @Slot(str)
    def _start_network_tool(self, tool_type):
        if self.tool_thread and self.tool_thread.isRunning(): return
        self.output_text.clear()
        self._set_buttons_enabled(False)
        self.tool_thread = NetworkToolThread(tool_type, self.target_input.text().strip())
        self.tool_thread.result_output.connect(self.output_text.insertPlainText)
        self.tool_thread.scan_complete.connect(lambda: self._set_buttons_enabled(True))
        self.tool_thread.start()

    @Slot()
    def _stop_network_tool(self):
        if self.tool_thread and self.tool_thread.isRunning():
            self.tool_thread.stop()
            self.tool_thread = None
        self._set_buttons_enabled(True)

    def _set_buttons_enabled(self, enabled):
        self.ping_btn.setEnabled(enabled)
        self.traceroute_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(not enabled)

class PortScannerWidget(BaseNetworkingToolWidget):
    """Widget for scanning open ports on a target."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scan_thread = None
        control_layout = QHBoxLayout()
        self.target_input = QLineEdit("127.0.0.1")
        self.port_range_input = QLineEdit("1-1024")
        self.scan_btn = QPushButton("Scan Ports")
        self.stop_btn = QPushButton("Stop Scan")
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(QLabel("Target:"))
        control_layout.addWidget(self.target_input)
        control_layout.addWidget(QLabel("Port Range:"))
        control_layout.addWidget(self.port_range_input)
        control_layout.addWidget(self.scan_btn)
        control_layout.addWidget(self.stop_btn)
        self.layout().insertLayout(0, control_layout)

        self.scan_btn.clicked.connect(self._start_port_scan)
        self.stop_btn.clicked.connect(self._stop_port_scan)

    @Slot()
    def _start_port_scan(self):
        if self.scan_thread and self.scan_thread.isRunning(): return
        try:
            start, end = map(int, self.port_range_input.text().strip().split('-'))
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid port range (e.g., 1-1024).")
            return
        
        self.output_text.clear()
        self._set_buttons_enabled(False)
        self.scan_thread = NetworkToolThread("port_scan", self.target_input.text().strip(), (start, end))
        self.scan_thread.result_output.connect(self.output_text.insertPlainText)
        self.scan_thread.scan_complete.connect(lambda: self._set_buttons_enabled(True))
        self.scan_thread.start()

    @Slot()
    def _stop_port_scan(self):
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
            self.scan_thread = None
        self._set_buttons_enabled(True)
    
    def _set_buttons_enabled(self, enabled):
        self.scan_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(not enabled)

class NotepadWidget(QWidget):
    """A simple rich-text notepad widget with auto-save."""
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.notes_folder = self.config_manager.get_setting("notes_folder")
        os.makedirs(self.notes_folder, exist_ok=True)
        self.notepad_file_path = os.path.join(self.notes_folder, "scratchpad.html")

        self.setLayout(QVBoxLayout())
        self.toolbar = QToolBar()
        self.notepad_text = QTextEdit()
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.notepad_text)

        self._setup_toolbar()
        self.notepad_text.selectionChanged.connect(self._update_toolbar_state)
        self.notepad_text.cursorPositionChanged.connect(self._update_toolbar_state)

        self.save_timer = QTimer(self)
        self.save_timer.setInterval(5000)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._auto_save_note)
        self.notepad_text.textChanged.connect(self.save_timer.start)

        self._load_note()

    def _setup_toolbar(self):
        self._bold_action = self._create_format_action("B", "Bold", "Ctrl+B", True, self._set_text_bold)
        self._italic_action = self._create_format_action("I", "Italic", "Ctrl+I", True, self._set_text_italic)
        self._underline_action = self._create_format_action("U", "Underline", "Ctrl+U", True, self._set_text_underline)
        
        self.toolbar.addSeparator()
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self._set_font_family)
        self.toolbar.addWidget(self.font_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 72)
        self.font_size_spin.setValue(10)
        self.font_size_spin.valueChanged.connect(self._set_font_size)
        self.toolbar.addWidget(self.font_size_spin)

        self.toolbar.addSeparator()
        self._create_format_action(None, "Text Color", None, False, self._set_text_color, "color-text")
        self._create_format_action(None, "Highlight Color", None, False, self._set_highlight_color, "color-fill")
        
        self.toolbar.addSeparator()
        save_as_button = QPushButton("Save As...")
        save_as_button.clicked.connect(self._save_note_as)
        self.toolbar.addWidget(save_as_button)

    def _create_format_action(self, text, tooltip, shortcut, checkable, triggered_func, icon_name=None):
        icon = QIcon.fromTheme(icon_name) if icon_name else QIcon()
        action = QAction(icon, text, self) if text else QAction(icon, tooltip, self)
        action.setToolTip(tooltip)
        if shortcut: action.setShortcut(shortcut)
        action.setCheckable(checkable)
        action.triggered.connect(triggered_func)
        self.toolbar.addAction(action)
        return action
    
    def _merge_format(self, char_format: QTextCharFormat):
        cursor = self.notepad_text.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(char_format)
        self.notepad_text.mergeCurrentCharFormat(char_format)

    def _set_text_bold(self, checked):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
        self._merge_format(fmt)
        
    def _set_text_italic(self, checked):
        fmt = QTextCharFormat()
        fmt.setFontItalic(checked)
        self._merge_format(fmt)

    def _set_text_underline(self, checked):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(checked)
        self._merge_format(fmt)
    
    def _set_font_family(self, font):
        fmt = QTextCharFormat()
        fmt.setFontFamily(font.family())
        self._merge_format(fmt)

    def _set_font_size(self, size):
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self._merge_format(fmt)
        
    def _set_text_color(self):
        color = QColorDialog.getColor(self.notepad_text.textColor(), self)
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self._merge_format(fmt)
            
    def _set_highlight_color(self):
        color = QColorDialog.getColor(self.notepad_text.textBackgroundColor(), self)
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setBackground(color)
            self._merge_format(fmt)
    
    @Slot()
    def _update_toolbar_state(self):
        fmt = self.notepad_text.currentCharFormat()
        self._bold_action.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self._italic_action.setChecked(fmt.fontItalic())
        self._underline_action.setChecked(fmt.fontUnderline())
        self.font_combo.setCurrentFont(fmt.font())
        self.font_size_spin.setValue(int(fmt.fontPointSize()))

    def _load_note(self):
        if os.path.exists(self.notepad_file_path):
            with open(self.notepad_file_path, 'r', encoding='utf-8') as f:
                self.notepad_text.setHtml(f.read())

    @Slot()
    def _auto_save_note(self): self._save_note(self.notepad_file_path)
    
    def _save_note(self, filepath):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.notepad_text.toHtml())
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Failed to save notes: {e}")

    @Slot()
    def _save_note_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Notes As", self.notes_folder, "HTML Files (*.html);;Text Files (*.txt)")
        if file_path: self._save_note(file_path)

    def save_and_stop(self):
        self.save_timer.stop()
        self._save_note(self.notepad_file_path)