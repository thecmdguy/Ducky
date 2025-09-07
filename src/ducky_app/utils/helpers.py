import time
import importlib.util
from PySide6.QtWidgets import QSplashScreen, QMessageBox, QApplication
from PySide6.QtCore import Qt

def check_dependencies(splash_screen: QSplashScreen) -> bool:
    required = {
        "PySide6": "PySide6", 
        "serial": "pyserial", 
        "psutil": "psutil",
        "scapy": "scapy",
        "requests": "requests",
        "zxcvbn": "zxcvbn",
        "paramiko": "paramiko",
        "telnetlib3": "telnetlib3",
        "pysnmp": "pysnmp"
    }
    missing = []
    
    splash_screen.showMessage("Checking Python dependencies...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
    QApplication.instance().processEvents()
    time.sleep(0.5)

    for module, pip_name in required.items():
        splash_screen.showMessage(f"Checking for '{module}'...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
        QApplication.instance().processEvents()
        time.sleep(0.2)
        if importlib.util.find_spec(module) is None:
            missing.append(pip_name)
    
    if missing:
        error_msg = (
            "The following Python packages are missing:\n\n"
            + "\n".join(f"- {mod}" for mod in missing)
            + f"\n\nPlease install them:\n'pip install {' '.join(missing)}'"
        )
        QMessageBox.critical(None, "Dependency Error", error_msg)
        return False
    
    splash_screen.showMessage("All dependencies met. Starting...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
    QApplication.instance().processEvents()
    time.sleep(1)
    
    return True