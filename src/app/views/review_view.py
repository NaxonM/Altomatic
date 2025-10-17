from __future__ import annotations

import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QLineEdit,
)

from .base_view import BaseView
from ..viewmodels.results_viewmodel import ResultsViewModel


class ResultItemWidget(QWidget):
    """Custom widget for displaying a single result item."""

    def __init__(self, item_data: Dict[str, Any]):
        super().__init__()
        self.item_data = item_data
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Image Preview
        self.image_preview = QLabel()
        self.image_preview.setFixedSize(100, 100)
        self.image_preview.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(self.item_data["original_path"])
        self.image_preview.setPixmap(pixmap.scaled(self.image_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        main_layout.addWidget(self.image_preview)

        # Details Layout
        details_layout = QVBoxLayout()
        details_layout.setSpacing(8)

        # New Filename
        name_layout = QHBoxLayout()
        name_label = QLabel("New Filename:")
        name_label.setProperty("state", "muted")
        self.name_text = QLineEdit(self.item_data["new_filename"])
        self.name_text.setReadOnly(True)
        copy_name_button = QPushButton("Copy")
        copy_name_button.clicked.connect(self._copy_name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_text, 1)
        name_layout.addWidget(copy_name_button)
        details_layout.addLayout(name_layout)

        # Alt Text
        alt_layout = QHBoxLayout()
        alt_label = QLabel("Alt Text:")
        alt_label.setProperty("state", "muted")
        self.alt_text = QTextEdit(self.item_data["alt_text"])
        self.alt_text.setReadOnly(True)
        self.alt_text.setFixedHeight(60)
        copy_alt_button = QPushButton("Copy")
        copy_alt_button.clicked.connect(self._copy_alt_text)
        alt_layout.addWidget(alt_label)
        alt_layout.addWidget(self.alt_text, 1)
        alt_layout.addWidget(copy_alt_button)
        details_layout.addLayout(alt_layout)

        main_layout.addLayout(details_layout)

    def _copy_name(self):
        QGuiApplication.clipboard().setText(self.item_data["new_filename"])

    def _copy_alt_text(self):
        QGuiApplication.clipboard().setText(self.item_data["alt_text"])


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

        # Header
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        self.title_label = QLabel("Review")
        self.title_label.setProperty("state", "title")
        header_layout.addWidget(self.title_label)
        self.subtitle_label = QLabel("Inspect processed results, copy alt text, or export to share with your team.")
        self.subtitle_label.setProperty("state", "subtitle")
        self.subtitle_label.setWordWrap(True)
        header_layout.addWidget(self.subtitle_label)
        layout.addWidget(header_frame)

        # Placeholder for when no results are available
        self.placeholder_label = QLabel("Run the workflow to generate results.")
        self.placeholder_label.setProperty("state", "muted")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setWordWrap(True)
        layout.addWidget(self.placeholder_label, 1)

        # Main content area with list and actions
        self.content_frame = QFrame()
        self.content_frame.setObjectName("SurfaceCard")
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setSpacing(10)
        layout.addWidget(self.content_frame, 1)

        # Results list
        self.results_list = QListWidget()
        content_layout.addWidget(self.results_list)

        # Actions row
        actions_frame = QFrame()
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)
        self.export_csv_button = QPushButton("Export CSV")
        self.export_json_button = QPushButton("Export JSON")
        self.open_folder_button = QPushButton("Open Output Folder")
        actions_layout.addWidget(self.open_folder_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self.export_csv_button)
        actions_layout.addWidget(self.export_json_button)
        content_layout.addWidget(actions_frame)

    def _bind_signals(self) -> None:
        self.export_csv_button.clicked.connect(lambda: self._export_results("csv"))
        self.export_json_button.clicked.connect(lambda: self._export_results("json"))
        self.open_folder_button.clicked.connect(self._open_output_folder)

    def _open_output_folder(self) -> None:
        if self.session_path and os.path.isdir(self.session_path):
            os.startfile(self.session_path)

    def set_results(self, results: List[Dict[str, Any]], table_enabled: bool, session_path: str) -> None:
        self._table_enabled = table_enabled
        self.view_model.update_results(results)
        self.session_path = session_path
        self._refresh_visibility()
        self._populate_results_list(results)

    def _populate_results_list(self, results: List[Dict[str, Any]]):
        self.results_list.clear()
        for result in results:
            item = QListWidgetItem(self.results_list)
            widget = ResultItemWidget(result)
            item.setSizeHint(widget.sizeHint())
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)

    def _refresh_visibility(self) -> None:
        has_results = bool(self.view_model.results)
        self.content_frame.setVisible(has_results)
        self.placeholder_label.setVisible(not has_results)

    def _export_results(self, fmt: str) -> None:
        if not self.view_model.results:
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