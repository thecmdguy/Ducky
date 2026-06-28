
<div align="center">
  <img src="src/ducky_app/assets/ducky_icon.png" alt="Ducky Logo" width="120" />
  <h1>Ducky - The Ultimate Networking Tool</h1>
  <p>
    An open-source, all-in-one desktop application for network engineers, students, and enthusiasts.
  </p>

  <!-- Badges -->
  <p>
    <img src="https://img.shields.io/badge/Python-3.8+-blue.svg?logo=python&logoColor=yellow" alt="Python Version">
    <img src="https://img.shields.io/badge/Qt_for_Python-PySide6-brightgreen.svg?logo=qt" alt="PySide6">
    <img src="https://img.shields.io/badge/Version-1.5-orange.svg" alt="Version 1.4">
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
    <a href="https://github.com/thecmdguy/Ducky/issues"><img src="https://img.shields.io/github/issues/thecmdguy/Ducky" alt="Issues"></a>
    <a href="https://github.com/thecmdguy/Ducky/pulls"><img src="https://img.shields.io/github/issues-pr/thecmdguy/Ducky" alt="Pull Requests"></a>
  </p>
</div>

## Star History

<a href="https://www.star-history.com/?repos=thecmdguy%2FDucky&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=thecmdguy/Ducky&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=thecmdguy/Ducky&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=thecmdguy/Ducky&type=date&legend=top-left" />
 </picture>
</a>

---

Ducky is a powerful desktop application that combines essential networking, security, and diagnostic utilities into a single, intuitive graphical interface with customizable themes. Stop switching between dozens of tools and get everything you need in one place.

### Support Ducky
If you find Ducky useful and would like to support its development, consider making a donation!
<p align="center">
<a href="https://www.paypal.com/paypalme/Gtsnobiladze" target="_blank">
<img src="https://img.shields.io/badge/Donate-Support%20Ducky-blueviolet?style=for-the-badge&logo=paypal&logoColor=white" alt="Donate Button">
</a>
<a href="https://ko-fi.com/thecmdguy" target="_blank">
<img src="https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20coffee-ff5e5e?style=for-the-badge&logo=ko-fi&logoColor=white" alt="Ko-fi Button">
</a>
</p>

![Ducky Screenshot](https://github.com/thecmdguy/Ducky/blob/main/src/ducky_app/assets/demo.png?raw=true)
*(Ducky v1.5 — dark theme)*

---

## Features

### Terminal
| Tool | Description |
|------|-------------|
| **Multi-Protocol Terminal** | Connect via SSH, Telnet, and Serial (COM) in a modern tabbed interface with session save/load |

### Network Diagnostics
| Tool | Description |
|------|-------------|
| **Network Monitor** | Live CPU, memory, and network I/O stats for your local machine |
| **Ping** | Send ICMP pings to any host and view round-trip results |
| **Traceroute** | Trace the full hop path to any destination |
| **Port Scanner** | Multi-threaded TCP port scanner with custom port range support |
| **Subnet Calculator** | Compute network address, broadcast, usable host range, and more from any CIDR |
| **Wake-on-LAN** | Send magic packets to boot remote machines by MAC address |

### DNS & Email
| Tool | Description |
|------|-------------|
| **DNS Lookup** | Query A, AAAA, MX, NS, TXT, CNAME, SOA, PTR, and SRV records |
| **MX Lookup** | Discover mail exchange servers for any domain |
| **DNS Propagation** | Check DNS resolution across 8 global resolvers simultaneously |
| **Whois** | Raw Whois registration data for domains and IP addresses |
| **SMTP Test** | Test SMTP server connectivity on any port and read the EHLO banner |

### Network & IP
| Tool | Description |
|------|-------------|
| **IP Info** | Geolocation, ISP, ASN, and reverse DNS for any IP address |
| **MAC Vendor** | Identify the hardware manufacturer from any MAC address OUI |
| **ARP / Route Table** | View the local ARP cache and system routing table |
| **Topology Map** | Auto-discover your network with ICMP + SNMP and render a live graphical device map |
| **Device Scan** | List all active hosts on your LAN with IP, MAC, and hostname |

### Website Analysis
| Tool | Description |
|------|-------------|
| **HTTP Headers** | Fetch and inspect full HTTP response headers for any URL |
| **SSL Inspector** | View TLS certificate details, validity, issuer, SANs, and cipher info |

### Security
| Tool | Description |
|------|-------------|
| **Blacklist Check** | Check an IP against 10 DNSBL spam blacklist servers simultaneously |
| **CVE Scan** | Search the NIST NVD for published vulnerabilities by product keyword |
| **Password Checker** | Analyze password strength with estimated crack time and improvement tips |
| **Hash Tool** | Calculate MD5, SHA1, SHA256, SHA512 hashes for text or files; includes a dictionary cracker |

### Utilities
| Tool | Description |
|------|-------------|
| **Scratchpad Notes** | Dockable rich-text notepad with formatting tools and auto-save |

---

## Getting Started

### Prerequisites

- Python 3.8 or newer (64-bit recommended)
- `pip` and `venv` (included with modern Python)

### Installation & Running

1. **Clone the repository**
   ```bash
   git clone https://github.com/thecmdguy/Ducky.git
   cd Ducky
   ```

2. **Create a virtual environment and install dependencies**

   **Windows:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -e .
   ```

   **macOS / Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

3. **Run Ducky**

   **Windows:**
   ```powershell
   .\venv\Scripts\python.exe src\ducky_app\main.py
   ```

   **macOS / Linux:**
   ```bash
   python src/ducky_app/main.py
   ```

> **Note on the `libpcap` warning:** You may see `WARNING: No libpcap provider available!` on first run. This is a harmless Scapy message and can be safely ignored. Ducky works perfectly without it.

> **Note on Topology Map / Device Scan:** These tools use raw ICMP packets and require administrator / root privileges to scan the network.

---

## Building the Windows Installer

Run the included build script from the `Ducky/` folder in PowerShell:

```powershell
.\build_installer.ps1
```

This will automatically:
1. Verify the virtual environment
2. Install PyInstaller and Pillow if missing
3. Convert the PNG icon to a multi-resolution `.ico`
4. Bundle the app with PyInstaller → `dist\Ducky\`
5. Install Inno Setup 6 via `winget` if not found
6. Compile the installer → `installer\Ducky-Setup-1.5.0.exe`

---

## Customization

- **Themes** — Switch between dark and light themes via **Settings → Preferences**
- **Terminal** — Customize font family, font size, and colors per session
- **Sessions** — Save and reload terminal sessions from the left panel

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
