
from PySide6.QtCore import Signal, Property
from .base_viewmodel import BaseViewModel
from src.core.prompts import load_prompts

class PromptsViewModel(BaseViewModel):
    """
    ViewModel for the Prompts sub-tab.
    """
    selected_prompt_changed = Signal(str)
    prompt_preview_text_changed = Signal(str)
    edit_prompts_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.prompts = load_prompts()
        self._selected_prompt = "default"
        self._prompt_preview_text = ""
        self.update_prompt_preview()

    @Property(str, notify=selected_prompt_changed)
    def selected_prompt(self):
        return self._selected_prompt

    @selected_prompt.setter
    def selected_prompt(self, value):
        if self._selected_prompt != value:
            self._selected_prompt = value
            self.selected_prompt_changed.emit(value)
            self.update_prompt_preview()

    @Property(str, notify=prompt_preview_text_changed)
    def prompt_preview_text(self):
        return self._prompt_preview_text

    @prompt_preview_text.setter
    def prompt_preview_text(self, value):
        if self._prompt_preview_text != value:
            self._prompt_preview_text = value
            self.prompt_preview_text_changed.emit(value)

    def get_prompt_labels(self):
        return {k: v.get("label", k) for k, v in self.prompts.items()}

    def update_prompt_preview(self):
        prompt = self.prompts.get(self.selected_prompt, {})
        label = prompt.get("label", self.selected_prompt)
        template = prompt.get("template", "")
        self.prompt_preview_text = f"{label}\\n\\n{template}".strip()

    def edit_prompts(self):
        self.edit_prompts_clicked.emit()
