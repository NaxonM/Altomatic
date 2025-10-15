
from .base_viewmodel import BaseViewModel
from .context_viewmodel import ContextViewModel
from .processing_viewmodel import ProcessingViewModel
from .output_viewmodel import OutputViewModel

class WorkflowViewModel(BaseViewModel):
    """
    ViewModel for the Workflow tab.
    """
    def __init__(self):
        super().__init__()
        self.context_vm = ContextViewModel()
        self.processing_vm = ProcessingViewModel()
        self.output_vm = OutputViewModel()
