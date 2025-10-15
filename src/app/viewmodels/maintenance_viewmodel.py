
from PySide6.QtCore import Signal
from .base_viewmodel import BaseViewModel
from src.core.config.manager import open_config_folder, save_config, reset_config

class MaintenanceViewModel(BaseViewModel):
    """
    ViewModel for the Maintenance sub-tab.
    """
    save_settings_clicked = Signal()
    open_config_folder_clicked = Signal()
    reset_defaults_clicked = Signal()
    reset_token_usage_clicked = Signal()
    reset_analyzed_stats_clicked = Signal()

    def __init__(self):
        super().__init__()

    def save_settings(self, state, geometry):
        try:
            save_config(state, geometry)
            self.save_settings_clicked.emit()
        except Exception as e:
            self.errorOccurred.emit(f"Error saving settings: {e}")

    def open_config_folder(self):
        try:
            open_config_folder()
            self.open_config_folder_clicked.emit()
        except Exception as e:
            self.errorOccurred.emit(f"Error opening config folder: {e}")

    def reset_defaults(self):
        try:
            reset_config()
            self.reset_defaults_clicked.emit()
        except Exception as e:
            self.errorOccurred.emit(f"Error resetting defaults: {e}")

    def reset_token_usage(self):
        self.reset_token_usage_clicked.emit()

    def reset_analyzed_stats(self):
        self.reset_analyzed_stats_clicked.emit()
