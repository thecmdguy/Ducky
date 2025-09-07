import os
import json
from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QMessageBox

class ConfigManager:
    def __init__(self):
        self.config_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, "ducky_config.json")
        self._config = self._load_config()

    def _get_default_config(self):
        return {
            "terminal_bg_color": "#282C34",
            "terminal_font_color": "#ABB2BF",
            "terminal_font_family": "Monospace",
            "terminal_font_size": 10,
            "session_folder": os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation), "Ducky_Sessions"),
            "notes_folder": os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation), "Ducky_Notes"),
            "default_baudrate": 9600,
            "app_theme": "dark"
        }

    def _load_config(self):
        default_config = self._get_default_config()
        if not os.path.exists(self.config_file):
            return default_config

        try:
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
            
            for key, default_val in default_config.items():
                if key not in loaded_config:
                    loaded_config[key] = default_val
            return loaded_config
        except json.JSONDecodeError:
            QMessageBox.warning(
                None,
                "Configuration Error",
                f"Your configuration file at {self.config_file} is corrupted and could not be loaded.\n\n"
                "Default settings will be used for this session. Please fix or delete the file to save new settings."
            )
            return default_config
        except Exception:
            return default_config

    def save_config(self):
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=4)
        except IOError as e:
             QMessageBox.critical(
                None,
                "Configuration Save Error",
                f"Could not save configuration to {self.config_file}.\n\nError: {e}"
            )

    def get_setting(self, key):
        return self._config.get(key)

    def set_setting(self, key, value):
        self._config[key] = value