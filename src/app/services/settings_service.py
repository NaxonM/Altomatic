
import json
import os

class SettingsService:
    """
    Manages loading and saving application settings from a JSON file.
    """
    def __init__(self, settings_file='src/app/resources/settings.json'):
        self.settings_file = settings_file
        self.settings = self._load_settings()

    def _load_settings(self):
        """Loads settings from the JSON file."""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def get(self, key, default=None):
        """Gets a setting value by key."""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Sets a setting value by key."""
        self.settings[key] = value

    def save(self):
        """Saves the current settings to the JSON file."""
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)
