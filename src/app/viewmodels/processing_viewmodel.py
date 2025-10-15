
from PySide6.QtCore import Signal, Property, str, bool
from .base_viewmodel import BaseViewModel

class ProcessingViewModel(BaseViewModel):
    """
    ViewModel for the Processing Options sub-tab.
    """
    filename_language_changed = Signal(str)
    alttext_language_changed = Signal(str)
    name_detail_level_changed = Signal(str)
    vision_detail_changed = Signal(str)
    ocr_enabled_changed = Signal(bool)
    tesseract_path_changed = Signal(str)
    ocr_language_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._filename_language = "English"
        self._alttext_language = "English"
        self._name_detail_level = "Detailed"
        self._vision_detail = "auto"
        self._ocr_enabled = False
        self._tesseract_path = ""
        self._ocr_language = "eng"

    # --- Properties ---
    @Property(str, notify=filename_language_changed)
    def filename_language(self):
        return self._filename_language

    @filename_language.setter
    def filename_language(self, value):
        if self._filename_language != value:
            self._filename_language = value
            self.filename_language_changed.emit(value)

    @Property(str, notify=alttext_language_changed)
    def alttext_language(self):
        return self._alttext_language

    @alttext_language.setter
    def alttext_language(self, value):
        if self._alttext_language != value:
            self._alttext_language = value
            self.alttext_language_changed.emit(value)

    @Property(str, notify=name_detail_level_changed)
    def name_detail_level(self):
        return self._name_detail_level

    @name_detail_level.setter
    def name_detail_level(self, value):
        if self._name_detail_level != value:
            self._name_detail_level = value
            self.name_detail_level_changed.emit(value)

    @Property(str, notify=vision_detail_changed)
    def vision_detail(self):
        return self._vision_detail

    @vision_detail.setter
    def vision_detail(self, value):
        if self._vision_detail != value:
            self._vision_detail = value
            self.vision_detail_changed.emit(value)

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
