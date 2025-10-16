from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


@dataclass
class Command:
    title: str
    description: str
    callback: Callable[[], None]


class CommandPalette(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)
        self.resize(560, 420)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(36, 36, 36, 36)

        container = QFrame()
        container.setObjectName("GlassCard")
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)
        outer.addWidget(container)

        header = QHBoxLayout()
        title = QLabel("Command Palette")
        title.setProperty("state", "title")
        header.addWidget(title)
        header.addStretch()
        close_button = QPushButton("Close")
        close_button.setProperty("text-role", "secondary")
        close_button.clicked.connect(self.reject)
        header.addWidget(close_button)
        layout.addLayout(header)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to search actions… (Esc to dismiss)")
        layout.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        self.list_widget.setWordWrap(True)
        self.list_widget.setUniformItemSizes(False)
        layout.addWidget(self.list_widget, 1)

        self.search_edit.textChanged.connect(self._filter_items)
        self.list_widget.itemActivated.connect(self._execute_item)

        self.commands: List[Command] = []

    def set_commands(self, commands: List[Command]) -> None:
        self.commands = commands
        self._populate()

    def open_palette(self) -> None:
        self._populate()
        self.search_edit.clear()
        self.search_edit.setFocus(Qt.ShortcutFocusReason)
        super().open()

    def _populate(self) -> None:
        self.list_widget.clear()
        for command in self.commands:
            item = QListWidgetItem()
            item.setText(f"{command.title}\n{command.description}")
            item.setData(Qt.UserRole, command)
            self.list_widget.addItem(item)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _filter_items(self, query: str) -> None:
        query_lower = query.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            command: Command = item.data(Qt.UserRole)
            match = query_lower in command.title.lower() or query_lower in command.description.lower()
            item.setHidden(not match)

        visible_items = [self.list_widget.item(i) for i in range(self.list_widget.count()) if not self.list_widget.item(i).isHidden()]
        if visible_items:
            self.list_widget.setCurrentItem(visible_items[0])

    def _execute_item(self, item: QListWidgetItem) -> None:
        command: Command = item.data(Qt.UserRole)
        if command:
            self.close()
            command.callback()

    def keyPressEvent(self, event):  # type: ignore[override]
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current = self.list_widget.currentItem()
            if current:
                self._execute_item(current)
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
