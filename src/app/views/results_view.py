
import csv
import json
from pathlib import Path

from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
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

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter filenames or alt text…")
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.view_model.table_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)

        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setWordWrap(True)
        self.table_view.resizeColumnsToContents()
        self.table_view.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_view)

        # Action Buttons
        button_layout = QHBoxLayout()
        self.copy_alt_text_button = QPushButton("Copy Alt Text")
        button_layout.addWidget(self.copy_alt_text_button)
        self.export_csv_button = QPushButton("Export CSV")
        button_layout.addWidget(self.export_csv_button)
        self.export_json_button = QPushButton("Export JSON")
        button_layout.addWidget(self.export_json_button)
        self.close_button = QPushButton("Close")
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        # Connect signals
        self.close_button.clicked.connect(self.close)
        self.copy_alt_text_button.clicked.connect(self._copy_alt_text)
        self.export_csv_button.clicked.connect(lambda: self._export_results("csv"))
        self.export_json_button.clicked.connect(lambda: self._export_results("json"))
        self.search_edit.textChanged.connect(self.proxy_model.setFilterFixedString)

    def _selected_row(self) -> int | None:
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            return None
        proxy_index = indexes[0]
        return self.proxy_model.mapToSource(proxy_index).row()

    def _copy_alt_text(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Copy Alt Text", "Select a row to copy its alt text.")
            return
        alt_text = self.view_model.results[row]["alt_text"]
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(alt_text)
        QMessageBox.information(self, "Copy Alt Text", "Alt text copied to clipboard.")

    def _export_results(self, fmt: str) -> None:
        filters = "CSV Files (*.csv)" if fmt == "csv" else "JSON Files (*.json)"
        path, _ = QFileDialog.getSaveFileName(self, "Export Results", "", filters)
        if not path:
            return
        try:
            export_path = Path(path)
            data = self.view_model.results
            if fmt == "csv":
                with export_path.open("w", encoding="utf-8", newline="") as fh:
                    writer = csv.DictWriter(fh, fieldnames=["original_filename", "new_filename", "alt_text"])
                    writer.writeheader()
                    writer.writerows(data)
            else:
                with export_path.open("w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Export Results", f"Results exported to {export_path}.")
        except Exception as exc:
            QMessageBox.critical(self, "Export Results", f"Failed to export results: {exc}")
