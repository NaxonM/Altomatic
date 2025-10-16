
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Qt, Signal

from .base_view import BaseView
from ..viewmodels.log_viewmodel import LogViewModel


class LogView(BaseView):
    """Activity log dock content."""

    dock_requested = Signal()

    def __init__(self, view_model: LogViewModel):
        super().__init__(view_model)
        self.setObjectName("ActivityLog")
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(6)

        title = QLabel("Activity log")
        title.setProperty("state", "subtitle")
        header.addWidget(title)
        header.addStretch()

        self.copy_button = QPushButton("Copy")
        self.copy_button.setProperty("text-role", "ghost")
        header.addWidget(self.copy_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.setProperty("text-role", "ghost")
        header.addWidget(self.clear_button)

        self.dock_button = QPushButton("Dock")
        self.dock_button.setProperty("text-role", "ghost")
        header.addWidget(self.dock_button)

        layout.addLayout(header)

        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setObjectName("ActivityLogText")
        self.log_text_edit.setProperty("state", "code")
        layout.addWidget(self.log_text_edit, 1)

    def _connect_signals(self):
        """Connects signals and slots."""
        # View to ViewModel
        self.copy_button.clicked.connect(self.view_model.copy_log)
        self.clear_button.clicked.connect(self.view_model.clear_log)
        self.dock_button.clicked.connect(self.dock_requested.emit)

        # ViewModel to View
        self.view_model.log_text_changed.connect(self.log_text_edit.setPlainText)
