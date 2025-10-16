
from PySide6.QtCore import Signal, Property
from .base_viewmodel import BaseViewModel

class AutomationViewModel(BaseViewModel):
    """
    ViewModel for the Automation sub-tab.
    """
    ocr_enabled_changed = Signal(bool)
    tesseract_path_changed = Signal(str)
    ocr_language_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._ocr_enabled = False
        self._tesseract_path = ""
        self._ocr_language = "eng"

    @Property(bool, notify=ocr_enabled_changed)
    def ocr_enabled(self):
        return self._ocr_enabled

    @ocr_enabled.setter
    def ocr_enabled(self, value):
        if self._ocr_enabled != value:
            self._ocr_enabled = value
            self.ocr_enabled_changed.emit(value)

    @Property(str, notify=tesseract_path_changed)
    def tesseract_path(self):
        return self._tesseract_path

    @tesseract_path.setter
    def tesseract_path(self, value):
        if self._tesseract_path != value:
            self._tesseract_path = value
            self.tesseract_path_changed.emit(value)

    @Property(str, notify=ocr_language_changed)
    def ocr_language(self):
        return self._ocr_language

    @ocr_language.setter
    def ocr_language(self, value):
        if self._ocr_language != value:
            self._ocr_language = value
            self.ocr_language_changed.emit(value)
