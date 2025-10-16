
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
)
from .base_view import BaseView
from ..viewmodels.maintenance_viewmodel import MaintenanceViewModel

class MaintenanceView(BaseView):
    """
    The Maintenance sub-tab view.
    """
    def __init__(self, view_model: MaintenanceViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)

        primary_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Settings")
        primary_layout.addWidget(self.save_button)
        self.open_config_button = QPushButton("Open Config Folder")
        primary_layout.addWidget(self.open_config_button)
        layout.addLayout(primary_layout)

        secondary_layout = QHBoxLayout()
        self.reset_defaults_button = QPushButton("Reset Defaults")
        secondary_layout.addWidget(self.reset_defaults_button)
        self.reset_token_button = QPushButton("Reset Token Usage")
        secondary_layout.addWidget(self.reset_token_button)
        self.reset_stats_button = QPushButton("Reset Analyzed Stats")
        secondary_layout.addWidget(self.reset_stats_button)
        layout.addLayout(secondary_layout)

        layout.addStretch()

    def _connect_signals(self):
        """Connects signals and slots."""
        # Note: Some of these actions require access to the main application state
        # and geometry, which is not directly available to this view.
        # This will require a more robust state management solution in the future.
        self.save_button.clicked.connect(self._save_settings)
        self.open_config_button.clicked.connect(self.view_model.open_config_folder)
        self.reset_defaults_button.clicked.connect(self._confirm_reset_defaults)

        self.view_model.save_settings_clicked.connect(self._show_save_confirmation)
        self.view_model.reset_defaults_clicked.connect(self._show_reset_confirmation)

    def _confirm_reset_defaults(self):
        reply = QMessageBox.question(self, 'Reset Settings',
                                     "Are you sure you want to reset all settings?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.view_model.reset_defaults()

    def _show_save_confirmation(self):
        QMessageBox.information(self, "Saved", "✅ Settings saved successfully.")

    def _show_reset_confirmation(self):
        QMessageBox.information(self, "Reset", "Settings reset. Please restart the application.")

    def _save_settings(self):
        window = self.window()
        if window is None:
            return
        geometry = f"{window.width()}x{window.height()}"
        self.view_model.save_settings(geometry)
