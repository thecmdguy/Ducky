import sys
import time
import subprocess
import socket
import serial
from PySide6.QtCore import Signal, QThread

class SerialReaderThread(QThread):
    """Thread to continuously read data from the serial port."""
    data_received = Signal(bytes)
    status_message = Signal(str)
    connection_lost = Signal(str)

    def __init__(self, serial_port: serial.Serial, parent=None):
        super().__init__(parent)
        self.serial_port = serial_port
        self._running = True

    def run(self):
        self.status_message.emit(f"Connected to {self.serial_port.port}")
        while self._running and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read_all()
                    if data:
                        self.data_received.emit(data)
                time.sleep(0.01)
            except serial.SerialException as e:
                self._running = False
                self.connection_lost.emit(f"Serial error: {e}")
            except Exception as e:
                self._running = False
                self.connection_lost.emit(f"Unexpected error: {e}")
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except serial.SerialException:
                pass
        self.status_message.emit("Disconnected.")

    def stop(self):
        self._running = False
        self.wait()

class NetworkToolThread(QThread):
    """Generic thread for blocking network operations (ping, traceroute, port scan)."""
    result_output = Signal(str)
    scan_complete = Signal()

    def __init__(self, tool_type, target, ports=None, parent=None):
        super().__init__(parent)
        self.tool_type = tool_type
        self.target = target
        self.ports = ports
        self._running = True

    def run(self):
        self.result_output.emit(f"--- Starting {self.tool_type} on {self.target} ---\n")
        if self.tool_type == "ping": self._run_ping()
        elif self.tool_type == "traceroute": self._run_traceroute()
        elif self.tool_type == "port_scan": self._run_port_scan()
        if self._running:
            self.result_output.emit(f"\n--- {self.tool_type} Complete ---")
        self.scan_complete.emit()

    def _run_ping(self):
        try:
            cmd = ['ping', '-n' if sys.platform.startswith('win') else '-c', '4', self.target]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0)
            for line in iter(proc.stdout.readline, ''):
                if not self._running:
                    proc.terminate()
                    break
                self.result_output.emit(line)
            proc.wait()
            if proc.returncode != 0 and self._running:
                self.result_output.emit(f"Ping failed: {proc.stderr.read()}")
        except Exception as e:
            self.result_output.emit(f"An error occurred during ping: {e}")

    def _run_traceroute(self):
        try:
            cmd = ['tracert' if sys.platform.startswith('win') else 'traceroute', self.target]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0)
            for line in iter(proc.stdout.readline, ''):
                if not self._running:
                    proc.terminate()
                    break
                self.result_output.emit(line)
            proc.wait()
            if proc.returncode != 0 and self._running:
                self.result_output.emit(f"Traceroute failed: {proc.stderr.read()}")
        except Exception as e:
            self.result_output.emit(f"An error occurred during traceroute: {e}")

    def _run_port_scan(self):
        if not self.ports or len(self.ports) != 2:
            self.result_output.emit("Error: Invalid port range.")
            return
        start_port, end_port = self.ports
        open_ports = []
        for port in range(start_port, end_port + 1):
            if not self._running:
                self.result_output.emit("\nPort scan interrupted.")
                break
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.1)
                    if s.connect_ex((self.target, port)) == 0:
                        open_ports.append(str(port))
                        self.result_output.emit(f"Port {port}: OPEN\n")
            except Exception:
                pass
        if self._running:
            if open_ports: self.result_output.emit(f"\nSummary of Open Ports: {', '.join(open_ports)}\n")
            else: self.result_output.emit("\nNo open ports found.\n")

    def stop(self):
        self._running = False
        self.wait(2000)