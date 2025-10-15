
from PySide6.QtCore import Signal, Property, str, QObject
from .base_viewmodel import BaseViewModel
from src.altomatic.prompts import load_prompts, save_prompts
from src.altomatic.utils import slugify

class PromptEditorViewModel(BaseViewModel):
    """
    ViewModel for the Prompt Editor window.
    """
    prompts_changed = Signal()
    selected_prompt_key_changed = Signal(str)
    prompt_label_changed = Signal(str)
    prompt_template_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._prompts = load_prompts()
        self._selected_prompt_key = "default"
        self._prompt_label = ""
        self._prompt_template = ""
        self.update_fields_from_selection()

    @Property(QObject, notify=prompts_changed)
    def prompts(self):
        return self._prompts

    @Property(str, notify=selected_prompt_key_changed)
    def selected_prompt_key(self):
        return self._selected_prompt_key

    @selected_prompt_key.setter
    def selected_prompt_key(self, value):
        if self._selected_prompt_key != value:
            self._selected_prompt_key = value
            self.selected_prompt_key_changed.emit(value)
            self.update_fields_from_selection()

    @Property(str, notify=prompt_label_changed)
    def prompt_label(self):
        return self._prompt_label

    @prompt_label.setter
    def prompt_label(self, value):
        if self._prompt_label != value:
            self._prompt_label = value
            self.prompt_label_changed.emit(value)

    @Property(str, notify=prompt_template_changed)
    def prompt_template(self):
        return self._prompt_template

    @prompt_template.setter
    def prompt_template(self, value):
        if self._prompt_template != value:
            self._prompt_template = value
            self.prompt_template_changed.emit(value)

    def update_fields_from_selection(self):
        prompt = self._prompts.get(self.selected_prompt_key, {})
        self.prompt_label = prompt.get("label", self.selected_prompt_key)
        self.prompt_template = prompt.get("template", "")

    def add_prompt(self, name):
        key = slugify(name) or f"prompt{len(self._prompts) + 1}"
        base_key = key
        suffix = 1
        while key in self._prompts:
            suffix += 1
            key = f"{base_key}-{suffix}"
        self._prompts[key] = {"label": name.strip(), "template": ""}
        self.prompts_changed.emit()
        self.selected_prompt_key = key

    def delete_prompt(self):
        if self.selected_prompt_key != "default" and len(self._prompts) > 1:
            del self._prompts[self.selected_prompt_key]
            self.prompts_changed.emit()
            self.selected_prompt_key = "default"

    def save_prompt(self):
        if self.selected_prompt_key:
            self._prompts[self.selected_prompt_key] = {
                "label": self.prompt_label,
                "template": self.prompt_template,
            }
            save_prompts(self._prompts)
            self.prompts_changed.emit()
