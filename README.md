
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
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
    <a href="https://github.com/thecmdguy/Ducky/issues"><img src="https://img.shields.io/github/issues/thecmdguy/Ducky" alt="Issues"></a>
    <a href="https://github.com/thecmdguy/Ducky/pulls"><img src="https://img.shields.io/github/issues-pr/thecmdguy/Ducky" alt="Pull Requests"></a>
  </p>
</div>

---

Ducky is a powerful, Desktop application that combines several essential networking utilities into a single, intuitive graphical interface with customizable themes. Stop switching between dozens of windows and get everything you need in one place.

### Support Ducky
If you find Ducky useful and would like to support its development, consider making a donation! Your contributions help keep this project alive and continuously improved.
<p align="center">
<a href="https://www.paypal.com/paypalme/Gtsnobiladze" target="_blank">
<img src="https://img.shields.io/badge/Donate-Support%20Ducky-blueviolet?style=for-the-badge&logo=paypal&logoColor=white" alt="Donate Button">
</a>
<a href="https://ko-fi.com/thecmdguy" target="_blank">
<img src="https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20coffee-ff5e5e?style=for-the-badge&logo=ko-fi&logoColor=white" alt="Ko-fi Button">
</a>
</p>

![Ducky Screenshot](https://github.com/thecmdguy/Ducky/blob/main/src/ducky_app/assets/banner.png?raw=true)
*(A screenshot of the Ducky application in action with the dark theme)*

## Features

*   **Multi-Protocol Terminal**: Connect via SSH, Telnet, and Serial (COM) in a modern, tabbed interface.
*   **SNMP Topology Mapper**: Automatically discover your network with a ping and SNMP sweep. See a graphical map of your devices, color-coded by type, and click to view detailed information.
*   **Network Diagnostics**: A full suite of tools including a Subnet Calculator, Network Monitor (Ping, Traceroute), and a multi-threaded Port Scanner.
*   **Security Toolkit**: Look up CVEs from the NIST database, check password strength, and calculate file hashes (MD5, SHA1, SHA256, SHA512).
*   **Rich-Text Notepad**: Keep notes and reminders in a dockable widget with formatting tools and auto-save.
*   **Customizable UI**: Switch between a sleek dark theme and a clean light theme. Customize terminal colors and fonts to your liking.

## Getting Started

Follow these instructions to get Ducky running on your local machine.

### Prerequisites

*   Python 3.8 or newer (64-bit recommended for full feature support).
*   `pip` and `venv`, which are included with modern Python installations.

### Installation & Running

Follow these instructions to get Ducky running on your local machine.

1.  **Clone the Repository**
    Open your terminal and run:
    ```bash
    git clone https://github.com/thecmdguy/Ducky.git
    cd Ducky
    ```

2.  **Install and Run**
    It is highly recommended to use a virtual environment. This single command will create a virtual environment, install all dependencies from `pyproject.toml`, and make the `ducky` command available.

    **On Windows:**
    ```powershell
    # Create and activate a virtual environment
    python -m venv venv
    .\venv\Scripts\activate

    # Install the project in editable mode. This also installs all dependencies.
    pip install -e .

    # Run the application!
    ducky
    ```

    **On macOS / Linux:**
    ```bash
    # Create and activate a virtual environment
    python3 -m venv venv
    source venv/bin/activate

    # Install the project in editable mode.
    pip install -e .

    # Run the application
    ducky
    ```

> **A Note on the `libpcap` Warning:**
> When you run Ducky for the first time, you may see a console warning that says `WARNING: No libpcap provider available !`. This is a harmless message from the Scapy library and **can be safely ignored**. Ducky is designed to work perfectly without it.

By taking these two steps, you address the user's immediate problem and improve your project's documentation for everyone else.
