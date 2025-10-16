
from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from .base_viewmodel import BaseViewModel
from src.core.config.manager import open_config_folder, reset_config

if TYPE_CHECKING:
    from .main_viewmodel import MainViewModel

class MaintenanceViewModel(BaseViewModel):
    """
    ViewModel for the Maintenance sub-tab.
    """
    save_settings_clicked = Signal()
    open_config_folder_clicked = Signal()
    reset_defaults_clicked = Signal()
    reset_token_usage_clicked = Signal()
    reset_analyzed_stats_clicked = Signal()

    def __init__(self, main_vm: "MainViewModel"):
        super().__init__()
        self._main_vm = main_vm

    def save_settings(self, geometry: str):
        try:
            self._main_vm.save_settings(geometry)
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
            self._main_vm.load_config()
            self.reset_defaults_clicked.emit()
        except Exception as e:
            self.errorOccurred.emit(f"Error resetting defaults: {e}")

    def reset_token_usage(self):
        self.reset_token_usage_clicked.emit()

    def reset_analyzed_stats(self):
        self.reset_analyzed_stats_clicked.emit()
