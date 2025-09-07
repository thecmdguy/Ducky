import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt

from ducky_app.utils.helpers import check_dependencies
from ducky_app.ui.main_window import DuckyMainWindow

def run_as_admin():
    if sys.platform == 'win32':
        try:
            if ctypes.windll.shell32.IsUserAnAdmin() == 0:
                script = os.path.abspath(sys.argv[0])
                params = ' '.join([script] + sys.argv[1:])
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
                sys.exit(0)
        except Exception:
            return
    return

def run():
    run_as_admin()
    
    app = QApplication(sys.argv)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    splash_image_path = os.path.join(base_dir, 'assets', 'splash.png')
    
    splash = None
    if os.path.exists(splash_image_path):
        splash_pixmap = QPixmap(splash_image_path)
        splash = QSplashScreen(splash_pixmap)
        splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    else:
        splash = QSplashScreen()

    status_font = QFont("Sans Serif", 10)
    splash.setFont(status_font)
    splash.show()
    app.processEvents()
    
    if not check_dependencies(splash):
        splash.close()
        sys.exit(1)
    
    icon_path = os.path.join(base_dir, 'assets', 'ducky_icon.png')
    window = DuckyMainWindow(icon_path=icon_path)
    
    splash.finish(window)
        
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()