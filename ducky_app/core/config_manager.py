import os
import json
from PySide6.QtCore import QStandardPaths

class ConfigManager:
    """Manages application settings, colors, and fonts."""
    def __init__(self):
        self.config_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, "ducky_config.json")
        self._config = self._load_config()

    def _load_config(self):
        default_config = {
            "terminal_bg_color": "#282C34",
            "terminal_font_color": "#ABB2BF",
            "terminal_font_family": "Monospace",
            "terminal_font_size": 10,
            "session_folder": os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation), "Ducky_Sessions"),
            "notes_folder": os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation), "Ducky_Notes"),
            "default_baudrate": 9600,
            "app_theme": "dark"
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                for key, default_val in default_config.items():
                    if key not in loaded_config:
                        loaded_config[key] = default_val
                return loaded_config
            except json.JSONDecodeError:
                print(f"Warning: Could not decode config file {self.config_file}. Using defaults.")
                return default_config
        return default_config

    def save_config(self):
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self._config, f, indent=4)

    def get_setting(self, key):
        return self._config.get(key)

    def set_setting(self, key, value):
        self._config[key] = value
        self.save_config()