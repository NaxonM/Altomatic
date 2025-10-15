
from PySide6.QtWidgets import QTabWidget, QVBoxLayout
from .base_view import BaseView
from ..viewmodels.prompts_model_viewmodel import PromptsModelViewModel
from .provider_view import ProviderView
from .prompts_view import PromptsView

class PromptsModelView(BaseView):
    """
    The Prompts & Model view, containing sub-tabs for provider and prompts.
    """
    def __init__(self, view_model: PromptsModelViewModel):
        super().__init__(view_model)
        self._setup_ui()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)
        notebook = QTabWidget(self)

        # Create the sub-tab views
        provider_view = ProviderView(self.view_model.provider_vm)
        prompts_view = PromptsView(self.view_model.prompts_vm)

        notebook.addTab(provider_view, "LLM Provider")
        notebook.addTab(prompts_view, "Prompts")

        layout.addWidget(notebook)
