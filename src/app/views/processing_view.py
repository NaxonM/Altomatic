
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QComboBox, QCheckBox, QLineEdit, QPushButton, QFileDialog
)
from .base_view import BaseView
from ..viewmodels.processing_viewmodel import ProcessingViewModel

class ProcessingView(BaseView):
    """
    The processing options sub-tab view.
    """
    def __init__(self, view_model: ProcessingViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)

        grid = QGridLayout()

        # Language Options
        grid.addWidget(QLabel("Filename language:"), 0, 0)
        self.filename_language_combo = QComboBox()
        self.filename_language_combo.addItems(["English", "Persian"])
        grid.addWidget(self.filename_language_combo, 0, 1)

        grid.addWidget(QLabel("Alt-text language:"), 0, 2)
        self.alttext_language_combo = QComboBox()
        self.alttext_language_combo.addItems(["English", "Persian"])
        grid.addWidget(self.alttext_language_combo, 0, 3)

        # Detail Levels
        grid.addWidget(QLabel("Name detail level:"), 1, 0)
        self.name_detail_combo = QComboBox()
        self.name_detail_combo.addItems(["Detailed", "Normal", "Minimal"])
        grid.addWidget(self.name_detail_combo, 1, 1)

        grid.addWidget(QLabel("Vision detail:"), 1, 2)
        self.vision_detail_combo = QComboBox()
        self.vision_detail_combo.addItems(["auto", "high", "low"])
        grid.addWidget(self.vision_detail_combo, 1, 3)

        # OCR Options
        self.ocr_checkbox = QCheckBox("Enable OCR before compression")
        grid.addWidget(self.ocr_checkbox, 2, 0, 1, 4) # Span across all columns

        grid.addWidget(QLabel("Tesseract path:"), 3, 0)
        tesseract_layout = QHBoxLayout()
        self.tesseract_path_edit = QLineEdit()
        tesseract_layout.addWidget(self.tesseract_path_edit)
        self.tesseract_browse_button = QPushButton("Browse")
        tesseract_layout.addWidget(self.tesseract_browse_button)
        grid.addLayout(tesseract_layout, 3, 1, 1, 3)

        grid.addWidget(QLabel("OCR language:"), 4, 0)
        self.ocr_language_edit = QLineEdit()
        grid.addWidget(self.ocr_language_edit, 4, 1)

        layout.addLayout(grid)
        layout.addStretch() # Push everything to the top

    def _connect_signals(self):
        """Connects the view model's signals to the view's slots and vice versa."""
        # View to ViewModel
        self.filename_language_combo.currentTextChanged.connect(self.view_model.filename_language)
        self.alttext_language_combo.currentTextChanged.connect(self.view_model.alttext_language)
        self.name_detail_combo.currentTextChanged.connect(self.view_model.name_detail_level)
        self.vision_detail_combo.currentTextChanged.connect(self.view_model.vision_detail)
        self.ocr_checkbox.toggled.connect(self.view_model.ocr_enabled)
        self.tesseract_path_edit.textChanged.connect(self.view_model.tesseract_path)
        self.tesseract_browse_button.clicked.connect(self._browse_for_tesseract)
        self.ocr_language_edit.textChanged.connect(self.view_model.ocr_language)

        # ViewModel to View
        self.view_model.filename_language_changed.connect(self.filename_language_combo.setCurrentText)
        self.view_model.alttext_language_changed.connect(self.alttext_language_combo.setCurrentText)
        self.view_model.name_detail_level_changed.connect(self.name_detail_combo.setCurrentText)
        self.view_model.vision_detail_changed.connect(self.vision_detail_combo.setCurrentText)
        self.view_model.ocr_enabled_changed.connect(self.ocr_checkbox.setChecked)
        self.view_model.tesseract_path_changed.connect(self.tesseract_path_edit.setText)
        self.view_model.ocr_language_changed.connect(self.ocr_language_edit.setText)

    def _browse_for_tesseract(self):
        """Opens a file dialog to select the Tesseract executable."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Tesseract Executable", "", "All Files (*)")
        if path:
            self.view_model.tesseract_path = path
