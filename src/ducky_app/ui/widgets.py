import os
import ipaddress
import psutil
import socket
import serial
import hashlib
import time
import asyncio
import telnetlib3
import paramiko
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
    QLabel, QToolBar, QFontComboBox, QSpinBox, QMessageBox, QFileDialog,
    QColorDialog, QGraphicsView, QGraphicsScene, QGraphicsItemGroup, QGraphicsEllipseItem,
    QGraphicsTextItem, QProgressBar, QComboBox, QPlainTextEdit, QTableWidget, QHeaderView,
    QAbstractItemView, QTableWidgetItem, QApplication, QGraphicsPathItem
)
from PySide6.QtGui import (
    QPalette, QColor, QFont, QIcon, QAction, QTextCharFormat, QTextCursor, QBrush,
    QKeyEvent, QPainter, QPen, QPainterPath, QRadialGradient
)
from PySide6.QtCore import Signal, Slot, QTimer, Qt, QRectF
from ducky_app.core.config_manager import ConfigManager
from ducky_app.core.workers import ConnectionReaderThread, NetworkToolThread, DiscoveryWorker, CveSearchWorker
from ducky_app.ui.dialogs import ConnectionDialog
from zxcvbn import zxcvbn

class BaseNetworkingToolWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_text = QTextEdit()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.output_text)
        self.output_text.setReadOnly(True)
        self.output_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

    @Slot(dict)
    def apply_settings(self, settings: dict):
        palette = self.output_text.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(settings.get("terminal_bg_color", "#282C34")))
        palette.setColor(QPalette.ColorRole.Text, QColor(settings.get("terminal_font_color", "#ABB2BF")))
        self.output_text.setPalette(palette)
        self.output_text.setFont(QFont(settings.get("terminal_font_family", "Monospace"), settings.get("terminal_font_size", 10)))

class BaseTerminalWidget(QWidget):
    connection_closed = Signal()

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.client = None
        self.ssh_client = None
        self.telnet_writer = None
        self.reader_thread = None
        self.is_connected = False
        self.conn_type = None
        self._current_settings = {}
        
        self.command_history = []
        self.history_index = -1
        self.known_commands = sorted([
            "show running-config", "show startup-config", "show ip interface brief",
            "show version", "show interfaces", "show vlan", "show mac address-table",
            "configure terminal", "interface", "ip address", "vlan", "switchport",
            "no shutdown", "exit", "end", "copy running-config startup-config",
            "write memory", "reload", "enable"
        ])

        self.output_text = QTextEdit()
        self.output_text.keyPressEvent = self.handle_key_press
        self.output_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.output_text)
        self.setFocusProxy(self.output_text)

    def connect_to_target(self, settings):
        if self.is_connected: self.disconnect_from_target()
        
        self._current_settings = settings
        self.conn_type = settings.get("type")
        self.clear_terminal()
        self.output_text.setReadOnly(False)

        try:
            tab_name = "Error"
            if self.conn_type == "serial":
                self.client = serial.Serial(**{k:v for k,v in settings.items() if k != 'type'})
                self.reader_thread = ConnectionReaderThread(self.client, None, self.conn_type)
                tab_name = f"{settings['port']}"
            
            elif self.conn_type == "telnet":
                try:
                    reader, writer = asyncio.run(telnetlib3.open_connection(settings['host'], settings['port'], timeout=5))
                    self.telnet_writer = writer
                    self.reader_thread = ConnectionReaderThread(reader, writer, self.conn_type)
                    tab_name = f"Telnet: {settings['host']}"
                except Exception as e:
                    raise ConnectionRefusedError(f"Telnet connection failed: {e}") from e

            elif self.conn_type == "ssh":
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(
                    hostname=settings['host'], port=settings['port'],
                    username=settings['username'], password=settings['password'],
                    timeout=10, look_for_keys=False, allow_agent=False
                )
                self.client = self.ssh_client.invoke_shell()
                self.reader_thread = ConnectionReaderThread(self.client, None, self.conn_type)
                tab_name = f"SSH: {settings['username']}@{settings['host']}"

            self.is_connected = True
            self.reader_thread.data_received.connect(self._handle_data_received)
            self.reader_thread.connection_lost.connect(self._handle_connection_lost)
            self.reader_thread.start()
            self.setFocus()
            return True, tab_name
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {e}")
            self.is_connected = False
            return False, "Error"

    def disconnect_from_target(self):
        if self.reader_thread and self.reader_thread.isRunning(): self.reader_thread.stop()
        if self.telnet_writer: 
            try: self.telnet_writer.close()
            except: pass
        if self.client:
            try: self.client.close()
            except: pass
        if self.ssh_client:
            try: self.ssh_client.close()
            except: pass
        self.client, self.ssh_client, self.telnet_writer, self.is_connected = None, None, None, False
        self.connection_closed.emit()
        self.output_text.setReadOnly(True)

    def load_log_for_display(self, log_content):
        self.clear_terminal(); self.output_text.setPlainText(log_content); self.output_text.setReadOnly(True)

    def handle_key_press(self, event: QKeyEvent):
        cursor = self.output_text.textCursor()

        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and (event.key() == Qt.Key.Key_C or event.key() == Qt.Key.Key_V):
            super(QTextEdit, self.output_text).keyPressEvent(event); return
        
        if self.is_connected and not self.output_text.isReadOnly():
            if event.key() == Qt.Key.Key_Up:
                if self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.recall_history()
                return
            
            elif event.key() == Qt.Key.Key_Down:
                if self.history_index > 0:
                    self.history_index -= 1
                    self.recall_history()
                else:
                    self.history_index = -1
                    cursor.select(QTextCursor.SelectionType.LineUnderCursor)
                    line_text = cursor.selectedText()
                    prompt_end = line_text.rfind('>') + 1 or line_text.rfind('#') + 1 or line_text.rfind('$') + 1
                    if prompt_end == 0:
                         prompt_end = len(line_text)
                         
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, prompt_end)
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
                    cursor.removeSelectedText()
                return
            
            if event.key() in [Qt.Key.Key_Left, Qt.Key.Key_Right]:
                super(QTextEdit, self.output_text).keyPressEvent(event)
                return

        if self.is_connected and not self.output_text.isReadOnly():
            if event.key() == Qt.Key.Key_Tab:
                self.perform_tab_completion()
                return
                
            char_to_send = event.text()
            if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
                cursor.select(QTextCursor.SelectionType.LineUnderCursor)
                line_text = cursor.selectedText()
                prompt_end = line_text.rfind('>') + 1 or line_text.rfind('#') + 1 or line_text.rfind('$') + 1
                if prompt_end == 0:
                    prompt_end = len(line_text)
                    
                command = line_text[prompt_end:].strip()
                if command:
                    if not self.command_history or self.command_history[0] != command:
                        self.command_history.insert(0, command)
                self.history_index = -1
                char_to_send = '\r'
            
            elif event.key() == Qt.Key.Key_Backspace:
                char_to_send = '\b'
            
            if char_to_send:
                try:
                    data = char_to_send.encode('utf-8')
                    if self.conn_type == 'ssh': self.client.send(data)
                    elif self.conn_type == 'telnet': self.telnet_writer.write(data)
                    else: self.client.write(data)
                except Exception as e:
                    QMessageBox.critical(self, "Write Error", f"Failed to send data: {e}"); self.disconnect_from_target()
        
        super(QTextEdit, self.output_text).keyPressEvent(event)
        
    def recall_history(self):
        if 0 <= self.history_index < len(self.command_history):
            command = self.command_history[self.history_index]
            cursor = self.output_text.textCursor()
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            line_text = cursor.selectedText()
            prompt_end = line_text.rfind('>') + 1 or line_text.rfind('#') + 1 or line_text.rfind('$') + 1
            if prompt_end == 0:
                prompt_end = len(line_text)
            
            prompt = line_text[:prompt_end]

            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveMode.MoveAnchor, prompt_end)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            cursor.insertText(command)
            self.output_text.setTextCursor(cursor)
    
    def perform_tab_completion(self):
        cursor = self.output_text.textCursor()
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        line_text = cursor.selectedText()
        prompt_end = line_text.rfind('>') + 1 or line_text.rfind('#') + 1 or line_text.rfind('$') + 1
        current_input = line_text[prompt_end:]

        parts = current_input.strip().split()
        if not parts: return
        
        word_to_complete = parts[-1]
        matches = [cmd for cmd in self.known_commands if cmd.startswith(word_to_complete)]

        if len(matches) == 1:
            completion = matches[0][len(word_to_complete):]
            self.output_text.insertPlainText(completion)
            if self.is_connected:
                data_to_send = completion.encode('utf-8')
                if self.conn_type == 'ssh': self.client.send(data_to_send)
                elif self.conn_type == 'telnet': self.telnet_writer.write(data_to_send)
                else: self.client.write(data_to_send)
        elif len(matches) > 1:
            QApplication.beep()
            self.output_text.append("\n" + "  ".join(matches))
            self.output_text.append(line_text)
            if self.is_connected:
                self.client.write(b'\n')

    @Slot(bytes)
    def _handle_data_received(self, data: bytes):
        try:
            decoded_data = data.decode('utf-8', errors='replace'); cursor = self.output_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            for char in decoded_data:
                if char == '\b': cursor.movePosition(QTextCursor.MoveOperation.PreviousCharacter, QTextCursor.MoveMode.KeepAnchor); cursor.removeSelectedText()
                else: cursor.insertText(char)
            self.output_text.setTextCursor(cursor)
        except Exception: pass
        
    @Slot(str)
    def _handle_connection_lost(self, error_msg):
        self.output_text.append(f"\n--- {error_msg} ---"); self.disconnect_from_target()
    def get_current_log_data(self): return self.output_text.toPlainText()
    def get_current_session_metadata(self): return self._current_settings if self.is_connected else {}
    def clear_terminal(self): 
        self.output_text.clear()
        self.command_history.clear()
        self.history_index = -1
    @Slot(dict)
    def apply_settings(self, settings: dict):
        palette = self.output_text.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(settings.get("terminal_bg_color", "#282C34")))
        palette.setColor(QPalette.ColorRole.Text, QColor(settings.get("terminal_font_color", "#ABB2BF")))
        self.output_text.setPalette(palette)
        self.output_text.setFont(QFont(settings.get("terminal_font_family", "Monospace"), settings.get("terminal_font_size", 10)))

class SubnetCalculatorWidget(BaseNetworkingToolWidget):
    def __init__(self, parent=None):
        super().__init__(parent); input_layout = QHBoxLayout(); input_layout.addWidget(QLabel("IP Address/CIDR:"))
        self.ip_input = QLineEdit("192.168.1.0/24"); self.calculate_btn = QPushButton("Calculate")
        input_layout.addWidget(self.ip_input); input_layout.addWidget(self.calculate_btn)
        self.layout().insertLayout(0, input_layout); self.calculate_btn.clicked.connect(self._calculate_subnet)
    @Slot()
    def _calculate_subnet(self):
        self.output_text.clear()
        try:
            network = ipaddress.ip_network(self.ip_input.text().strip(), strict=False); hosts = list(network.hosts())
            output = [f"--- Subnet Calculation for {network.with_prefixlen} ---", f"Network Address: {network.network_address}", f"Subnet Mask: {network.netmask}",
                      f"Broadcast Address: {network.broadcast_address}", f"Usable Host Range: {hosts[0]} - {hosts[-1]}" if hosts else "N/A",
                      f"Total Addresses: {network.num_addresses}", f"Usable Hosts: {len(hosts)}"]
            self.output_text.setPlainText("\n".join(output))
        except ValueError as e: self.output_text.setPlainText(f"Error: {e}")

class NetworkPerformanceMonitorWidget(BaseNetworkingToolWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.tool_thread = None; control_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Local Info"); self.target_input = QLineEdit("google.com"); self.ping_btn = QPushButton("Ping")
        self.traceroute_btn = QPushButton("Traceroute"); self.stop_btn = QPushButton("Stop"); self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.refresh_btn); control_layout.addWidget(QLabel("Target:")); control_layout.addWidget(self.target_input)
        control_layout.addWidget(self.ping_btn); control_layout.addWidget(self.traceroute_btn); control_layout.addWidget(self.stop_btn)
        self.layout().insertLayout(0, control_layout); self.refresh_btn.clicked.connect(self._refresh_local_info)
        self.ping_btn.clicked.connect(lambda: self._start_network_tool("ping")); self.traceroute_btn.clicked.connect(lambda: self._start_network_tool("traceroute"))
        self.stop_btn.clicked.connect(self._stop_network_tool); self._refresh_local_info()
    @Slot()
    def _refresh_local_info(self):
        self.output_text.clear(); mem = psutil.virtual_memory(); net_io = psutil.net_io_counters()
        output = ["--- Local System and Network Information ---", f"CPU Usage: {psutil.cpu_percent(interval=0.1)}%",
                  f"Memory Usage: {mem.percent}% ({mem.used/1024**3:.2f}GB / {mem.total/1024**3:.2f}GB)", "\n--- Network I/O ---",
                  f"Bytes Sent: {net_io.bytes_sent/1024**2:.2f} MB", f"Bytes Recv: {net_io.bytes_recv/1024**2:.2f} MB"]
        self.output_text.setPlainText("\n".join(output))
    @Slot(str)
    def _start_network_tool(self, tool_type):
        if self.tool_thread and self.tool_thread.isRunning(): return
        self.output_text.clear(); self._set_buttons_enabled(False)
        self.tool_thread = NetworkToolThread(tool_type, self.target_input.text().strip())
        self.tool_thread.result_output.connect(self.output_text.insertPlainText)
        self.tool_thread.scan_complete.connect(lambda: self._set_buttons_enabled(True)); self.tool_thread.start()
    @Slot()
    def _stop_network_tool(self):
        if self.tool_thread and self.tool_thread.isRunning(): self.tool_thread.stop(); self.tool_thread = None
        self._set_buttons_enabled(True)
    def _set_buttons_enabled(self, enabled):
        self.ping_btn.setEnabled(enabled); self.traceroute_btn.setEnabled(enabled); self.stop_btn.setEnabled(not enabled)

class PortScannerWidget(BaseNetworkingToolWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.scan_thread = None; control_layout = QHBoxLayout()
        self.target_input = QLineEdit("127.0.0.1"); self.port_range_input = QLineEdit("1-1024"); self.scan_btn = QPushButton("Scan Ports")
        self.stop_btn = QPushButton("Stop Scan"); self.stop_btn.setEnabled(False)
        control_layout.addWidget(QLabel("Target:")); control_layout.addWidget(self.target_input); control_layout.addWidget(QLabel("Port Range:"))
        control_layout.addWidget(self.port_range_input); control_layout.addWidget(self.scan_btn); control_layout.addWidget(self.stop_btn)
        self.layout().insertLayout(0, control_layout); self.scan_btn.clicked.connect(self._start_port_scan); self.stop_btn.clicked.connect(self._stop_port_scan)
    @Slot()
    def _start_port_scan(self):
        if self.scan_thread and self.scan_thread.isRunning(): return
        try:
            start, end = map(int, self.port_range_input.text().strip().split('-'))
            if not (0 < start <= 65535 and start <= end <= 65535): raise ValueError("Port range out of bounds")
        except ValueError: QMessageBox.warning(self, "Input Error", "Invalid port range (e.g., 1-1024)."); return
        self.output_text.clear(); self._set_buttons_enabled(False)
        self.scan_thread = NetworkToolThread("port_scan", self.target_input.text().strip(), (start, end))
        self.scan_thread.result_output.connect(self.output_text.insertPlainText)
        self.scan_thread.scan_complete.connect(lambda: self._set_buttons_enabled(True)); self.scan_thread.start()
    @Slot()
    def _stop_port_scan(self):
        if self.scan_thread and self.scan_thread.isRunning(): self.scan_thread.stop(); self.scan_thread = None
        self._set_buttons_enabled(True)
    def _set_buttons_enabled(self, enabled):
        self.scan_btn.setEnabled(enabled); self.stop_btn.setEnabled(not enabled)

class NotepadWidget(QWidget):
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent); self.config_manager = config_manager
        self.notes_folder = self.config_manager.get_setting("notes_folder"); os.makedirs(self.notes_folder, exist_ok=True)
        self.notepad_file_path = os.path.join(self.notes_folder, "scratchpad.html"); self.setLayout(QVBoxLayout())
        self.toolbar = QToolBar(); self.notepad_text = QTextEdit(); self.layout().addWidget(self.toolbar); self.layout().addWidget(self.notepad_text)
        self._setup_toolbar(); self.notepad_text.selectionChanged.connect(self._update_toolbar_state); self.notepad_text.cursorPositionChanged.connect(self._update_toolbar_state)
        self.save_timer = QTimer(self); self.save_timer.setInterval(5000); self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._auto_save_note); self.notepad_text.textChanged.connect(self.save_timer.start); self._load_note()
    def _setup_toolbar(self):
        self._bold_action = self._create_format_action("B", "Bold", "Ctrl+B", True, self._set_text_bold)
        self._italic_action = self._create_format_action("I", "Italic", "Ctrl+I", True, self._set_text_italic)
        self._underline_action = self._create_format_action("U", "Underline", "Ctrl+U", True, self._set_text_underline)
        self.toolbar.addSeparator(); self.font_combo = QFontComboBox(); self.font_combo.currentFontChanged.connect(self._set_font_family); self.toolbar.addWidget(self.font_combo)
        self.font_size_spin = QSpinBox(); self.font_size_spin.setRange(6, 72); self.font_size_spin.setValue(10); self.font_size_spin.valueChanged.connect(self._set_font_size); self.toolbar.addWidget(self.font_size_spin)
        self.toolbar.addSeparator(); self._create_format_action(None, "Text Color", None, False, self._set_text_color, "color-text"); self._create_format_action(None, "Highlight Color", None, False, self._set_highlight_color, "color-fill")
        self.toolbar.addSeparator(); save_as_button = QPushButton("Save As..."); save_as_button.clicked.connect(self._save_note_as); self.toolbar.addWidget(save_as_button)
    def _create_format_action(self, text, tooltip, shortcut, checkable, triggered_func, icon_name=None):
        icon = QIcon.fromTheme(icon_name) if icon_name else QIcon(); action = QAction(icon, text, self) if text else QAction(icon, tooltip, self)
        action.setToolTip(tooltip); action.setCheckable(checkable); action.triggered.connect(triggered_func)
        if shortcut: action.setShortcut(shortcut)
        self.toolbar.addAction(action); return action
    def _merge_format(self, char_format: QTextCharFormat):
        cursor = self.notepad_text.textCursor();
        if not cursor.hasSelection(): cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(char_format); self.notepad_text.mergeCurrentCharFormat(char_format)
    def _set_text_bold(self, checked): fmt = QTextCharFormat(); fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal); self._merge_format(fmt)
    def _set_text_italic(self, checked): fmt = QTextCharFormat(); fmt.setFontItalic(checked); self._merge_format(fmt)
    def _set_text_underline(self, checked): fmt = QTextCharFormat(); fmt.setFontUnderline(checked); self._merge_format(fmt)
    def _set_font_family(self, font): fmt = QTextCharFormat(); fmt.setFontFamily(font.family()); self._merge_format(fmt)
    def _set_font_size(self, size): fmt = QTextCharFormat(); fmt.setFontPointSize(size); self._merge_format(fmt)
    def _set_text_color(self):
        color = QColorDialog.getColor(self.notepad_text.textColor(), self)
        if color.isValid(): fmt = QTextCharFormat(); fmt.setForeground(color); self._merge_format(fmt)
    def _set_highlight_color(self):
        color = QColorDialog.getColor(self.notepad_text.textBackgroundColor(), self)
        if color.isValid(): fmt = QTextCharFormat(); fmt.setBackground(color); self._merge_format(fmt)
    @Slot()
    def _update_toolbar_state(self):
        fmt = self.notepad_text.currentCharFormat(); self._bold_action.setChecked(fmt.fontWeight() == QFont.Weight.Bold); self._italic_action.setChecked(fmt.fontItalic())
        self._underline_action.setChecked(fmt.fontUnderline()); self.font_combo.setCurrentFont(fmt.font()); self.font_size_spin.setValue(int(fmt.fontPointSize()))
    def _load_note(self):
        if os.path.exists(self.notepad_file_path):
            try:
                with open(self.notepad_file_path, 'r', encoding='utf-8') as f: self.notepad_text.setHtml(f.read())
            except Exception: pass
    @Slot()
    def _auto_save_note(self): self._save_note(self.notepad_file_path)
    def _save_note(self, filepath):
        try:
            with open(filepath, 'w', encoding='utf-8') as f: f.write(self.notepad_text.toHtml())
        except Exception as e: QMessageBox.warning(self, "Save Error", f"Failed to save notes: {e}")
    @Slot()
    def _save_note_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Notes As", self.notes_folder, "HTML Files (*.html);;Text Files (*.txt)")
        if file_path: self._save_note(file_path)
    def save_and_stop(self): self.save_timer.stop(); self._save_note(self.notepad_file_path)

class DeviceNode(QGraphicsItemGroup):
    def __init__(self, ip, mac, hostname=None, description=None, parent_widget=None):
        super().__init__()
        self.ip = ip
        self.mac = mac
        self.hostname = hostname
        self.description = description
        self.parent_widget = parent_widget
        
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable)
        
        base_color = QColor("#fec301")
        if description and ("switch" in description.lower() or "cisco" in description.lower()):
            base_color = QColor("#3498db")
        elif description and "router" in description.lower():
            base_color = QColor("#2ecc71")

        gradient = QRadialGradient(0, 0, 30)
        gradient.setColorAt(0, base_color.lighter(130))
        gradient.setColorAt(1, base_color)
        
        circle = QGraphicsEllipseItem(-30, -30, 60, 60)
        circle.setBrush(QBrush(gradient))
        circle.setPen(QPen(Qt.GlobalColor.black, 1))
        self.addToGroup(circle)
        
        self.create_icon(description)
        
        display_text = f"<b>{self.hostname}</b><br><small>{self.ip}</small>" if self.hostname else self.ip
        label = QGraphicsTextItem()
        label.setHtml(f"<div style='text-align: center;'>{display_text}</div>")
        font = QFont("Sans Serif", 8)
        label.setFont(font)
        label.setDefaultTextColor(Qt.GlobalColor.white if base_color.lightness() < 128 else Qt.GlobalColor.black)
        label.setPos(-label.boundingRect().width() / 2, 5)
        self.addToGroup(label)
        
        tooltip = f"IP: {self.ip}\nMAC: {self.mac}"
        if self.hostname: tooltip += f"\nHost: {self.hostname}"
        if self.description: tooltip += f"\nDesc: {self.description}"
        self.setToolTip(tooltip)

    def create_icon(self, description):
        icon_path = QPainterPath()
        desc = description.lower() if description else ""

        if "switch" in desc or "cisco" in desc:
            icon_path.moveTo(-15, -5); icon_path.lineTo(15, -5)
            icon_path.moveTo(-12, 0); icon_path.lineTo(-10, -5); icon_path.lineTo(-8, 0)
            icon_path.moveTo(-5, 0); icon_path.lineTo(-3, -5); icon_path.lineTo(-1, 0)
            icon_path.moveTo(2, 0); icon_path.lineTo(4, -5); icon_path.lineTo(6, 0)
            icon_path.moveTo(9, 0); icon_path.lineTo(11, -5); icon_path.lineTo(13, 0)
        elif "router" in desc:
            icon_path.addEllipse(-10, -10, 20, 20)
            icon_path.moveTo(-15, 0); icon_path.lineTo(15, 0)
            icon_path.moveTo(0, -15); icon_path.lineTo(0, 15)
        else:
            icon_path.addRect(-12, -8, 24, 16)
            icon_path.moveTo(-9, -4); icon_path.lineTo(-9, -2)
            icon_path.moveTo(-6, -4); icon_path.lineTo(-6, -2)

        icon = QGraphicsPathItem(icon_path)
        icon.setPen(QPen(Qt.GlobalColor.white, 2))
        icon.setPos(0, -10)
        self.addToGroup(icon)

    def mousePressEvent(self, event):
        title = f"Device Information: {self.hostname or self.ip}"
        info_text = f"IP Address: {self.ip}\n"
        info_text += f"MAC Address: {self.mac}\n"
        if self.hostname:
            info_text += f"SNMP Hostname: {self.hostname}\n"
        if self.description:
            info_text += f"SNMP Description: {self.description}\n"
        
        QMessageBox.information(self.parent_widget, title, info_text)
        super().mousePressEvent(event)

class TopologyMapperWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.discovery_worker = None
        self.nodes = []
        layout = QVBoxLayout(self)
        control_bar = QHBoxLayout()
        self.scan_btn = QPushButton("Start Network Discovery")
        self.status_label = QLabel("Ready to scan.")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_bar.addWidget(self.scan_btn)
        control_bar.addWidget(self.status_label)
        control_bar.addStretch()
        layout.addLayout(control_bar)
        layout.addWidget(self.progress_bar)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        layout.addWidget(self.view)
        self.scan_btn.clicked.connect(self._start_discovery)

    @Slot()
    def _start_discovery(self):
        if self.discovery_worker and self.discovery_worker.isRunning(): return
        self.scan_btn.setEnabled(False)
        self.scene.clear()
        self.nodes.clear()
        self.status_label.setText("Scanning network...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.discovery_worker = DiscoveryWorker()
        self.discovery_worker.host_found.connect(self._add_host_node)
        self.discovery_worker.scan_finished.connect(self._on_scan_finished)
        self.discovery_worker.status_update.connect(self.status_label.setText)
        self.discovery_worker.start()

    @Slot(dict)
    def _add_host_node(self, host_data):
        node = DeviceNode(
            host_data.get('ip', 'N/A'),
            host_data.get('mac', 'N/A'),
            host_data.get('hostname'),
            host_data.get('description'),
            parent_widget=self
        )
        self.nodes.append(node)
        self.scene.addItem(node)

    @Slot(str)
    def _on_scan_finished(self, message: str):
        self.status_label.setText(message)
        self.scan_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if not self.nodes:
            return
            
        num_nodes = len(self.nodes)
        if num_nodes == 1:
            self.nodes[0].setPos(0,0)
        else:
            radius = 35 * num_nodes
            angle_step = (2 * math.pi) / num_nodes
            for i, node in enumerate(self.nodes):
                angle = i * angle_step
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                node.setPos(x, y)
        
        QTimer.singleShot(100, self.fit_view)

    def fit_view(self):
        if not self.nodes: return
        rect = self.scene.itemsBoundingRect()
        if rect.isValid():
            self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        
    def apply_settings(self, settings: dict): pass

class VulnerabilityScannerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.worker = None; layout = QVBoxLayout(self)
        input_layout = QHBoxLayout(); self.keyword_input = QLineEdit(); self.keyword_input.setPlaceholderText("e.g., Apache 2.4.51 or OpenSSH 8.2")
        self.search_btn = QPushButton("Search for CVEs"); input_layout.addWidget(QLabel("Software Keyword:")); input_layout.addWidget(self.keyword_input); input_layout.addWidget(self.search_btn)
        layout.addLayout(input_layout); self.results_table = QTableWidget(); self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["CVE ID", "Severity", "Description", "Published"]); self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.results_table.setEditTriggers(QAbstractItemView.EditTriggers.NoEditTriggers)
        self.results_table.setWordWrap(True); self.results_table.verticalHeader().setVisible(False); layout.addWidget(self.results_table)
        self.status_label = QLabel("Ready. Search the NIST NVD for published vulnerabilities."); layout.addWidget(self.status_label)
        self.search_btn.clicked.connect(self.start_search); self.keyword_input.returnPressed.connect(self.start_search)
    def start_search(self):
        keyword = self.keyword_input.text().strip()
        if not keyword: QMessageBox.warning(self, "Input Error", "Please enter a software product to search for."); return
        if self.worker and self.worker.isRunning(): return
        self.search_btn.setEnabled(False); self.status_label.setText(f"Searching for vulnerabilities related to '{keyword}'..."); self.results_table.setRowCount(0)
        self.worker = CveSearchWorker(keyword); self.worker.result_ready.connect(self.display_results); self.worker.error_occurred.connect(self.on_error); self.worker.start()
    @Slot(dict)
    def display_results(self, data):
        self.search_btn.setEnabled(True); vulnerabilities = data.get('vulnerabilities', [])
        if not vulnerabilities: self.status_label.setText(f"No vulnerabilities found for '{self.keyword_input.text().strip()}'."); return
        self.results_table.setRowCount(len(vulnerabilities))
        for row, item in enumerate(vulnerabilities):
            cve = item.get('cve', {}); cve_id = cve.get('id', 'N/A'); published_date = cve.get('published', 'N/A').split('T')[0]
            description = next((d.get('value', 'N/A') for d in cve.get('descriptions', []) if d.get('lang') == 'en'), 'N/A')
            severity = "N/A"
            if cvss_metrics := cve.get('metrics', {}).get('cvssMetricV31', []):
                base_severity = cvss_metrics[0].get('cvssData', {}).get('baseSeverity', 'N/A'); base_score = cvss_metrics[0].get('cvssData', {}).get('baseScore', 'N/A')
                severity = f"{base_severity} ({base_score})"
            self.results_table.setItem(row, 0, QTableWidgetItem(cve_id)); self.results_table.setItem(row, 1, QTableWidgetItem(severity))
            self.results_table.setItem(row, 2, QTableWidgetItem(description)); self.results_table.setItem(row, 3, QTableWidgetItem(published_date))
        self.results_table.resizeRowsToContents(); self.status_label.setText(f"Search complete. Displaying {len(vulnerabilities)} results.")
    @Slot(str)
    def on_error(self, error_message): self.search_btn.setEnabled(True); self.status_label.setText(f"Error: {error_message}")
    def apply_settings(self, settings: dict): pass

class PasswordCheckerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); layout = QVBoxLayout(self); input_layout = QHBoxLayout(); self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password); self.show_password_btn = QPushButton("Show"); self.show_password_btn.setCheckable(True)
        input_layout.addWidget(QLabel("Password:")); input_layout.addWidget(self.password_input); input_layout.addWidget(self.show_password_btn)
        layout.addLayout(input_layout); self.results_text = QTextEdit(); self.results_text.setReadOnly(True); layout.addWidget(self.results_text)
        self.password_input.textChanged.connect(self.check_password); self.show_password_btn.toggled.connect(self.toggle_password_visibility); self.check_password("")
    @Slot(str)
    def check_password(self, password):
        if not password: self.results_text.setPlainText("Enter a password to analyze its strength."); return
        results = zxcvbn(password); score = results['score']; crack_time = results['crack_times_display']['offline_slow_hashing_1e4_per_second']
        feedback = results['feedback']['warning']; suggestions = "\n".join(f"- {s}" for s in results['feedback']['suggestions'])
        score_text = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]; report = (f"--- Password Strength Analysis ---\n\nScore: {score}/4 ({score_text[score]})\n"
                  f"Estimated time to crack: {crack_time}\n\n")
        if feedback: report += f"Warning:\n- {feedback}\n\n"
        if suggestions: report += f"Suggestions:\n{suggestions}"
        self.results_text.setPlainText(report)
    @Slot(bool)
    def toggle_password_visibility(self, checked):
        self.password_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
    def apply_settings(self, settings: dict): pass

class HashToolWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); layout = QVBoxLayout(self); self.input_text = QPlainTextEdit(); self.input_text.setPlaceholderText("Enter text here to hash...")
        layout.addWidget(self.input_text, 1); control_layout = QHBoxLayout(); self.hash_algo_combo = QComboBox(); self.hash_algo_combo.addItems(["MD5", "SHA1", "SHA256", "SHA512"])
        self.calculate_btn = QPushButton("Calculate Hashes"); self.load_file_btn = QPushButton("Hash a File..."); control_layout.addWidget(QLabel("Algorithm (for cracker):"))
        control_layout.addWidget(self.hash_algo_combo); control_layout.addWidget(self.calculate_btn); control_layout.addWidget(self.load_file_btn); layout.addLayout(control_layout)
        self.output_layout = QHBoxLayout(); self.md5_output = self._create_output_field("MD5:"); self.sha1_output = self._create_output_field("SHA1:")
        self.sha256_output = self._create_output_field("SHA256:"); self.sha512_output = self._create_output_field("SHA512:"); layout.addLayout(self.output_layout)
        cracker_layout = QHBoxLayout(); self.hash_to_crack_input = QLineEdit(); self.hash_to_crack_input.setPlaceholderText("Paste hash here to crack...")
        self.wordlist_btn = QPushButton("Load Wordlist..."); self.crack_btn = QPushButton("Crack Hash"); cracker_layout.addWidget(QLabel("Crack Hash:"))
        cracker_layout.addWidget(self.hash_to_crack_input); cracker_layout.addWidget(self.wordlist_btn); cracker_layout.addWidget(self.crack_btn); layout.addLayout(cracker_layout)
        self.cracker_status = QLabel("Ready. Load a wordlist to attempt dictionary attack."); layout.addWidget(self.cracker_status); self.wordlist_path = None
        self.calculate_btn.clicked.connect(self._calculate_text_hashes); self.load_file_btn.clicked.connect(self._load_and_hash_file)
        self.wordlist_btn.clicked.connect(self._load_wordlist); self.crack_btn.clicked.connect(self._start_crack)
    def _create_output_field(self, label_text):
        h_layout = QHBoxLayout(); h_layout.addWidget(QLabel(label_text)); line_edit = QLineEdit(); line_edit.setReadOnly(True); h_layout.addWidget(line_edit); self.output_layout.addLayout(h_layout); return line_edit
    @Slot()
    def _calculate_text_hashes(self):
        text = self.input_text.toPlainText().encode('utf-8')
        if not text: return
        self.md5_output.setText(hashlib.md5(text).hexdigest()); self.sha1_output.setText(hashlib.sha1(text).hexdigest())
        self.sha256_output.setText(hashlib.sha256(text).hexdigest()); self.sha512_output.setText(hashlib.sha512(text).hexdigest())
    @Slot()
    def _load_and_hash_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select a file to hash")
        if not filepath: return
        self.input_text.setPlainText(f"--- Hashing File ---\n{filepath}"); md5, sha1, sha256, sha512 = hashlib.md5(), hashlib.sha1(), hashlib.sha256(), hashlib.sha512()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192): md5.update(chunk); sha1.update(chunk); sha256.update(chunk); sha512.update(chunk)
            self.md5_output.setText(md5.hexdigest()); self.sha1_output.setText(sha1.hexdigest()); self.sha256_output.setText(sha256.hexdigest()); self.sha512_output.setText(sha512.hexdigest())
        except Exception as e: QMessageBox.critical(self, "File Error", f"Could not read or hash the file:\n{e}")
    @Slot()
    def _load_wordlist(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select a Wordlist File", "", "Text Files (*.txt);;All Files (*)")
        if filepath: self.wordlist_path = filepath; self.cracker_status.setText(f"Loaded wordlist: {os.path.basename(filepath)}")
    @Slot()
    def _start_crack(self):
        hash_to_crack = self.hash_to_crack_input.text().strip().lower()
        if not self.wordlist_path: QMessageBox.warning(self, "Wordlist Missing", "Please load a wordlist file first."); return
        if not hash_to_crack: QMessageBox.warning(self, "Input Missing", "Please paste a hash to crack."); return
        algo_name = self.hash_algo_combo.currentText().lower(); hash_func = getattr(hashlib, algo_name); self.cracker_status.setText("Cracking... this may take a while."); QApplication.processEvents()
        found = False
        try:
            with open(self.wordlist_path, 'r', errors='ignore') as f:
                for line in f:
                    word = line.strip(); hashed_word = hash_func(word.encode('utf-8')).hexdigest()
                    if hashed_word == hash_to_crack:
                        self.cracker_status.setText(f"Success! Password found: {word}"); QMessageBox.information(self, "Success", f"The password for the hash is:\n\n{word}"); found = True; break
            if not found: self.cracker_status.setText("Failed. Password not found in the wordlist.")
        except Exception as e: self.cracker_status.setText(f"Error: Could not process wordlist."); QMessageBox.critical(self, "Error", f"An error occurred: {e}")
    def apply_settings(self, settings: dict): pass
