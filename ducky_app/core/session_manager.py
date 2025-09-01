import os
import json
import time
from ducky_app.core.config_manager import ConfigManager

class SessionManager:
    """Manages saving and loading of terminal sessions."""
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.base_session_dir = self.config_manager.get_setting("session_folder")
        os.makedirs(self.base_session_dir, exist_ok=True)

    def get_session_dir(self):
        return self.base_session_dir

    def create_session_folder(self, parent_path, folder_name):
        new_path = os.path.join(parent_path, folder_name)
        if not os.path.exists(new_path):
            os.makedirs(new_path)
            return True, new_path
        return False, f"Folder '{folder_name}' already exists."

    def save_session(self, folder_path, session_name, log_data, metadata=None):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_session_name = "".join(c for c in session_name if c.isalnum() or c in (' ', '.', '_', '-')).rstrip().replace(' ', '_')
        
        log_filename = f"{safe_session_name}_{timestamp}.log"
        meta_filename = f"{safe_session_name}_{timestamp}.json"
        log_filepath = os.path.join(folder_path, log_filename)
        meta_filepath = os.path.join(folder_path, meta_filename)

        if os.path.exists(log_filepath) or os.path.exists(meta_filepath):
             return False, f"A session named '{safe_session_name}_{timestamp}' already exists."

        try:
            with open(log_filepath, 'w', encoding='utf-8') as f:
                f.write(log_data)
            
            full_metadata = {
                "name": session_name,
                "filename_base": safe_session_name,
                "timestamp": timestamp,
                "log_file": log_filename,
                "log_path": log_filepath,
                "meta_file": meta_filename,
                "meta_path": meta_filepath,
                "created_at": time.time(),
                "updated_at": time.time(),
                **(metadata if metadata else {})
            }
            with open(meta_filepath, 'w', encoding='utf-8') as f:
                json.dump(full_metadata, f, indent=4)
            return True, log_filepath
        except Exception as e:
            return False, f"Error saving session: {e}"

    def load_session_log(self, log_filepath):
        try:
            with open(log_filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error loading log: {e}"