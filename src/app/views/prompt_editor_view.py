
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit,
    QLineEdit, QPushButton, QSplitter, QInputDialog, QMessageBox
)
from .base_view import BaseView
from ..viewmodels.prompt_editor_viewmodel import PromptEditorViewModel

class PromptEditorView(BaseView, QDialog):
    """
    The Prompt Editor window view.
    """
    def __init__(self, view_model: PromptEditorViewModel):
        super().__init__(view_model)
        self.setWindowTitle("Prompt Editor")
        self.setGeometry(200, 200, 800, 600)
        self._setup_ui()
        self._connect_signals()
        self._update_prompt_list()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(self)
        main_layout.addWidget(splitter)

        # Left panel: Prompt list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.prompt_list = QListWidget()
        left_layout.addWidget(self.prompt_list)
        splitter.addWidget(left_panel)

        # Right panel: Prompt details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.prompt_label_edit = QLineEdit()
        right_layout.addWidget(self.prompt_label_edit)
        self.prompt_template_edit = QTextEdit()
        right_layout.addWidget(self.prompt_template_edit)
        splitter.addWidget(right_panel)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.delete_button = QPushButton("Delete")
        self.save_button = QPushButton("Save")
        self.save_and_close_button = QPushButton("Save & Close")
        self.close_button = QPushButton("Close")
        toolbar_layout.addWidget(self.add_button)
        toolbar_layout.addWidget(self.delete_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.save_button)
        toolbar_layout.addWidget(self.save_and_close_button)
        toolbar_layout.addWidget(self.close_button)
        main_layout.addLayout(toolbar_layout)

    def _connect_signals(self):
        # View to ViewModel
        self.prompt_list.currentItemChanged.connect(self._on_prompt_selected)
        self.prompt_label_edit.textChanged.connect(
            lambda value: setattr(self.view_model, "prompt_label", value)
        )
        self.prompt_template_edit.textChanged.connect(
            lambda: setattr(self.view_model, "prompt_template", self.prompt_template_edit.toPlainText())
        )

        self.add_button.clicked.connect(self._add_prompt)
        self.delete_button.clicked.connect(self._delete_prompt)
        self.save_button.clicked.connect(self.view_model.save_prompt)
        self.save_and_close_button.clicked.connect(self._save_and_close)
        self.close_button.clicked.connect(self.close)

        # ViewModel to View
        self.view_model.prompts_changed.connect(self._update_prompt_list)
        self.view_model.selected_prompt_key_changed.connect(self._update_selection)
        self.view_model.prompt_label_changed.connect(self.prompt_label_edit.setText)
        self.view_model.prompt_template_changed.connect(self.prompt_template_edit.setPlainText)

    def _update_prompt_list(self):
        self.prompt_list.clear()
        for key, prompt in self.view_model.prompts.items():
            self.prompt_list.addItem(f"{prompt.get('label', key)} ({key})")

    def _on_prompt_selected(self, current, previous):
        if current:
            key = current.text().split('(')[-1][:-1] # Extract key from "Label (key)"
            self.view_model.selected_prompt_key = key

    def _update_selection(self, key):
        for i in range(self.prompt_list.count()):
            item = self.prompt_list.item(i)
            if item.text().endswith(f"({key})"):
                item.setSelected(True)
                self.prompt_list.setCurrentItem(item)
                break

    def _add_prompt(self):
        text, ok = QInputDialog.getText(self, "New Prompt", "Enter a label for the new prompt:")
        if ok and text:
            self.view_model.add_prompt(text)

    def _delete_prompt(self):
        reply = QMessageBox.question(self, 'Delete Prompt',
                                     "Are you sure you want to delete this prompt?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.view_model.delete_prompt()

    def _save_and_close(self):
        self.view_model.save_prompt()
        self.close()
