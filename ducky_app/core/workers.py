# ducky_app/core/workers.py

import sys
import time
import subprocess
import socket
import serial
import requests
import json
import ipaddress
import paramiko
import asyncio
import telnetlib3
from PySide6.QtCore import Signal, QThread
from scapy.all import arping, get_if_addr, conf

class ConnectionReaderThread(QThread):
    data_received = Signal(bytes)
    connection_lost = Signal(str)

    def __init__(self, reader, writer, conn_type, parent=None):
        super().__init__(parent)
        self.reader = reader
        self.writer = writer
        self.conn_type = conn_type
        self._running = True

    def run(self):
        if self.conn_type == 'telnet':
            asyncio.run(self.run_telnet())
        else:
            self.run_sync()

    def run_sync(self):
        while self._running:
            try:
                if self.conn_type == 'serial' and self.reader.in_waiting > 0:
                    data = self.reader.read_all()
                    if data: self.data_received.emit(data)
                elif self.conn_type == 'ssh' and self.reader.recv_ready():
                    data = self.reader.recv(4096)
                    if data: self.data_received.emit(data)
                
                time.sleep(0.02)
            except (serial.SerialException, paramiko.SSHException) as e:
                self.connection_lost.emit(f"Connection error: {e}"); break
            except Exception as e:
                self.connection_lost.emit(f"An unexpected error occurred: {e}"); break

    async def run_telnet(self):
        while self._running:
            try:
                data = await self.reader.read(4096)
                if not data:
                    self.connection_lost.emit("Connection closed by remote host.")
                    break
                self.data_received.emit(data.encode('latin-1'))
            except asyncio.IncompleteReadError:
                self.connection_lost.emit("Connection closed unexpectedly.")
                break
            except Exception as e:
                self.connection_lost.emit(f"Telnet error: {e}"); break

    def stop(self):
        self._running = False
        if self.conn_type == 'telnet' and self.writer:
            self.writer.close()
        self.wait(500)

class NetworkToolThread(QThread):
    result_output = Signal(str)
    scan_complete = Signal()
    def __init__(self, tool_type, target, ports=None, parent=None):
        super().__init__(parent); self.tool_type, self.target, self.ports, self._running = tool_type, target, ports, True
    def run(self):
        self.result_output.emit(f"--- Starting {self.tool_type} on {self.target} ---\n")
        if self.tool_type == "ping": self._run_ping()
        elif self.tool_type == "traceroute": self._run_traceroute()
        elif self.tool_type == "port_scan": self._run_port_scan()
        if self._running: self.result_output.emit(f"\n--- {self.tool_type} Complete ---")
        self.scan_complete.emit()
    def _run_ping(self):
        try:
            cmd = ['ping', '-n' if sys.platform.startswith('win') else '-c', '4', self.target]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0)
            for line in iter(proc.stdout.readline, ''):
                if not self._running: proc.terminate(); break
                self.result_output.emit(line)
            proc.wait()
            if proc.returncode != 0 and self._running: self.result_output.emit(f"Ping failed: {proc.stderr.read()}")
        except Exception as e: self.result_output.emit(f"An error occurred during ping: {e}")
    def _run_traceroute(self):
        try:
            cmd = ['tracert' if sys.platform.startswith('win') else 'traceroute', self.target]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0)
            for line in iter(proc.stdout.readline, ''):
                if not self._running: proc.terminate(); break
                self.result_output.emit(line)
            proc.wait()
            if proc.returncode != 0 and self._running: self.result_output.emit(f"Traceroute failed: {proc.stderr.read()}")
        except Exception as e: self.result_output.emit(f"An error occurred during traceroute: {e}")
    def _run_port_scan(self):
        if not self.ports or len(self.ports) != 2: self.result_output.emit("Error: Invalid port range."); return
        start_port, end_port = self.ports; open_ports = []
        for port in range(start_port, end_port + 1):
            if not self._running: self.result_output.emit("\nPort scan interrupted."); break
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.1)
                    if s.connect_ex((self.target, port)) == 0: open_ports.append(str(port)); self.result_output.emit(f"Port {port}: OPEN\n")
            except Exception: pass
        if self._running:
            if open_ports: self.result_output.emit(f"\nSummary of Open Ports: {', '.join(open_ports)}\n")
            else: self.result_output.emit("\nNo open ports found.\n")
    def stop(self): self._running = False; self.wait(2000)

class DiscoveryWorker(QThread):
    host_found = Signal(dict); scan_finished = Signal(str); status_update = Signal(str)
    def __init__(self, subnet=None, parent=None): super().__init__(parent); self.subnet = subnet
    def run(self):
        target = self.subnet
        if not target:
            try:
                host_ip = get_if_addr(conf.iface); net = ipaddress.ip_network(f"{host_ip}/255.255.255.0", strict=False)
                target = str(net); self.status_update.emit(f"Auto-detected subnet: {target}. Starting ARP scan...")
            except Exception as e: self.scan_finished.emit(f"Error: Could not auto-detect network. Please specify a subnet. Details: {e}"); return
        try:
            answered, unanswered = arping(target, verbose=0)
            self.status_update.emit(f"Scan complete. Found {len(answered)} hosts.")
            for sent, received in answered:
                self.host_found.emit({'ip': received.psrc, 'mac': received.hwsrc}); time.sleep(0.01)
            self.scan_finished.emit(f"Discovery finished. Found {len(answered)} devices.")
        except Exception as e: self.scan_finished.emit(f"An error occurred during scan: {e}")

class CveSearchWorker(QThread):
    result_ready = Signal(dict); error_occurred = Signal(str)
    def __init__(self, keyword, parent=None): super().__init__(parent); self.keyword = keyword
    def run(self):
        base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"; params = {'keywordSearch': self.keyword, 'resultsPerPage': 20}
        try:
            response = requests.get(base_url, params=params, timeout=15); response.raise_for_status()
            self.result_ready.emit(response.json())
        except requests.exceptions.RequestException as e: self.error_occurred.emit(f"Network error: Could not connect to the NVD API.\nDetails: {e}")
        except json.JSONDecodeError: self.error_occurred.emit("API Error: Could not parse the response from the NVD API.")
        except Exception as e: self.error_occurred.emit(f"An unexpected error occurred: {e}")