
from PySide6.QtCore import Signal, Property
from .base_viewmodel import BaseViewModel
from ..theming import THEMES, DEFAULT_THEME

class AppearanceViewModel(BaseViewModel):
    """
    ViewModel for the Appearance sub-tab.
    """
    ui_theme_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._ui_theme = DEFAULT_THEME
        self.themes = list(THEMES.keys())

    @Property(str, notify=ui_theme_changed)
    def ui_theme(self):
        return self._ui_theme

    @ui_theme.setter
    def ui_theme(self, value):
        if value not in THEMES:
            value = DEFAULT_THEME
        if self._ui_theme != value:
            self._ui_theme = value
            self.ui_theme_changed.emit(value)
