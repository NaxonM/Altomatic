
from PySide6.QtCore import Signal, Property
from .base_viewmodel import BaseViewModel

class HeaderViewModel(BaseViewModel):
    """
    ViewModel for the header section.
    """
    summary_model_changed = Signal(str)
    summary_prompt_changed = Signal(str)
    summary_output_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._summary_model = ""
        self._summary_prompt = ""
        self._summary_output = ""

    # --- Properties ---
    @Property(str, notify=summary_model_changed)
    def summary_model(self):
        return self._summary_model

    @summary_model.setter
    def summary_model(self, value):
        if self._summary_model != value:
            self._summary_model = value
            self.summary_model_changed.emit(value)

    @Property(str, notify=summary_prompt_changed)
    def summary_prompt(self):
        return self._summary_prompt

    @summary_prompt.setter
    def summary_prompt(self, value):
        if self._summary_prompt != value:
            self._summary_prompt = value
            self.summary_prompt_changed.emit(value)

    @Property(str, notify=summary_output_changed)
    def summary_output(self):
        return self._summary_output

    @summary_output.setter
    def summary_output(self, value):
        if self._summary_output != value:
            self._summary_output = value
            self.summary_output_changed.emit(value)

    def update_summaries(self, state):
        """
        Updates all summary properties from a central state dictionary.
        This is a temporary solution until a more robust state management
        system is in place.
        """
        if "summary_model" in state:
            self.summary_model = state["summary_model"]
        if "summary_prompt" in state:
            self.summary_prompt = state["summary_prompt"]
        if "summary_output" in state:
            self.summary_output = state["summary_output"]
