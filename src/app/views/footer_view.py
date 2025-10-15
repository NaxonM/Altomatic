
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton
from .base_view import BaseView
from ..viewmodels.footer_viewmodel import FooterViewModel

class FooterView(BaseView):
    """
    The footer view, containing the status bar, progress bar, and process button.
    """
    def __init__(self, view_model: FooterViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QHBoxLayout(self)

        self.status_label = QLabel(self.view_model.status_text)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(self.view_model.progress_value)
        self.process_button = QPushButton("Describe Images")
        self.token_label = QLabel(f"Tokens: {self.view_model.total_tokens}")

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.process_button)
        layout.addWidget(self.token_label)

    def _connect_signals(self):
        """Connects the view model's signals to the view's slots."""
        self.view_model.status_text_changed.connect(self.status_label.setText)
        self.view_model.progress_value_changed.connect(self.progress_bar.setValue)
        self.view_model.total_tokens_changed.connect(lambda tokens: self.token_label.setText(f"Tokens: {tokens}"))
        self.process_button.clicked.connect(self.view_model.process_images)
