
from PySide6.QtCore import Signal, Property, str
from .base_viewmodel import BaseViewModel

class AppearanceViewModel(BaseViewModel):
    """
    ViewModel for the Appearance sub-tab.
    """
    ui_theme_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._ui_theme = "Arctic Light"
        self.themes = [
            "Arctic Light", "Midnight", "Forest", "Sunset", "Lavender",
            "Charcoal", "Ocean Blue", "Deep Space", "Warm Sand",
            "Cherry Blossom", "Emerald Night", "Monochrome", "Nord"
        ]

    @Property(str, notify=ui_theme_changed)
    def ui_theme(self):
        return self._ui_theme

    @ui_theme.setter
    def ui_theme(self, value):
        if self._ui_theme != value:
            self._ui_theme = value
            self.ui_theme_changed.emit(value)
