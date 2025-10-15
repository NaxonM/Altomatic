
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
)
from .base_view import BaseView
from ..viewmodels.appearance_viewmodel import AppearanceViewModel

class AppearanceView(BaseView):
    """
    The Appearance sub-tab view.
    """
    def __init__(self, view_model: AppearanceViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("UI Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.view_model.themes)
        theme_layout.addWidget(self.theme_combo)

        layout.addLayout(theme_layout)
        layout.addStretch()

    def _connect_signals(self):
        """Connects signals and slots."""
        # View to ViewModel
        self.theme_combo.currentTextChanged.connect(self.view_model.ui_theme)

        # ViewModel to View
        self.view_model.ui_theme_changed.connect(self.theme_combo.setCurrentText)
