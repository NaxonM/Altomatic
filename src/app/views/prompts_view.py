
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QTextEdit, QPushButton
)
from .base_view import BaseView
from ..viewmodels.prompts_viewmodel import PromptsViewModel

class PromptsView(BaseView):
    """
    The Prompts sub-tab view.
    """
    def __init__(self, view_model: PromptsViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)

        # Prompt Selection
        prompt_layout = QHBoxLayout()
        prompt_layout.addWidget(QLabel("Prompt preset:"))
        self.prompt_combo = QComboBox()
        self.prompt_labels = self.view_model.get_prompt_labels()
        for key, label in self.prompt_labels.items():
            self.prompt_combo.addItem(label, key)
        prompt_layout.addWidget(self.prompt_combo)
        self.edit_prompts_button = QPushButton("Edit Prompts...")
        prompt_layout.addWidget(self.edit_prompts_button)
        layout.addLayout(prompt_layout)

        # Prompt Preview
        self.prompt_preview = QTextEdit()
        self.prompt_preview.setReadOnly(True)
        layout.addWidget(self.prompt_preview)

    def _connect_signals(self):
        """Connects signals and slots."""
        # View to ViewModel
        self.prompt_combo.currentIndexChanged.connect(self._on_prompt_selected)
        # self.edit_prompts_button.clicked.connect(...) # Will be implemented later

        # ViewModel to View
        self.view_model.selected_prompt_changed.connect(self._update_prompt_selection)
        self.view_model.prompt_preview_text_changed.connect(self.prompt_preview.setPlainText)

    def _on_prompt_selected(self, index):
        """Handles the selection of a new prompt."""
        key = self.prompt_combo.itemData(index)
        self.view_model.selected_prompt = key

    def _update_prompt_selection(self, key):
        """Selects the correct prompt in the combobox."""
        for i in range(self.prompt_combo.count()):
            if self.prompt_combo.itemData(i) == key:
                self.prompt_combo.setCurrentIndex(i)
                break
