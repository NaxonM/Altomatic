
from PySide6.QtWidgets import QVBoxLayout, QLabel
from .base_view import BaseView
from ..viewmodels.header_viewmodel import HeaderViewModel

class HeaderView(BaseView):
    """
    The header view, displaying summary information.
    """
    def __init__(self, view_model: HeaderViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.summary_model_label = QLabel()
        self.summary_model_label.setProperty("state", "muted")
        self.summary_model_label.setWordWrap(True)

        self.summary_prompt_label = QLabel()
        self.summary_prompt_label.setProperty("state", "muted")
        self.summary_prompt_label.setWordWrap(True)

        self.summary_output_label = QLabel()
        self.summary_output_label.setProperty("state", "muted")
        self.summary_output_label.setWordWrap(True)

        layout.addWidget(self.summary_model_label)
        layout.addWidget(self.summary_prompt_label)
        layout.addWidget(self.summary_output_label)
        layout.addStretch()

        self._refresh_labels()

    def _connect_signals(self):
        """Connects the view model's signals to the view's slots."""
        self.view_model.summary_model_changed.connect(self._refresh_labels)
        self.view_model.summary_prompt_changed.connect(self._refresh_labels)
        self.view_model.summary_output_changed.connect(self._refresh_labels)

    def _refresh_labels(self) -> None:
        self.summary_model_label.setText(f"Provider · {self.view_model.summary_model}")
        self.summary_prompt_label.setText(f"Prompt · {self.view_model.summary_prompt}")
        self.summary_output_label.setText(f"Output · {self.view_model.summary_output}")
