import sys
import os
from PySide6.QtWidgets import QApplication

# This adds the project directory to Python's path, making 'ducky_app' importable.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now we can import from our application package
from ducky_app.ui.main_window import DuckyMainWindow

def run():
    """Initializes and runs the Ducky application."""
    app = QApplication(sys.argv)
    
    # Pass the base directory to find the icon
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "ducky_icon.png")
    
    # The splash screen and dependency checks are now handled inside the main window's __init__
    window = DuckyMainWindow(icon_path=icon_path)
    
    # If the window failed to initialize (e.g., missing dependencies), exit gracefully.
    if not window.initialized_successfully:
        sys.exit(1)
        
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()