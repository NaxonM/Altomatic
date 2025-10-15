
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QAbstractItemView,
    QPushButton, QHBoxLayout
)
from .base_view import BaseView
from ..viewmodels.results_viewmodel import ResultsViewModel

class ResultsView(BaseView):
    """
    The Results window view.
    """
    def __init__(self, view_model: ResultsViewModel):
        super().__init__(view_model)
        self.setWindowTitle("Processing Results")
        self.setGeometry(150, 150, 800, 600)
        self._setup_ui()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)

        # Results Table
        self.table_view = QTableView()
        self.table_view.setModel(self.view_model.table_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setWordWrap(True)
        self.table_view.resizeColumnsToContents()
        self.table_view.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_view)

        # Action Buttons
        button_layout = QHBoxLayout()
        self.copy_alt_text_button = QPushButton("Copy Alt Text")
        button_layout.addWidget(self.copy_alt_text_button)
        self.close_button = QPushButton("Close")
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        # Connect signals
        self.close_button.clicked.connect(self.close)
        # self.copy_alt_text_button.clicked.connect(...) # Will implement later
