
from PySide6.QtCore import Signal, Property, int, str
from .base_viewmodel import BaseViewModel

class FooterViewModel(BaseViewModel):
    """
    ViewModel for the main application footer.
    """
    # Signals to notify the view of property changes
    status_text_changed = Signal(str)
    progress_value_changed = Signal(int)
    total_tokens_changed = Signal(int)
    process_button_clicked = Signal()

    def __init__(self):
        super().__init__()
        self._status_text = "Ready."
        self._progress_value = 0
        self._total_tokens = 0

    # --- Properties ---
    @Property(str, notify=status_text_changed)
    def status_text(self):
        return self._status_text

    @status_text.setter
    def status_text(self, value):
        if self._status_text != value:
            self._status_text = value
            self.status_text_changed.emit(value)

    @Property(int, notify=progress_value_changed)
    def progress_value(self):
        return self._progress_value

    @progress_value.setter
    def progress_value(self, value):
        if self._progress_value != value:
            self._progress_value = value
            self.progress_value_changed.emit(value)

    @Property(int, notify=total_tokens_changed)
    def total_tokens(self):
        return self._total_tokens

    @total_tokens.setter
    def total_tokens(self, value):
        if self._total_tokens != value:
            self._total_tokens = value
            self.total_tokens_changed.emit(value)

    # --- Actions ---
    def process_images(self):
        """Emits a signal to start the image processing task."""
        self.process_button_clicked.emit()
