
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton
)
from .base_view import BaseView
from ..viewmodels.context_viewmodel import ContextViewModel

class ContextView(BaseView):
    """
    The context sub-tab view.
    """
    def __init__(self, view_model: ContextViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)

        label = QLabel("Context notes:")
        label.setProperty("state", "subtitle")
        layout.addWidget(label)

        self.context_text_edit = QTextEdit()
        layout.addWidget(self.context_text_edit)

        bottom_layout = QHBoxLayout()
        self.char_count_label = QLabel()
        bottom_layout.addWidget(self.char_count_label)

        self.clear_button = QPushButton("Clear")
        bottom_layout.addWidget(self.clear_button)

        layout.addLayout(bottom_layout)

    def _connect_signals(self):
        """Connects the view model's signals to the view's slots and vice versa."""
        # View to ViewModel
        self.context_text_edit.textChanged.connect(self._on_text_changed)
        self.clear_button.clicked.connect(self.view_model.clear_context)

        # ViewModel to View
        self.view_model.context_text_changed.connect(self.context_text_edit.setPlainText)
        self.view_model.char_count_text_changed.connect(self.char_count_label.setText)

    def _on_text_changed(self):
        self.view_model.context_text = self.context_text_edit.toPlainText()
