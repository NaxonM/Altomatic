
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QComboBox, QFileDialog
)
from .base_view import BaseView
from ..viewmodels.input_viewmodel import InputViewModel

class InputView(BaseView):
    """
    The input view, containing widgets for selecting the input type, path, and options.
    """
    def __init__(self, view_model: InputViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        main_layout = QVBoxLayout(self)

        # Input Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Input type:"))
        self.input_type_combo = QComboBox()
        self.input_type_combo.addItems(["Folder", "File"])
        type_layout.addWidget(self.input_type_combo)

        # Input Path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Input path:"))
        self.input_path_edit = QLineEdit()
        path_layout.addWidget(self.input_path_edit)
        self.browse_button = QPushButton("Browse")
        path_layout.addWidget(self.browse_button)

        # Options
        self.subdirectories_checkbox = QCheckBox("Include subdirectories")
        self.image_count_label = QLabel()

        main_layout.addLayout(type_layout)
        main_layout.addLayout(path_layout)
        main_layout.addWidget(self.subdirectories_checkbox)
        main_layout.addWidget(self.image_count_label)

    def _connect_signals(self):
        """Connects the view model's signals to the view's slots and vice versa."""
        # View to ViewModel
        self.input_type_combo.currentTextChanged.connect(self.view_model.input_type)
        self.input_path_edit.textChanged.connect(self.view_model.input_path)
        self.subdirectories_checkbox.toggled.connect(self.view_model.include_subdirectories)
        self.browse_button.clicked.connect(self._browse_for_input)

        # ViewModel to View
        self.view_model.input_type_changed.connect(self.input_type_combo.setCurrentText)
        self.view_model.input_path_changed.connect(self.input_path_edit.setText)
        self.view_model.include_subdirectories_changed.connect(self.subdirectories_checkbox.setChecked)
        self.view_model.image_count_text_changed.connect(self.image_count_label.setText)

    def _browse_for_input(self):
        """Opens a file or folder dialog based on the selected input type."""
        if self.view_model.input_type == "Folder":
            path = QFileDialog.getExistingDirectory(self, "Select Folder")
        else: # File
            path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Image Files (*.png *.jpg *.jpeg *.webp *.heic *.heif)")

        if path:
            self.view_model.input_path = path
