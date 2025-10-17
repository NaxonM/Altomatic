from __future__ import annotations

import os
from datetime import datetime
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMenu,
    QPushButton,
    QSizePolicy,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

from .base_view import BaseView
from ..viewmodels.input_viewmodel import InputViewModel


class SourcesPanel(QFrame):
    pathsDropped = Signal(list)
    selectionChanged = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DropArea")
        self.setProperty("drag", "false")
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        title = QLabel("Selected sources")
        title.setProperty("state", "subtitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.add_button = QPushButton("Add sources…")
        self.add_button.setProperty("text-role", "primary")
        header_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.setProperty("text-role", "secondary")
        header_layout.addWidget(self.remove_button)

        self.clear_button = QPushButton("Clear All")
        self.clear_button.setProperty("text-role", "secondary")
        header_layout.addWidget(self.clear_button)

        layout.addLayout(header_layout)

        self._stack_container = QWidget()
        self._stack_layout = QStackedLayout(self._stack_container)
        self._stack_layout.setContentsMargins(0, 0, 0, 0)

        self.placeholder_label = QLabel("Drop files or folders here")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setWordWrap(True)
        self.placeholder_label.setProperty("state", "muted")
        self._stack_layout.addWidget(self.placeholder_label)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["", "Name", "Size", "Date Modified"])
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_widget.setSelectionMode(QTableWidget.NoSelection)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.setSortingEnabled(True)
        self._stack_layout.addWidget(self.table_widget)

        layout.addWidget(self._stack_container, 1)

        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(6)
        self.summary_label = QLabel()
        self.summary_label.setProperty("state", "muted")
        summary_layout.addWidget(self.summary_label)
        summary_layout.addStretch()
        self.subdirectories_checkbox = QCheckBox("Include subdirectories when folders are added")
        summary_layout.addWidget(self.subdirectories_checkbox)
        layout.addLayout(summary_layout)

        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(6)
        footer_layout.addStretch()
        self.image_count_label = QLabel()
        self.image_count_label.setProperty("state", "caption")
        footer_layout.addWidget(self.image_count_label)
        layout.addLayout(footer_layout)

        self.set_empty_state(True)

        self.table_widget.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item: QTableWidgetItem):
        if item.column() == 0:
            self.selectionChanged.emit(self.get_selected_paths())

    def get_selected_paths(self) -> List[str]:
        selected_paths = []
        for i in range(self.table_widget.rowCount()):
            item = self.table_widget.item(i, 0)
            if item and item.checkState() == Qt.Checked:
                name_item = self.table_widget.item(i, 1)
                if name_item:
                    selected_paths.append(name_item.data(Qt.UserRole))
        return selected_paths

    # --- Drag and drop handling ---
    def dragEnterEvent(self, event):  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("drag", "true")
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):  # type: ignore[override]
        self.setProperty("drag", "false")
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):  # type: ignore[override]
        event.setDropAction(Qt.CopyAction)
        event.accept()
        paths: List[str] = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                paths.append(url.toLocalFile())
        if paths:
            self.pathsDropped.emit(paths)
        self.setProperty("drag", "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_empty_state(self, empty: bool) -> None:
        self._stack_layout.setCurrentIndex(0 if empty else 1)
        self.remove_button.setEnabled(not empty)
        self.clear_button.setEnabled(not empty)


class InputView(BaseView):
    """Collects user sources and related options."""

    def __init__(self, view_model: InputViewModel):
        super().__init__(view_model)
        self.setObjectName("SurfaceCard")
        self._setup_ui()
        self._connect_signals()
        self._populate_sources(self.view_model.sources())
        self.sources_panel.summary_label.setText(self.view_model.sources_summary)
        self.sources_panel.image_count_label.setText(self.view_model.image_count_text)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        headline = QLabel("Sources")
        headline.setProperty("state", "title")
        layout.addWidget(headline)

        helper = QLabel("Add images or folders, or drop them anywhere in this area. Supported formats are detected automatically.")
        helper.setProperty("state", "subtitle")
        helper.setWordWrap(True)
        layout.addWidget(helper)

        self.sources_panel = SourcesPanel(self)
        layout.addWidget(self.sources_panel)

    def _connect_signals(self) -> None:
        # View to ViewModel
        self.sources_panel.pathsDropped.connect(self.view_model.add_sources)
        self.sources_panel.add_button.clicked.connect(self._show_add_menu)
        self.sources_panel.remove_button.clicked.connect(self._remove_selected)
        self.sources_panel.clear_button.clicked.connect(self.view_model.clear_sources)
        self.sources_panel.subdirectories_checkbox.toggled.connect(
            lambda checked: setattr(self.view_model, "include_subdirectories", checked)
        )
        self.sources_panel.selectionChanged.connect(self.view_model.set_selected_sources)

        # ViewModel to View
        self.view_model.sources_changed.connect(self._populate_sources)
        self.view_model.sources_summary_changed.connect(self.sources_panel.summary_label.setText)
        self.view_model.include_subdirectories_changed.connect(self.sources_panel.subdirectories_checkbox.setChecked)
        self.view_model.image_count_text_changed.connect(self.sources_panel.image_count_label.setText)

        self._add_menu = QMenu(self)
        self._add_menu.addAction("Add files…", self._add_files)
        self._add_menu.addAction("Add folder…", self._add_folder)

    # --- Slots ---
    def _show_add_menu(self) -> None:
        anchor = self.sources_panel.add_button
        menu_pos = anchor.mapToGlobal(anchor.rect().bottomLeft())
        self._add_menu.exec(menu_pos)

    def _add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.heic *.heif);;All Files (*)",
        )
        if paths:
            self.view_model.add_sources(paths)

    def _add_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            self.view_model.add_sources([path])

    def _remove_selected(self) -> None:
        selected_paths = self.sources_panel.get_selected_paths()
        for path in selected_paths:
            self.view_model.remove_source(path)

    def _populate_sources(self, sources: List[str]) -> None:
        self.sources_panel.table_widget.setRowCount(0)
        self.sources_panel.table_widget.setSortingEnabled(False)
        for path in sources:
            row_position = self.sources_panel.table_widget.rowCount()
            self.sources_panel.table_widget.insertRow(row_position)

            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Checked)
            self.sources_panel.table_widget.setItem(row_position, 0, checkbox)

            name_item = QTableWidgetItem(os.path.basename(path) or path)
            name_item.setData(Qt.UserRole, path)
            self.sources_panel.table_widget.setItem(row_position, 1, name_item)

            size_item = QTableWidgetItem(f"{os.path.getsize(path) / 1024:.2f} KB")
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.sources_panel.table_widget.setItem(row_position, 2, size_item)

            modified_date = datetime.fromtimestamp(os.path.getmtime(path))
            date_item = QTableWidgetItem(modified_date.strftime("%Y-%m-%d %H:%M:%S"))
            self.sources_panel.table_widget.setItem(row_position, 3, date_item)

        self.sources_panel.table_widget.setSortingEnabled(True)
        self.sources_panel.set_empty_state(len(sources) == 0)

    # --- Public helpers for external triggers ---
    def trigger_add_files(self) -> None:
        self._add_files()

    def trigger_add_sources(self) -> None:
        self._show_add_menu()

    def trigger_clear_sources(self) -> None:
        self.view_model.clear_sources()