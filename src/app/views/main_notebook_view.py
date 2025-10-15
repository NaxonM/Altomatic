
from PySide6.QtWidgets import QTabWidget
from .workflow_view import WorkflowView
from ..viewmodels.workflow_viewmodel import WorkflowViewModel
from .prompts_model_view import PromptsModelView
from ..viewmodels.prompts_model_viewmodel import PromptsModelViewModel
from .advanced_view import AdvancedView
from ..viewmodels.advanced_viewmodel import AdvancedViewModel

class MainNotebookView(QTabWidget):
    """
    The main notebook view, containing the application's settings tabs.
    """
    def __init__(self, workflow_vm: WorkflowViewModel,
                 prompts_model_vm: PromptsModelViewModel,
                 advanced_vm: AdvancedViewModel):
        super().__init__()
        self.setDocumentMode(True) # Use a modern, flat look for the tabs

        # --- Workflow Tab ---
        self.workflow_view = WorkflowView(workflow_vm)
        self.addTab(self.workflow_view, "Workflow")

        # --- Prompts & Model Tab ---
        self.prompts_model_view = PromptsModelView(prompts_model_vm)
        self.addTab(self.prompts_model_view, "Prompts & Model")

        # --- Advanced Tab ---
        self.advanced_view = AdvancedView(advanced_vm)
        self.addTab(self.advanced_view, "Advanced")
