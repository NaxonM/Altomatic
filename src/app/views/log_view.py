
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QGroupBox
)
from .base_view import BaseView
from ..viewmodels.log_viewmodel import LogViewModel

class LogView(BaseView):
    """
    The Activity Log view.
    """
    def __init__(self, view_model: LogViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)

        log_box = QGroupBox("Activity Log")
        box_layout = QVBoxLayout(log_box)

        # Action Buttons
        button_layout = QHBoxLayout()
        self.copy_button = QPushButton("Copy")
        button_layout.addWidget(self.copy_button)
        self.clear_button = QPushButton("Clear")
        button_layout.addWidget(self.clear_button)
        box_layout.addLayout(button_layout)

        # Log Display
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        box_layout.addWidget(self.log_text_edit)

        layout.addWidget(log_box)

    def _connect_signals(self):
        """Connects signals and slots."""
        # View to ViewModel
        self.copy_button.clicked.connect(self.view_model.copy_log)
        self.clear_button.clicked.connect(self.view_model.clear_log)

        # ViewModel to View
        self.view_model.log_text_changed.connect(self.log_text_edit.setPlainText)
