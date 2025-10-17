from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QStackedLayout,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .base_view import BaseView
from ..viewmodels.prompts_model_viewmodel import PromptsModelViewModel
from ..viewmodels.workflow_viewmodel import WorkflowViewModel


class DescribeView(BaseView):
    """Configure provider, model, prompt, and optional context."""

    def __init__(self, prompts_model_vm: PromptsModelViewModel, workflow_vm: WorkflowViewModel) -> None:
        super().__init__(prompts_model_vm)
        self.setObjectName("SurfaceCard")

        self.prompts_model_vm = prompts_model_vm
        self.provider_vm = prompts_model_vm.provider_vm
        self.prompts_vm = prompts_model_vm.prompts_vm
        self.context_vm = workflow_vm.context_vm

        self._updating = False
        self._api_overlay_force_hidden = False
        self._api_focus_in_handler = None
        self._api_focus_out_handler = None
        self._api_focus_in_handler = None
        self._api_focus_out_handler = None
        self._api_focus_in_handler = None
        self._api_focus_out_handler = None
        self._api_focus_in_handler = None
        self._api_focus_out_handler = None
        self._setup_ui()
        self._connect_signals()
        self._refresh_provider()
        self._refresh_prompts()
        self._refresh_context()
        self._update_api_key_indicator(self._provider_has_key())

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("Describe")
        title.setProperty("state", "title")
        layout.addWidget(title)

        subtitle = QLabel("Choose your provider, model, and prompt. Adjust context to guide the analysis.")
        subtitle.setProperty("state", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        provider_card = QFrame()
        provider_card.setObjectName("InsetCard")
        provider_form = QFormLayout(provider_card)
        provider_form.setHorizontalSpacing(10)
        provider_form.setVerticalSpacing(10)

        self.provider_combo = QComboBox()
        for label, provider_id in sorted(self.provider_vm.provider_labels.items()):
            self.provider_combo.addItem(label, provider_id)
        provider_form.addRow("Provider", self.provider_combo)

        self.model_combo = QComboBox()
        provider_form.addRow("Model", self.model_combo)

        self.api_key_label = QLabel("API Key")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Enter provider key (optional)")

        api_field_widget = QWidget()
        field_stack = QStackedLayout(api_field_widget)
        field_stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        field_stack.setContentsMargins(0, 0, 0, 0)

        field_container = QWidget()
        field_layout = QVBoxLayout(field_container)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(0)
        field_layout.addWidget(self.api_key_edit)

        overlay_container = QWidget()
        overlay_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        overlay_container.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        overlay_container.setVisible(False)

        overlay_layout = QVBoxLayout(overlay_container)
        overlay_layout.setContentsMargins(0, 0, 0, 0)

        overlay_wrapper = QWidget()
        overlay_wrapper.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        overlay_wrapper.setStyleSheet("background: transparent;")
        overlay_wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        overlay_wrapper_layout = QVBoxLayout(overlay_wrapper)
        overlay_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        overlay_wrapper_layout.setSpacing(0)
        overlay_wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.api_key_overlay = QLabel("Configured – click to edit")
        self.api_key_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.api_key_overlay.setStyleSheet(
            "background-color: rgba(12, 94, 196, 0.88);"
            "color: #ffffff;"
            "font-weight: 600;"
            "border-radius: 10px;"
            "padding: 6px;"
        )
        self.api_key_overlay.setMinimumHeight(32)
        self.api_key_overlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.api_key_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        overlay_wrapper_layout.addWidget(self.api_key_overlay)
        overlay_layout.addWidget(overlay_wrapper)

        field_stack.addWidget(field_container)
        field_stack.addWidget(overlay_container)

        self.api_key_overlay_container = overlay_container
        provider_form.addRow(self.api_key_label, api_field_widget)

        layout.addWidget(provider_card)

        prompt_card = QFrame()
        prompt_card.setObjectName("InsetCard")
        prompt_layout = QVBoxLayout(prompt_card)
        prompt_layout.setSpacing(10)

        prompt_row = QHBoxLayout()
        prompt_row.setSpacing(8)
        prompt_label = QLabel("Prompt preset")
        prompt_label.setProperty("state", "muted")
        prompt_row.addWidget(prompt_label)
        self.prompt_combo = QComboBox()
        prompt_row.addWidget(self.prompt_combo, 1)
        self.edit_prompts_button = QPushButton("Edit…")
        self.edit_prompts_button.setProperty("text-role", "ghost")
        prompt_row.addWidget(self.edit_prompts_button)
        prompt_layout.addLayout(prompt_row)

        self.prompt_preview = QTextEdit()
        self.prompt_preview.setReadOnly(True)
        self.prompt_preview.setPlaceholderText("Prompt template preview")
        self.prompt_preview.setMinimumHeight(80)
        self.prompt_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        prompt_layout.addWidget(self.prompt_preview)

        self.context_edit = QTextEdit()
        self.context_edit.setPlaceholderText("Optional context to include with every request…")
        self.context_edit.setMinimumHeight(80)
        self.context_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        prompt_layout.addWidget(self.context_edit)

        layout.addWidget(prompt_card)
        layout.addStretch()

    def _connect_signals(self) -> None:
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        self.api_key_edit.textChanged.connect(self._on_api_key_changed)
        self.api_key_edit.editingFinished.connect(self._on_api_key_editing_finished)

        self.prompt_combo.currentIndexChanged.connect(self._on_prompt_changed)
        self.edit_prompts_button.clicked.connect(self.prompts_vm.edit_prompts)
        self.context_edit.textChanged.connect(self._on_context_changed)

        self.provider_vm.llm_provider_changed.connect(self._refresh_provider)
        self.provider_vm.model_changed.connect(self._refresh_provider)
        self.provider_vm.openai_api_key_changed.connect(self._refresh_api_key)
        self.provider_vm.openrouter_api_key_changed.connect(self._refresh_api_key)
        self.provider_vm.openai_api_key_changed.connect(
            lambda _: self._update_api_key_indicator(self._provider_has_key())
        )
        self.provider_vm.openrouter_api_key_changed.connect(
            lambda _: self._update_api_key_indicator(self._provider_has_key())
        )

        self.api_key_overlay.mousePressEvent = self._handle_api_overlay_click  # type: ignore[assignment]
        self._api_focus_in_handler = self.api_key_edit.focusInEvent
        self._api_focus_out_handler = self.api_key_edit.focusOutEvent
        self.api_key_edit.focusInEvent = self._api_field_focus_in  # type: ignore[assignment]
        self.api_key_edit.focusOutEvent = self._api_field_focus_out  # type: ignore[assignment]

        self.prompts_vm.selected_prompt_changed.connect(self._refresh_prompts)
        self.prompts_vm.prompt_preview_text_changed.connect(self.prompt_preview.setPlainText)
        self.context_vm.context_text_changed.connect(self._set_context_text)

    def _refresh_provider(self) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            provider_id = self.provider_vm.llm_provider
            index = self.provider_combo.findData(provider_id)
            if index >= 0:
                self.provider_combo.setCurrentIndex(index)

            models = self.provider_vm.get_models_for_current_provider()
            current_model = self.provider_vm.model
            self.model_combo.blockSignals(True)
            self.model_combo.clear()
            for model_id, info in models.items():
                label = info.get("label", model_id)
                self.model_combo.addItem(label, model_id)
            model_index = self.model_combo.findData(current_model)
            if model_index >= 0:
                self.model_combo.setCurrentIndex(model_index)
            self.model_combo.blockSignals(False)

            self._refresh_api_key()
        finally:
            self._updating = False

    def _refresh_api_key(self) -> None:
        if self._updating:
            return
        provider_id = self.provider_vm.llm_provider
        self._updating = True
        try:
            if provider_id == "openai":
                self.api_key_label.setText("OpenAI API Key")
                value = self.provider_vm.openai_api_key
                self._set_api_field_value(value, reveal=False)
                self._update_api_key_indicator(bool(value))
            elif provider_id == "openrouter":
                self.api_key_label.setText("OpenRouter API Key")
                value = self.provider_vm.openrouter_api_key
                self._set_api_field_value(value, reveal=False)
                self._update_api_key_indicator(bool(value))
            else:
                self.api_key_label.setText("API Key")
                self.api_key_edit.clear()
                self._update_api_key_indicator(False)
        finally:
            self._updating = False

    def _refresh_prompts(self) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            labels = self.prompts_vm.get_prompt_labels()
            selected = self.prompts_vm.selected_prompt

            self.prompt_combo.blockSignals(True)
            self.prompt_combo.clear()
            for key, label in labels.items():
                self.prompt_combo.addItem(label, key)
            index = self.prompt_combo.findData(selected)
            if index >= 0:
                self.prompt_combo.setCurrentIndex(index)
            self.prompt_combo.blockSignals(False)

            self.prompt_preview.setPlainText(self.prompts_vm.prompt_preview_text)
        finally:
            self._updating = False

    def _refresh_context(self) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            self.context_edit.setPlainText(self.context_vm.context_text)
        finally:
            self._updating = False

    def _on_provider_changed(self) -> None:
        if self._updating:
            return
        provider_id = self.provider_combo.currentData()
        if provider_id:
            self.provider_vm.llm_provider = provider_id

    def _on_model_changed(self) -> None:
        if self._updating:
            return
        model_id = self.model_combo.currentData()
        if model_id:
            self.provider_vm.model = model_id

    def _on_api_key_changed(self, text: str) -> None:
        if self._updating:
            return
        self._api_overlay_force_hidden = True
        provider_id = self.provider_vm.llm_provider
        if provider_id == "openai":
            self.provider_vm.openai_api_key = text
        elif provider_id == "openrouter":
            self.provider_vm.openrouter_api_key = text
        self._update_api_key_indicator(bool(text))

    def _on_prompt_changed(self) -> None:
        if self._updating:
            return
        key = self.prompt_combo.currentData()
        if key:
            self.prompts_vm.selected_prompt = key

    def _on_context_changed(self) -> None:
        if self._updating:
            return
        self.context_vm.context_text = self.context_edit.toPlainText()

    def _set_context_text(self, text: str) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            self.context_edit.setPlainText(text)
        finally:
            self._updating = False

    def _update_api_key_indicator(self, has_value: bool) -> None:
        if not has_value:
            self._api_overlay_force_hidden = False
        should_show = has_value and not self._api_overlay_force_hidden and not self.api_key_edit.hasFocus()
        self.api_key_overlay.setVisible(should_show)

    def _provider_has_key(self) -> bool:
        provider_id = self.provider_vm.llm_provider
        if provider_id == "openai":
            return bool(self.provider_vm.openai_api_key)
        if provider_id == "openrouter":
            return bool(self.provider_vm.openrouter_api_key)
        return False

    def _handle_api_overlay_click(self, event) -> None:
        self._api_overlay_force_hidden = True
        self.api_key_overlay.hide()
        self._set_api_field_value(self._get_current_key(), reveal=True)
        self.api_key_edit.setFocus()
        self.api_key_edit.selectAll()
        event.accept()

    def _on_api_key_editing_finished(self) -> None:
        if not self.api_key_edit.text():
            provider_id = self.provider_vm.llm_provider
            if provider_id == "openai":
                self.provider_vm.openai_api_key = ""
            elif provider_id == "openrouter":
                self.provider_vm.openrouter_api_key = ""
        self._api_overlay_force_hidden = False
        self._set_api_field_value(self._get_current_key(), reveal=False)
        self._update_api_key_indicator(self._provider_has_key())

    def _api_field_focus_in(self, event) -> None:
        self._api_overlay_force_hidden = True
        self.api_key_overlay.hide()
        self._set_api_field_value(self._get_current_key(), reveal=True)
        if self._api_focus_in_handler:
            self._api_focus_in_handler(event)

    def _api_field_focus_out(self, event) -> None:
        if self._api_focus_out_handler:
            self._api_focus_out_handler(event)
        self._api_overlay_force_hidden = False
        if not self.api_key_edit.text():
            provider_id = self.provider_vm.llm_provider
            if provider_id == "openai":
                self.provider_vm.openai_api_key = ""
            elif provider_id == "openrouter":
                self.provider_vm.openrouter_api_key = ""
        self._set_api_field_value(self._get_current_key(), reveal=False)
        self._update_api_key_indicator(self._provider_has_key())

    def _set_api_field_value(self, value: str, *, reveal: bool) -> None:
        self.api_key_edit.blockSignals(True)
        if reveal:
            self.api_key_edit.setText(value)
        else:
            self.api_key_edit.clear()
        self.api_key_edit.blockSignals(False)

    def _get_current_key(self) -> str:
        provider_id = self.provider_vm.llm_provider
        if provider_id == "openai":
            return self.provider_vm.openai_api_key
        if provider_id == "openrouter":
            return self.provider_vm.openrouter_api_key
        return ""


class OutputSettingsView(BaseView):
    """Configure output destinations and result preferences."""

    def __init__(self, workflow_vm: WorkflowViewModel) -> None:
        super().__init__(workflow_vm.output_vm)
        self.setObjectName("SurfaceCard")
        self.output_vm = workflow_vm.output_vm

        self._updating = False
        self._setup_ui()
        self._connect_signals()
        self._refresh_output()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("Output")
        title.setProperty("state", "title")
        layout.addWidget(title)

        subtitle = QLabel("Select where generated text and files should be saved.")
        subtitle.setProperty("state", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("InsetCard")
        form = QFormLayout(card)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(10)

        self.output_option_combo = QComboBox()
        self.output_option_combo.addItems(["Same as input", "Pictures", "Desktop", "Custom"])
        form.addRow("Destination", self.output_option_combo)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.custom_output_edit = QLineEdit()
        path_row.addWidget(self.custom_output_edit)
        self.custom_browse_button = QPushButton("Browse…")
        self.custom_browse_button.setProperty("text-role", "ghost")
        path_row.addWidget(self.custom_browse_button)
        form.addRow("Custom path", path_row)

        self.show_results_checkbox = QCheckBox("Show results table after run")
        form.addRow("", self.show_results_checkbox)

        layout.addWidget(card)
        layout.addStretch()

    def _connect_signals(self) -> None:
        self.output_option_combo.currentIndexChanged.connect(self._on_output_option_changed)
        self.custom_output_edit.textChanged.connect(self._on_custom_output_changed)
        self.custom_browse_button.clicked.connect(self._browse_custom_output)
        self.show_results_checkbox.toggled.connect(self._on_show_results_toggled)

        self.output_vm.output_folder_option_changed.connect(self._refresh_output)
        self.output_vm.custom_output_path_changed.connect(self._refresh_output)
        self.output_vm.show_results_table_changed.connect(self._refresh_output)

    def _refresh_output(self) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            option = self.output_vm.output_folder_option
            index = self.output_option_combo.findText(option)
            if index >= 0:
                self.output_option_combo.setCurrentIndex(index)

            self.custom_output_edit.setText(self.output_vm.custom_output_path)
            is_custom = option == "Custom"
            self.custom_output_edit.setEnabled(is_custom)
            self.custom_browse_button.setEnabled(is_custom)
            self.show_results_checkbox.setChecked(self.output_vm.show_results_table)
        finally:
            self._updating = False

    def _on_output_option_changed(self) -> None:
        if self._updating:
            return
        option = self.output_option_combo.currentText()
        self.output_vm.output_folder_option = option

    def _on_custom_output_changed(self, text: str) -> None:
        if self._updating:
            return
        self.output_vm.custom_output_path = text

    def _browse_custom_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder", os.path.expanduser("~"))
        if path:
            self.output_vm.custom_output_path = path

    def _on_show_results_toggled(self, checked: bool) -> None:
        if self._updating:
            return
        self.output_vm.show_results_table = checked
