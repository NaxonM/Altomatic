
from PySide6.QtCore import Signal, Property
from .base_viewmodel import BaseViewModel
import pyperclip

class LogViewModel(BaseViewModel):
    """
    ViewModel for the Activity Log.
    """
    log_text_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._logs = []
        self._log_text = ""

    @Property(str, notify=log_text_changed)
    def log_text(self):
        return self._log_text

    def _update_log_text(self):
        """Updates the formatted log text from the list of logs."""
        # Using simple text for now, will add color later
        new_text = "\\n".join(self._logs)
        if self._log_text != new_text:
            self._log_text = new_text
            self.log_text_changed.emit(self._log_text)

    def add_log(self, message: str, level: str = "info"):
        """Adds a new message to the log."""
        formatted_message = f"[{level.upper()}] {message}"
        self._logs.append(formatted_message)
        self._update_log_text()

    def clear_log(self):
        """Clears all log messages."""
        self._logs.clear()
        self._update_log_text()

    def copy_log(self):
        """Copies the log content to the clipboard."""
        try:
            pyperclip.copy(self.log_text)
        except Exception as e:
            self.errorOccurred.emit(f"Could not copy to clipboard: {e}")
