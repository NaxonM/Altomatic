
from PySide6.QtCore import Signal, Property, str
from .base_viewmodel import BaseViewModel
from src.altomatic.models import AVAILABLE_PROVIDERS, get_provider_label, get_default_model, get_models_for_provider
import pyperclip

class ProviderViewModel(BaseViewModel):
    """
    ViewModel for the LLM Provider sub-tab.
    """
    llm_provider_changed = Signal(str)
    openai_api_key_changed = Signal(str)
    openrouter_api_key_changed = Signal(str)
    model_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._llm_provider = "openai"
        self._openai_api_key = ""
        self._openrouter_api_key = ""
        self._model = get_default_model("openai")
        self.provider_labels = {get_provider_label(pid): pid for pid in AVAILABLE_PROVIDERS}

    # --- Properties ---
    @Property(str, notify=llm_provider_changed)
    def llm_provider(self):
        return self._llm_provider

    @llm_provider.setter
    def llm_provider(self, value):
        if self._llm_provider != value:
            self._llm_provider = value
            self.llm_provider_changed.emit(value)
            self.model = get_default_model(value) # Reset model on provider change

    @Property(str, notify=openai_api_key_changed)
    def openai_api_key(self):
        return self._openai_api_key

    @openai_api_key.setter
    def openai_api_key(self, value):
        if self._openai_api_key != value:
            self._openai_api_key = value
            self.openai_api_key_changed.emit(value)

    @Property(str, notify=openrouter_api_key_changed)
    def openrouter_api_key(self):
        return self._openrouter_api_key

    @openrouter_api_key.setter
    def openrouter_api_key(self, value):
        if self._openrouter_api_key != value:
            self._openrouter_api_key = value
            self.openrouter_api_key_changed.emit(value)

    @Property(str, notify=model_changed)
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        if self._model != value:
            self._model = value
            self.model_changed.emit(value)

    # --- Actions ---
    def paste_openai_key(self):
        try:
            self.openai_api_key = pyperclip.paste()
        except Exception as e:
            self.errorOccurred.emit(f"Could not paste from clipboard: {e}")

    def paste_openrouter_key(self):
        try:
            self.openrouter_api_key = pyperclip.paste()
        except Exception as e:
            self.errorOccurred.emit(f"Could not paste from clipboard: {e}")

    def get_models_for_current_provider(self):
        return get_models_for_provider(self.llm_provider)
