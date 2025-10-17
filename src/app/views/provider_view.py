
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QCheckBox, QFrame
)
from .base_view import BaseView
from ..viewmodels.provider_viewmodel import ProviderViewModel

class ProviderView(BaseView):
    """
    The LLM Provider sub-tab view.
    """
    def __init__(self, view_model: ProviderViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()
        self._update_provider_section()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)

        # Provider Selection
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(self.view_model.provider_labels.keys())
        provider_layout.addWidget(self.provider_combo)
        layout.addLayout(provider_layout)

        # API Key Sections
        self._create_api_sections(layout)

        # Model Selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        model_layout.addWidget(self.model_combo)
        self.refresh_models_button = QPushButton("Refresh free models")
        model_layout.addWidget(self.refresh_models_button)
        layout.addLayout(model_layout)

        layout.addStretch()

    def _create_api_sections(self, parent_layout):
        """Creates the API key sections for OpenAI and OpenRouter."""
        api_layout = QHBoxLayout()

        # OpenAI
        self.openai_frame = QFrame()
        openai_layout = QVBoxLayout(self.openai_frame)
        openai_layout.addWidget(QLabel("OpenAI API Key"))
        openai_key_layout = QHBoxLayout()
        self.openai_key_edit = QLineEdit()
        self.openai_key_edit.setEchoMode(QLineEdit.Password)
        openai_key_layout.addWidget(self.openai_key_edit)
        self.show_openai_key_check = QCheckBox("Show")
        openai_key_layout.addWidget(self.show_openai_key_check)
        openai_layout.addLayout(openai_key_layout)
        self.paste_openai_button = QPushButton("Paste")
        openai_layout.addWidget(self.paste_openai_button)
        api_layout.addWidget(self.openai_frame)

        # OpenRouter
        self.openrouter_frame = QFrame()
        openrouter_layout = QVBoxLayout(self.openrouter_frame)
        openrouter_layout.addWidget(QLabel("OpenRouter API Key"))
        openrouter_key_layout = QHBoxLayout()
        self.openrouter_key_edit = QLineEdit()
        self.openrouter_key_edit.setEchoMode(QLineEdit.Password)
        openrouter_key_layout.addWidget(self.openrouter_key_edit)
        self.show_openrouter_key_check = QCheckBox("Show")
        openrouter_key_layout.addWidget(self.show_openrouter_key_check)
        openrouter_layout.addLayout(openrouter_key_layout)
        self.paste_openrouter_button = QPushButton("Paste")
        openrouter_layout.addWidget(self.paste_openrouter_button)
        api_layout.addWidget(self.openrouter_frame)

        parent_layout.addLayout(api_layout)

    def _connect_signals(self):
        """Connects signals and slots."""
        # View to ViewModel
        self.provider_combo.currentTextChanged.connect(
            lambda text: setattr(self.view_model, "llm_provider", self.view_model.provider_labels[text])
        )
        self.openai_key_edit.textChanged.connect(
            lambda value: setattr(self.view_model, "openai_api_key", value)
        )
        self.openrouter_key_edit.textChanged.connect(
            lambda value: setattr(self.view_model, "openrouter_api_key", value)
        )
        self.model_combo.currentTextChanged.connect(
            lambda value: setattr(self.view_model, "model", self.model_combo.currentData())
        )

        self.show_openai_key_check.toggled.connect(
            lambda checked: self.openai_key_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        )
        self.show_openrouter_key_check.toggled.connect(
            lambda checked: self.openrouter_key_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        )
        self.paste_openai_button.clicked.connect(self.view_model.paste_openai_key)
        self.paste_openrouter_button.clicked.connect(self.view_model.paste_openrouter_key)
        # self.refresh_models_button.clicked.connect(...) # Will be implemented later

        # ViewModel to View
        self.view_model.llm_provider_changed.connect(self._update_provider_section)
        self.view_model.openai_api_key_changed.connect(self.openai_key_edit.setText)
        self.view_model.openrouter_api_key_changed.connect(self.openrouter_key_edit.setText)
        self.view_model.model_changed.connect(self._update_model_selection)

    def _update_provider_section(self):
        """Shows/hides UI elements based on the selected provider."""
        provider = self.view_model.llm_provider
        self.openai_frame.setVisible(provider == "openai")
        self.openrouter_frame.setVisible(provider == "openrouter")
        self.refresh_models_button.setVisible(provider == "openrouter")
        self._update_model_list()
        self.openai_key_edit.setText(self.view_model.openai_api_key)
        self.openrouter_key_edit.setText(self.view_model.openrouter_api_key)

    def _update_model_list(self):
        """Updates the model combobox with models for the current provider."""
        self.model_combo.clear()
        models = self.view_model.get_models_for_current_provider()
        for model_id, info in models.items():
            self.model_combo.addItem(info.get("label", model_id), model_id)

    def _update_model_selection(self, model_id):
        """Selects the correct model in the combobox."""
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == model_id:
                self.model_combo.setCurrentIndex(i)
                break

