
import os
from typing import Any, Dict, List

from PySide6.QtCore import QThreadPool, Signal

from src.core.config.manager import load_config as load_config_file, save_config
from src.core.models import get_models_for_provider, get_provider_label

from .advanced_viewmodel import AdvancedViewModel
from .base_viewmodel import BaseViewModel
from .footer_viewmodel import FooterViewModel
from .header_viewmodel import HeaderViewModel
from .input_viewmodel import InputViewModel
from .log_viewmodel import LogViewModel
from .prompts_model_viewmodel import PromptsModelViewModel
from .prompt_editor_viewmodel import PromptEditorViewModel
from .workflow_viewmodel import WorkflowViewModel
from ..views.prompt_editor_view import PromptEditorView
from ..worker import Worker

class MainViewModel(BaseViewModel):
    """
    The main ViewModel, orchestrating all other ViewModels.
    """

    processingStarted = Signal()
    processingFinished = Signal(bool)
    resultsReady = Signal(list)

    def __init__(self):
        super().__init__()
        self.input_vm = InputViewModel()
        self.header_vm = HeaderViewModel()
        self.footer_vm = FooterViewModel()
        self.log_vm = LogViewModel()

        # ViewModels for the notebook tabs
        self.workflow_vm = WorkflowViewModel()
        self.prompts_model_vm = PromptsModelViewModel()
        self.advanced_vm = AdvancedViewModel(self)

        self.thread_pool = QThreadPool()
        self._connect_signals()
        self._load_config()

    def _connect_signals(self):
        """Connects signals between different ViewModels."""
        self.footer_vm.process_button_clicked.connect(self.start_processing)
        self.prompts_model_vm.prompts_vm.edit_prompts_clicked.connect(self.open_prompt_editor)

        self.input_vm.sources_changed.connect(self._update_header_from_sources)
        self.input_vm.sources_summary_changed.connect(
            lambda summary: self.header_vm.update_summaries({"summary_output": summary})
        )

        provider_vm = self.prompts_model_vm.provider_vm
        provider_vm.llm_provider_changed.connect(lambda _: self._update_header_model_summary())
        provider_vm.model_changed.connect(lambda _: self._update_header_model_summary())

        prompts_vm = self.prompts_model_vm.prompts_vm
        prompts_vm.selected_prompt_changed.connect(lambda _: self._update_header_prompt_summary())

        self.input_vm.errorOccurred.connect(self.log_vm.add_log)
        self.footer_vm.errorOccurred.connect(self.log_vm.add_log)
        self.log_vm.errorOccurred.connect(self.log_vm.add_log)

    def start_processing(self):
        """Starts the image processing in a background thread."""
        self.processingStarted.emit()
        worker = Worker(self)
        worker.signals.finished.connect(self.show_results)
        self.thread_pool.start(worker)

    def show_results(self, results: List[Dict[str, Any]]):
        """Displays the results window."""
        if self.workflow_vm.output_vm.show_results_table:
            self.resultsReady.emit(results)
        else:
            # Still provide results payload for potential summaries
            self.resultsReady.emit(results if results else [])
        self.processingFinished.emit(bool(results))

    def open_prompt_editor(self):
        """Opens the prompt editor window."""
        prompt_editor_vm = PromptEditorViewModel()
        self.prompt_editor_view = PromptEditorView(prompt_editor_vm)
        self.prompt_editor_view.exec() # Use exec for a modal dialog
        # Refresh prompts in case they were changed
        self.prompts_model_vm.prompts_vm.prompts = prompt_editor_vm.prompts
        self.prompts_model_vm.prompts_vm.update_prompt_preview()
        self._update_header_prompt_summary()

    # --- Settings ---
    def _load_config(self):
        config = load_config_file()
        self._apply_config(config)

    def load_config(self):
        self._load_config()

    def _apply_config(self, config: Dict[str, Any]):
        provider_vm = self.prompts_model_vm.provider_vm
        provider_vm.llm_provider = config.get("llm_provider", provider_vm.llm_provider)
        provider_vm.model = config.get("llm_model", provider_vm.model)
        provider_vm.openai_api_key = config.get("openai_api_key", "")
        provider_vm.openrouter_api_key = config.get("openrouter_api_key", "")

        prompts_vm = self.prompts_model_vm.prompts_vm
        prompts_vm.selected_prompt = config.get("prompt_key", prompts_vm.selected_prompt)

        context_vm = self.workflow_vm.context_vm
        context_vm.context_text = config.get("context_text", context_vm.context_text)

        processing_vm = self.workflow_vm.processing_vm
        processing_vm.filename_language = config.get("filename_language", processing_vm.filename_language)
        processing_vm.alttext_language = config.get("alttext_language", processing_vm.alttext_language)
        processing_vm.name_detail_level = config.get("name_detail_level", processing_vm.name_detail_level)
        processing_vm.vision_detail = config.get("vision_detail", processing_vm.vision_detail)
        processing_vm.ocr_enabled = config.get("ocr_enabled", processing_vm.ocr_enabled)
        processing_vm.tesseract_path = config.get("tesseract_path", processing_vm.tesseract_path)
        processing_vm.ocr_language = config.get("ocr_language", processing_vm.ocr_language)

        output_vm = self.workflow_vm.output_vm
        output_vm.output_folder_option = config.get("output_folder_option", output_vm.output_folder_option)
        output_vm.custom_output_path = config.get("custom_output_path", output_vm.custom_output_path)
        output_vm.show_results_table = config.get("show_results_table", output_vm.show_results_table)

        network_vm = self.advanced_vm.network_vm
        network_vm.proxy_enabled = config.get("proxy_enabled", network_vm.proxy_enabled)
        network_vm.proxy_override = config.get("proxy_override", network_vm.proxy_override)

        appearance_vm = self.advanced_vm.appearance_vm
        appearance_vm.ui_theme = config.get("ui_theme", appearance_vm.ui_theme)

        sources = config.get("input_sources", [])
        if isinstance(sources, list):
            self.input_vm.set_sources(sources)
        include_subdirs = config.get("include_subdirectories")
        if include_subdirs is not None:
            self.input_vm.include_subdirectories = bool(include_subdirs)

        self._update_header_model_summary()
        self._update_header_prompt_summary()
        self._update_header_from_sources(self.input_vm.sources())

    def save_settings(self, geometry: str) -> None:
        config = load_config_file()

        provider_vm = self.prompts_model_vm.provider_vm
        output_vm = self.workflow_vm.output_vm
        processing_vm = self.workflow_vm.processing_vm
        network_vm = self.advanced_vm.network_vm
        prompts_vm = self.prompts_model_vm.prompts_vm
        appearance_vm = self.advanced_vm.appearance_vm
        context_vm = self.workflow_vm.context_vm

        config.update(
            {
                "custom_output_path": output_vm.custom_output_path,
                "output_folder_option": output_vm.output_folder_option,
                "llm_provider": provider_vm.llm_provider,
                "llm_model": provider_vm.model,
                "openai_api_key": provider_vm.openai_api_key,
                "openrouter_api_key": provider_vm.openrouter_api_key,
                "proxy_enabled": network_vm.proxy_enabled,
                "proxy_override": network_vm.proxy_override,
                "filename_language": processing_vm.filename_language,
                "alttext_language": processing_vm.alttext_language,
                "name_detail_level": processing_vm.name_detail_level,
                "vision_detail": processing_vm.vision_detail,
                "ocr_enabled": processing_vm.ocr_enabled,
                "tesseract_path": processing_vm.tesseract_path,
                "ocr_language": processing_vm.ocr_language,
                "ui_theme": appearance_vm.ui_theme,
                "prompt_key": prompts_vm.selected_prompt,
                "context_text": context_vm.context_text,
                "input_sources": self.input_vm.sources(),
                "include_subdirectories": self.input_vm.include_subdirectories,
                "openai_model": config.get("openai_model", provider_vm.model if provider_vm.llm_provider == "openai" else config.get("openai_model")),
                "openrouter_model": config.get("openrouter_model", provider_vm.model if provider_vm.llm_provider == "openrouter" else config.get("openrouter_model")),
                "window_geometry": geometry,
            }
        )

        save_config(config, geometry)

    def _update_header_from_sources(self, sources: List[str]) -> None:
        if not sources:
            summary = "awaiting selection"
        else:
            first = sources[0]
            label = os.path.basename(first) or first
            if len(sources) == 1:
                summary = f"{label}"
            else:
                summary = f"{label} + {len(sources) - 1} more"
        self.header_vm.update_summaries({"summary_output": summary})

    def _update_header_model_summary(self) -> None:
        provider_vm = self.prompts_model_vm.provider_vm
        provider_label = get_provider_label(provider_vm.llm_provider)
        models = get_models_for_provider(provider_vm.llm_provider)
        model_entry = models.get(provider_vm.model, {})
        model_label = model_entry.get("label", provider_vm.model)
        self.header_vm.update_summaries({"summary_model": f"{provider_label} • {model_label}"})

    def _update_header_prompt_summary(self) -> None:
        prompts_vm = self.prompts_model_vm.prompts_vm
        labels = prompts_vm.get_prompt_labels()
        label = labels.get(prompts_vm.selected_prompt, prompts_vm.selected_prompt)
        self.header_vm.update_summaries({"summary_prompt": label})
