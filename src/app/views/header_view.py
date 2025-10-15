
from PySide6.QtWidgets import QHBoxLayout, QLabel
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
        layout = QHBoxLayout(self)

        self.summary_model_label = QLabel(self.view_model.summary_model)
        self.summary_prompt_label = QLabel(self.view_model.summary_prompt)
        self.summary_output_label = QLabel(self.view_model.summary_output)

        layout.addWidget(self.summary_model_label)
        layout.addWidget(self.summary_prompt_label)
        layout.addWidget(self.summary_output_label)

    def _connect_signals(self):
        """Connects the view model's signals to the view's slots."""
        self.view_model.summary_model_changed.connect(self.summary_model_label.setText)
        self.view_model.summary_prompt_changed.connect(self.summary_prompt_label.setText)
        self.view_model.summary_output_changed.connect(self.summary_output_label.setText)
