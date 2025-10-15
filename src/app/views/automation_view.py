
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QCheckBox, QLineEdit, QPushButton, QFileDialog
)
from .base_view import BaseView
from ..viewmodels.automation_viewmodel import AutomationViewModel

class AutomationView(BaseView):
    """
    The Automation sub-tab view.
    """
    def __init__(self, view_model: AutomationViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)

        grid = QGridLayout()

        # OCR Options
        self.ocr_checkbox = QCheckBox("Enable OCR")
        grid.addWidget(self.ocr_checkbox, 0, 0, 1, 2)

        grid.addWidget(QLabel("Tesseract path:"), 1, 0)
        tesseract_layout = QHBoxLayout()
        self.tesseract_path_edit = QLineEdit()
        tesseract_layout.addWidget(self.tesseract_path_edit)
        self.tesseract_browse_button = QPushButton("Browse")
        tesseract_layout.addWidget(self.tesseract_browse_button)
        grid.addLayout(tesseract_layout, 1, 1)

        grid.addWidget(QLabel("OCR language:"), 2, 0)
        self.ocr_language_edit = QLineEdit()
        grid.addWidget(self.ocr_language_edit, 2, 1)

        layout.addLayout(grid)
        layout.addStretch()

    def _connect_signals(self):
        """Connects signals and slots."""
        # View to ViewModel
        self.ocr_checkbox.toggled.connect(self.view_model.ocr_enabled)
        self.tesseract_path_edit.textChanged.connect(self.view_model.tesseract_path)
        self.tesseract_browse_button.clicked.connect(self._browse_for_tesseract)
        self.ocr_language_edit.textChanged.connect(self.view_model.ocr_language)

        # ViewModel to View
        self.view_model.ocr_enabled_changed.connect(self.ocr_checkbox.setChecked)
        self.view_model.tesseract_path_changed.connect(self.tesseract_path_edit.setText)
        self.view_model.ocr_language_changed.connect(self.ocr_language_edit.setText)

    def _browse_for_tesseract(self):
        """Opens a file dialog to select the Tesseract executable."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Tesseract Executable", "", "All Files (*)")
        if path:
            self.view_model.tesseract_path = path
