from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List, Dict, Any

from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .base_view import BaseView
from ..viewmodels.results_viewmodel import ResultsViewModel


class ReviewView(BaseView):
    """Embedded review page displaying recent results."""

    def __init__(self):
        super().__init__(ResultsViewModel([]))
        self._table_enabled = True
        self._setup_ui()
        self._bind_signals()
        self._refresh_visibility()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.title_label = QLabel("Review")
        self.title_label.setProperty("state", "title")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("Inspect processed results, copy alt text, or export to share with your team.")
        self.subtitle_label.setProperty("state", "subtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        self.placeholder_label = QLabel("Run the workflow to generate results.")
        self.placeholder_label.setProperty("state", "muted")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setWordWrap(True)
        layout.addWidget(self.placeholder_label, 1)

        # Search + table container
        self.search_container = QWidget()
        self.search_layout = QHBoxLayout(self.search_container)
        self.search_layout.setContentsMargins(0, 0, 0, 0)
        self.search_layout.setSpacing(6)
        search_label = QLabel("Search")
        search_label.setProperty("state", "muted")
        self.search_layout.addWidget(search_label)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter filenames or alt text…")
        self.search_layout.addWidget(self.search_edit, 1)
        layout.addWidget(self.search_container)

        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.view_model.table_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)

        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().hide()
        layout.addWidget(self.table_view, 1)

        # Actions row
        self.actions_container = QWidget()
        self.actions_layout = QHBoxLayout(self.actions_container)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(8)
        self.copy_button = QPushButton("Copy Alt Text")
        self.export_csv_button = QPushButton("Export CSV")
        self.export_json_button = QPushButton("Export JSON")
        self.actions_layout.addWidget(self.copy_button)
        self.actions_layout.addWidget(self.export_csv_button)
        self.actions_layout.addWidget(self.export_json_button)
        self.actions_layout.addStretch()
        layout.addWidget(self.actions_container)

    def _bind_signals(self) -> None:
        self.search_edit.textChanged.connect(self.proxy_model.setFilterFixedString)
        self.copy_button.clicked.connect(self._copy_selected_alt_text)
        self.export_csv_button.clicked.connect(lambda: self._export_results("csv"))
        self.export_json_button.clicked.connect(lambda: self._export_results("json"))

    def set_results(self, results: List[Dict[str, Any]], table_enabled: bool) -> None:
        self._table_enabled = table_enabled
        self.view_model.update_results(results)
        self._refresh_visibility()
        if results:
            self.table_view.resizeColumnsToContents()

    # --- helpers ---
    def _refresh_visibility(self) -> None:
        results_available = self.view_model.results
        show_table = self._table_enabled and len(results_available) > 0

        self.table_view.setVisible(show_table)
        self.search_container.setVisible(show_table)
        self.actions_container.setVisible(show_table)

        if not self._table_enabled:
            self.placeholder_label.setText("Interactive results table has been disabled in Output settings.")
        elif show_table:
            self.placeholder_label.hide()
            return
        elif results_available:
            self.placeholder_label.setText("Results are available, but nothing to display.")
        else:
            self.placeholder_label.setText("Run the workflow to generate results.")
        self.placeholder_label.show()

    def _selected_row(self) -> int | None:
        indexes = self.table_view.selectionModel().selectedRows() if self.table_view.isVisible() else []
        if not indexes:
            return None
        proxy_index = indexes[0]
        return self.proxy_model.mapToSource(proxy_index).row()

    def _copy_selected_alt_text(self) -> None:
        row = self._selected_row()
        if row is None:
            return
        alt_text = self.view_model.results[row]["alt_text"]
        QGuiApplication.clipboard().setText(alt_text)

    def _export_results(self, fmt: str) -> None:
        if not self.view_model.results or not self.table_view.isVisible():
            return
        filters = "CSV Files (*.csv)" if fmt == "csv" else "JSON Files (*.json)"
        path, _ = QFileDialog.getSaveFileName(self, "Export Results", "", filters)
        if not path:
            return
        export_path = Path(path)
        data = self.view_model.results
        try:
            if fmt == "csv":
                with export_path.open("w", encoding="utf-8", newline="") as fh:
                    writer = csv.DictWriter(fh, fieldnames=["original_filename", "new_filename", "alt_text"])
                    writer.writeheader()
                    writer.writerows(data)
            else:
                with export_path.open("w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2, ensure_ascii=False)
        except Exception:
            pass
