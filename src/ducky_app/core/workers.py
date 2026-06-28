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
import psutil
import re
import xml.etree.ElementTree as ET
import datetime
import urllib.parse
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

            try:
                ans, unans = sr(IP(dst=target_ips)/ICMP(), timeout=2, verbose=0)
            except PermissionError:
                self.scan_finished.emit(
                    "Error: Permission denied. Raw packet capture requires root/administrator privileges.\n"
                    "On Linux/macOS, run with sudo. On Windows, run as Administrator."
                )
                return
            except OSError as e:
                self.scan_finished.emit(
                    f"Error: Could not open network device: {e}\n"
                    "Try running the application with root/administrator privileges."
                )
                return

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
        except (IOError, ValueError, socket.herror, RuntimeError, PermissionError, OSError) as e:
            self.scan_finished.emit(f"Error: {e}")

class CveSearchWorker(QThread):
    result_ready = Signal(dict); error_occurred = Signal(str)
    def __init__(self, keyword, parent=None): super().__init__(parent); self.keyword = keyword
    def run(self):
        base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        now = datetime.datetime.now(datetime.timezone.utc)
        month_ago = now - datetime.timedelta(days=30)
        
        params = {
            'keywordSearch': self.keyword,
            'pubEndDate': now.isoformat().replace('+00:00', 'Z'),
            'pubStartDate': month_ago.isoformat().replace('+00:00', 'Z')
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=15); response.raise_for_status()
            self.result_ready.emit(response.json())
        except requests.exceptions.RequestException as e: self.error_occurred.emit(f"Network error: Could not connect to the NVD API.\nDetails: {e}")
        except json.JSONDecodeError: self.error_occurred.emit("API Error: Could not parse the response from the NVD API.")

class BlacklistWorker(QThread):
    """Check an IPv4 address against common DNSBL blacklist servers."""
    result_ready = Signal(dict)
    status = Signal(str)
    finished = Signal()

    SERVERS = [
        'zen.spamhaus.org',
        'bl.spamcop.net',
        'cbl.abuseat.org',
        'dnsbl.sorbs.net',
        'b.barracudacentral.org',
        'dnsbl-1.uceprotect.net',
        'spam.dnsbl.sorbs.net',
        'psbl.surriel.com',
        'dnsbl.dronebl.org',
        'all.s5h.net',
    ]

    def __init__(self, ip, parent=None):
        super().__init__(parent)
        self.ip = ip

    def run(self):
        try:
            reversed_ip = '.'.join(reversed(self.ip.split('.')))
            results = {}
            for server in self.SERVERS:
                self.status.emit(f"Checking {server}…")
                query = f"{reversed_ip}.{server}"
                try:
                    addrs = socket.getaddrinfo(query, None, socket.AF_INET)
                    addr = addrs[0][4][0] if addrs else '127.0.0.0'
                    results[server] = (True, addr)
                except socket.gaierror:
                    results[server] = (False, 'Clean')
                except Exception as e:
                    results[server] = (None, str(e))
            self.result_ready.emit(results)
        except Exception as e:
            self.result_ready.emit({'Error': (None, str(e))})
        self.finished.emit()


class IpInfoWorker(QThread):
    """IP geolocation and ASN lookup via ip-api.com (free, no key needed)."""
    result_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, ip='', parent=None):
        super().__init__(parent)
        self.ip = ip

    def run(self):
        try:
            fields = 'status,message,continent,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,query,reverse'
            url = f"http://ip-api.com/json/{self.ip}?fields={fields}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data.get('status') == 'fail':
                self.error_occurred.emit(data.get('message', 'Lookup failed.'))
            else:
                self.result_ready.emit(data)
        except Exception as e:
            self.error_occurred.emit(f'IP lookup failed: {e}')


class SmtpTestWorker(QThread):
    """Test SMTP connectivity: connect, read banner, send EHLO."""
    result_ready = Signal(str)

    def __init__(self, host, port=25, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port

    def run(self):
        lines = [
            f"Testing SMTP — {self.host}:{self.port}",
            '=' * 52,
        ]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(8)
            t0 = time.time()
            sock.connect((self.host, self.port))
            ms = int((time.time() - t0) * 1000)
            banner = sock.recv(1024).decode('utf-8', errors='replace').strip()
            lines += [f'Connected in {ms} ms', f'Server banner: {banner}', '']
            sock.sendall(b'EHLO ducky.probe\r\n')
            ehlo = sock.recv(4096).decode('utf-8', errors='replace').strip()
            lines += ['EHLO response:', ehlo, '']
            sock.sendall(b'QUIT\r\n')
            sock.close()
            lines.append('Result: SMTP port OPEN — server is responding correctly.')
        except ConnectionRefusedError:
            lines.append(f'REFUSED — nothing is listening on port {self.port}.')
        except socket.timeout:
            lines.append('TIMED OUT (8 s) — port may be firewalled.')
        except Exception as e:
            lines.append(f'Error: {e}')
        self.result_ready.emit('\n'.join(lines))


class DnsLookupWorker(QThread):
    result_ready = Signal(str)
    finished = Signal()

    RECORD_TYPES = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA', 'PTR', 'SRV']

    def __init__(self, host, record_type='A', parent=None):
        super().__init__(parent)
        self.host = host
        self.record_type = record_type

    def run(self):
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
            cmd = ['nslookup', f'-type={self.record_type}', self.host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10,
                                    creationflags=flags)
            output = (result.stdout + (result.stderr or '')).strip() or 'No results returned.'
            self.result_ready.emit(output)
        except FileNotFoundError:
            try:
                addrs = socket.getaddrinfo(self.host, None)
                seen, lines = set(), []
                for fam, _, _, _, addr in addrs:
                    ip = addr[0]
                    if ip not in seen:
                        seen.add(ip)
                        lines.append(f"{socket.AddressFamily(fam).name}: {ip}")
                self.result_ready.emit('\n'.join(lines) or 'No addresses found.')
            except Exception as e2:
                self.result_ready.emit(f'Error: {e2}')
        except Exception as e:
            self.result_ready.emit(f'Error: {e}')
        self.finished.emit()


class WhoisWorker(QThread):
    result_ready = Signal(str)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(self, query, parent=None):
        super().__init__(parent)
        self.query = query

    @staticmethod
    def _raw_whois(query, server):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(15)
            s.connect((server, 43))
            s.sendall((query + '\r\n').encode())
            chunks = []
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
        return b''.join(chunks).decode('utf-8', errors='replace')

    def run(self):
        try:
            query = self.query.strip()
            result = self._raw_whois(query, 'whois.iana.org')
            for line in result.splitlines():
                lower = line.lower()
                if lower.startswith('whois:') or lower.startswith('refer:'):
                    server = line.split(':', 1)[1].strip()
                    if server:
                        try:
                            result = self._raw_whois(query, server)
                        except Exception:
                            pass
                    break
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(f'Whois query failed: {e}')
        self.finished.emit()


class HttpHeadersWorker(QThread):
    result_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        try:
            url = self.url.strip()
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            resp = requests.get(
                url, timeout=15, allow_redirects=True,
                headers={'User-Agent': 'Ducky/1.3.0 (https://github.com/thecmdguy/Ducky)'}
            )
            self.result_ready.emit({
                'final_url': resp.url,
                'status': resp.status_code,
                'reason': resp.reason,
                'elapsed_ms': round(resp.elapsed.total_seconds() * 1000),
                'redirects': [r.url for r in resp.history],
                'headers': dict(resp.headers),
            })
        except requests.exceptions.SSLError as e:
            self.error_occurred.emit(f'SSL Error: {e}')
        except requests.exceptions.ConnectionError as e:
            self.error_occurred.emit(f'Connection Error: {e}')
        except requests.exceptions.Timeout:
            self.error_occurred.emit('Request timed out (15 s).')
        except Exception as e:
            self.error_occurred.emit(f'Error: {e}')


class SslCheckerWorker(QThread):
    result_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, host, port=443, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port

    def run(self):
        import ssl as _ssl, hashlib
        try:
            ctx = _ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = _ssl.CERT_OPTIONAL
            with socket.create_connection((self.host, self.port), timeout=10) as raw:
                with ctx.wrap_socket(raw, server_hostname=self.host) as tls:
                    cert = tls.getpeercert()
                    cipher = tls.cipher()
                    version = tls.version()
                    der = tls.getpeercert(binary_form=True)
            fp = hashlib.sha256(der).hexdigest().upper()
            sha256 = ':'.join(fp[i:i+2] for i in range(0, len(fp), 2))
            self.result_ready.emit({
                'cert': cert,
                'cipher': cipher,
                'version': version,
                'host': self.host,
                'port': self.port,
                'sha256': sha256,
            })
        except _ssl.SSLCertVerificationError as e:
            self.error_occurred.emit(f'Certificate verification failed: {e}')
        except socket.timeout:
            self.error_occurred.emit(f'Connection timed out to {self.host}:{self.port}')
        except Exception as e:
            self.error_occurred.emit(f'SSL check failed: {e}')


class ImportWorker(QThread):
    session_found = Signal(dict)
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        count = 0
        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()
            for session in root.findall('.//Session'):
                session_data = {}
                session_name_node = session.find("Name")
                if session_name_node is None: continue
                session_data['name'] = session_name_node.text

                options = {node.find('Name').text: node.find('Value').text for node in session.findall('.//Option') if node.find('Name') is not None and node.find('Value') is not None}

                protocol = options.get("Protocol Name")
                if protocol == "SSH2":
                    session_data['type'] = 'ssh'
                    session_data['host'] = options.get("Hostname")
                    session_data['port'] = int(options.get("Port", "22"))
                    session_data['username'] = options.get("Username")
                    session_data['password'] = ""
                    if session_data['host'] and session_data['username']:
                        self.session_found.emit(session_data)
                        count += 1
                elif protocol == "Telnet":
                    session_data['type'] = 'telnet'
                    session_data['host'] = options.get("Hostname")
                    session_data['port'] = int(options.get("Port", "23"))
                    if session_data['host']:
                        self.session_found.emit(session_data)
                        count += 1
        except ET.ParseError:
            self.error.emit("Failed to parse XML file. Ensure it is a valid SecureCRT export.")
        except Exception as e:
            self.error.emit(f"An unexpected error occurred during import: {e}")
        finally:
            self.finished.emit(count)


class WakeOnLanWorker(QThread):
    result_ready = Signal(str)

    def __init__(self, mac, broadcast='255.255.255.255', port=9, parent=None):
        super().__init__(parent)
        self.mac = mac
        self.broadcast = broadcast
        self.port = port

    def run(self):
        try:
            mac_clean = self.mac.replace(':', '').replace('-', '').replace('.', '')
            if len(mac_clean) != 12:
                self.result_ready.emit('Error: Invalid MAC address — expected 12 hex characters.')
                return
            mac_bytes = bytes.fromhex(mac_clean)
            magic = b'\xff' * 6 + mac_bytes * 16
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.settimeout(5)
                sock.sendto(magic, (self.broadcast, self.port))
            formatted_mac = ':'.join(mac_clean[i:i+2].upper() for i in range(0, 12, 2))
            self.result_ready.emit(
                f'Magic packet sent successfully!\n\n'
                f'  Target MAC  :  {formatted_mac}\n'
                f'  Broadcast   :  {self.broadcast}\n'
                f'  UDP Port    :  {self.port}\n'
                f'  Packet size :  {len(magic)} bytes\n\n'
                f'Note: The target device must be powered off but plugged in,\n'
                f'on the same network segment, and have Wake-on-LAN enabled\n'
                f'in its BIOS/UEFI firmware settings.'
            )
        except ValueError:
            self.result_ready.emit('Error: Invalid MAC address — could not parse hex bytes.')
        except Exception as e:
            self.result_ready.emit(f'Error sending magic packet: {e}')


class MacVendorWorker(QThread):
    result_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, mac, parent=None):
        super().__init__(parent)
        self.mac = mac

    def run(self):
        try:
            mac_clean = self.mac.replace(':', '').replace('-', '').replace('.', '').upper()
            if len(mac_clean) < 6:
                self.error_occurred.emit('Invalid MAC address — too short.')
                return
            oui = ':'.join(mac_clean[i:i+2] for i in range(0, 6, 2))
            url = f'https://api.macvendors.com/{urllib.parse.quote(oui)}'
            resp = requests.get(url, timeout=10, headers={'User-Agent': 'Ducky/1.4 (network toolkit)'})
            vendor = resp.text.strip() if resp.status_code == 200 else 'Unknown / Not in database'
            self.result_ready.emit({
                'mac': ':'.join(mac_clean[i:i+2] for i in range(0, 12, 2)) if len(mac_clean) == 12 else self.mac.upper(),
                'oui': oui,
                'vendor': vendor,
            })
        except requests.exceptions.Timeout:
            self.error_occurred.emit('Request timed out (10 s).')
        except Exception as e:
            self.error_occurred.emit(f'Vendor lookup failed: {e}')


class DnsPropagationWorker(QThread):
    row_ready = Signal(dict)
    finished = Signal(str)

    SERVERS = [
        ('Google',         '8.8.8.8'),
        ('Google 2',       '8.8.4.4'),
        ('Cloudflare',     '1.1.1.1'),
        ('Cloudflare 2',   '1.0.0.1'),
        ('OpenDNS',        '208.67.222.222'),
        ('Quad9',          '9.9.9.9'),
        ('Comodo',         '8.26.56.26'),
        ('Level3',         '4.2.2.2'),
    ]

    def __init__(self, domain, record_type='A', parent=None):
        super().__init__(parent)
        self.domain = domain
        self.record_type = record_type

    def _query(self, server_ip):
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
            result = subprocess.run(
                ['nslookup', f'-type={self.record_type}', self.domain, server_ip],
                capture_output=True, text=True, timeout=8, creationflags=flags
            )
            output = result.stdout + result.stderr
            lower = output.lower()

            if any(x in lower for x in ['nxdomain', "can't find", 'non-existent']):
                return False, 'NXDOMAIN'
            if not output.strip() or 'timed out' in lower:
                return None, 'Timeout'

            # Find the answer section (after server header), then extract IPs
            answer_part = output
            for marker in ['non-authoritative answer', 'authoritative answers']:
                idx = lower.find(marker)
                if idx != -1:
                    answer_part = output[idx:]
                    break

            ips = [m.group() for m in re.finditer(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', answer_part)
                   if m.group() != server_ip]
            if ips:
                return True, ', '.join(list(dict.fromkeys(ips))[:3])

            # Fall back to non-IP answer lines for MX/NS/TXT/CNAME records
            for line in answer_part.splitlines()[2:]:
                stripped = line.strip()
                if stripped and not stripped.lower().startswith(('server', 'address', 'non-auth')):
                    return True, stripped

            return True, 'Resolved'
        except subprocess.TimeoutExpired:
            return None, 'Timeout (8 s)'
        except Exception as e:
            return None, f'Error: {e}'

    def run(self):
        for name, ip in self.SERVERS:
            status, result = self._query(ip)
            self.row_ready.emit({'name': name, 'ip': ip, 'status': status, 'result': result})
        self.finished.emit(f'Propagation check complete for {self.domain} ({self.record_type})')


class ArpRouteTableWorker(QThread):
    result_ready = Signal(str, str)
    error_occurred = Signal(str)

    def run(self):
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
            if sys.platform.startswith('win'):
                arp_cmd   = ['arp', '-a']
                route_cmd = ['route', 'print']
            else:
                arp_cmd   = ['arp', '-n']
                route_cmd = ['ip', 'route']

            arp = subprocess.run(arp_cmd,   capture_output=True, text=True, timeout=10, creationflags=flags)
            rte = subprocess.run(route_cmd, capture_output=True, text=True, timeout=10, creationflags=flags)
            self.result_ready.emit(
                arp.stdout or arp.stderr or 'No ARP data available.',
                rte.stdout or rte.stderr or 'No routing data available.'
            )
        except Exception as e:
            self.error_occurred.emit(f'Error fetching network tables: {e}')
