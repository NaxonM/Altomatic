
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QComboBox, QCheckBox, QLineEdit, QPushButton, QFileDialog
)
from .base_view import BaseView
from ..viewmodels.output_viewmodel import OutputViewModel

class OutputView(BaseView):
    """
    The output options sub-tab view.
    """
    def __init__(self, view_model: OutputViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)

        grid = QGridLayout()

        # Output Folder Options
        grid.addWidget(QLabel("Save to:"), 0, 0)
        self.output_folder_combo = QComboBox()
        self.output_folder_combo.addItems(["Same as input", "Pictures", "Desktop", "Custom"])
        grid.addWidget(self.output_folder_combo, 0, 1)

        # Custom Folder
        grid.addWidget(QLabel("Custom folder:"), 1, 0)
        custom_folder_layout = QHBoxLayout()
        self.custom_output_path_edit = QLineEdit()
        custom_folder_layout.addWidget(self.custom_output_path_edit)
        self.browse_button = QPushButton("Browse")
        custom_folder_layout.addWidget(self.browse_button)
        grid.addLayout(custom_folder_layout, 1, 1)

        # Results Table
        self.results_table_checkbox = QCheckBox("Show interactive results table after processing")
        grid.addWidget(self.results_table_checkbox, 2, 0, 1, 2)

        layout.addLayout(grid)
        layout.addStretch()

    def _connect_signals(self):
        """Connects the view model's signals to the view's slots and vice versa."""
        # View to ViewModel
        self.output_folder_combo.currentTextChanged.connect(self.view_model.output_folder_option)
        self.custom_output_path_edit.textChanged.connect(self.view_model.custom_output_path)
        self.browse_button.clicked.connect(self._browse_for_output_folder)
        self.results_table_checkbox.toggled.connect(self.view_model.show_results_table)

        # ViewModel to View
        self.view_model.output_folder_option_changed.connect(self.output_folder_combo.setCurrentText)
        self.view_model.custom_output_path_changed.connect(self.custom_output_path_edit.setText)
        self.view_model.show_results_table_changed.connect(self.results_table_checkbox.setChecked)

        # Enable/disable custom path edit based on combo box selection
        self.output_folder_combo.currentTextChanged.connect(
            lambda text: self.custom_output_path_edit.setEnabled(text == "Custom")
        )
        self.custom_output_path_edit.setEnabled(self.output_folder_combo.currentText() == "Custom")

    def _browse_for_output_folder(self):
        """Opens a folder dialog to select the custom output folder."""
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            self.view_model.custom_output_path = path
