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
import psutil
from PySide6.QtCore import Signal, QThread
from scapy.all import get_if_addr, conf, sr, IP, ICMP, getmacbyip

try:
    from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd
    SNMP_AVAILABLE = True
except ImportError:
    SNMP_AVAILABLE = False

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
            except (serial.SerialException, paramiko.SSHException, OSError) as e:
                self.connection_lost.emit(f"Connection error: {e}"); break
            
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
            except OSError as e:
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
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e: self.result_output.emit(f"An error occurred during ping: {e}")
    def _run_traceroute(self):
        try:
            cmd = ['tracert' if sys.platform.startswith('win') else 'traceroute', self.target]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0)
            for line in iter(proc.stdout.readline, ''):
                if not self._running: proc.terminate(); break
                self.result_output.emit(line)
            proc.wait()
            if proc.returncode != 0 and self._running: self.result_output.emit(f"Traceroute failed: {proc.stderr.read()}")
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e: self.result_output.emit(f"An error occurred during traceroute: {e}")
    def _run_port_scan(self):
        if not self.ports or len(self.ports) != 2: self.result_output.emit("Error: Invalid port range."); return
        start_port, end_port = self.ports; open_ports = []
        for port in range(start_port, end_port + 1):
            if not self._running: self.result_output.emit("\nPort scan interrupted."); break
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.1)
                    if s.connect_ex((self.target, port)) == 0: open_ports.append(str(port)); self.result_output.emit(f"Port {port}: OPEN\n")
            except socket.error:
                pass
        if self._running:
            if open_ports: self.result_output.emit(f"\nSummary of Open Ports: {', '.join(open_ports)}\n")
            else: self.result_output.emit("\nNo open ports found.\n")
    def stop(self): self._running = False; self.wait(2000)

class DiscoveryWorker(QThread):
    host_found = Signal(dict)
    scan_finished = Signal(str)
    status_update = Signal(str)
    def __init__(self, subnet=None, parent=None):
        super().__init__(parent)
        self.subnet = subnet

    def get_snmp_data(self, ip_addr):
        if not SNMP_AVAILABLE:
            return None, None

        hostname, description = None, None
        community_string = 'public'
        
        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(community_string, mpModel=0),
                UdpTransportTarget((ip_addr, 161)),
                ContextData(),
                ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0)),
                ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0)),
                lookupMib=False, timeout=0.5, retries=1
            )
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            if not errorIndication and not errorStatus:
                for varBind in varBinds:
                    oid, value = varBind
                    if '1.3.6.1.2.1.1.5.0' in str(oid): hostname = str(value)
                    elif '1.3.6.1.2.1.1.1.0' in str(oid): description = str(value)
        except Exception:
            pass
        return hostname, description

    def get_active_network(self):
        primary_ip, primary_netmask = None, None
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(0.1)
                s.connect(('8.8.8.8', 1))
                primary_ip = s.getsockname()[0]
        except socket.error:
            for interface, snics in psutil.net_if_addrs().items():
                for snic in snics:
                    if snic.family == socket.AF_INET and not snic.address.startswith("127.") and not snic.address.startswith("169.254."):
                        if snic.netmask: return snic.address, snic.netmask
            return None, None

        for interface, snics in psutil.net_if_addrs().items():
            for snic in snics:
                if snic.address == primary_ip:
                    primary_netmask = snic.netmask
                    break
            if primary_netmask: break
        return primary_ip, primary_netmask

    def run(self):
        try:
            net = None
            if self.subnet:
                net = ipaddress.ip_network(self.subnet, strict=False)
            else:
                host_ip, netmask = self.get_active_network()
                if not host_ip or not netmask:
                    raise IOError("Could not find an active network interface.")
                net = ipaddress.ip_network(f"{host_ip}/{netmask}", strict=False)
                self.status_update.emit(f"Auto-detected network: {net.with_prefixlen}. Starting scan...")
            
            if net.num_addresses > 4096:
                self.scan_finished.emit(f"Error: Subnet {net.with_prefixlen} is too large to scan.")
                return

            target_ips = [str(ip) for ip in net.hosts()]
            if not target_ips:
                self.scan_finished.emit("Scan finished. No hosts to scan in the subnet.")
                return

            self.status_update.emit(f"Pinging {len(target_ips)} hosts on {net.with_prefixlen}...")
            
            ans, unans = sr(IP(dst=target_ips)/ICMP(), timeout=2, verbose=0)
            
            self.status_update.emit(f"Scan complete. Found {len(ans)} responsive hosts. Querying for details...")

            for sent, received in ans:
                ip_addr = received.src
                mac_addr = getmacbyip(ip_addr)
                hostname, description = self.get_snmp_data(ip_addr)
                
                self.host_found.emit({
                    'ip': ip_addr, 
                    'mac': mac_addr if mac_addr else 'N/A',
                    'hostname': hostname,
                    'description': description
                })
                time.sleep(0.01)
                
            self.scan_finished.emit(f"Discovery finished. Found {len(ans)} devices.")
        except (IOError, ValueError, socket.herror, RuntimeError) as e:
            self.scan_finished.emit(f"An error occurred during scan: {e}")

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