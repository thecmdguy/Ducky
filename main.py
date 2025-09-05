import sys
import os
from PySide6.QtWidgets import QApplication

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ducky_app.ui.main_window import DuckyMainWindow

def run():
    """Initializes and runs the Ducky application."""
    app = QApplication(sys.argv)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "ducky_icon.png")
    
    window = DuckyMainWindow(icon_path=icon_path)

    if not window.initialized_successfully:
        sys.exit(1)
        
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()
