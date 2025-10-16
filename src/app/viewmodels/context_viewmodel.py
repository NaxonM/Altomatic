
from PySide6.QtCore import Signal, Property
from .base_viewmodel import BaseViewModel

class ContextViewModel(BaseViewModel):
    """
    ViewModel for the Context sub-tab.
    """
    context_text_changed = Signal(str)
    char_count_text_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._context_text = ""
        self._char_count_text = "0 characters"

    @Property(str, notify=context_text_changed)
    def context_text(self):
        return self._context_text

    @context_text.setter
    def context_text(self, value):
        if self._context_text != value:
            self._context_text = value
            self.context_text_changed.emit(value)
            self.char_count_text = f"{len(value)} characters"

    @Property(str, notify=char_count_text_changed)
    def char_count_text(self):
        return self._char_count_text

    @char_count_text.setter
    def char_count_text(self, value):
        if self._char_count_text != value:
            self._char_count_text = value
            self.char_count_text_changed.emit(value)

    def clear_context(self):
        self.context_text = ""
