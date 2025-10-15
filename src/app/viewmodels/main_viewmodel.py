
from .base_viewmodel import BaseViewModel
from .input_viewmodel import InputViewModel
from .header_viewmodel import HeaderViewModel
from .footer_viewmodel import FooterViewModel
from .log_viewmodel import LogViewModel
from .workflow_viewmodel import WorkflowViewModel
from .prompts_model_viewmodel import PromptsModelViewModel
from .advanced_viewmodel import AdvancedViewModel

class MainViewModel(BaseViewModel):
    """
    The main ViewModel, orchestrating all other ViewModels.
    """
    def __init__(self):
        super().__init__()
        self.input_vm = InputViewModel()
        self.header_vm = HeaderViewModel()
        self.footer_vm = FooterViewModel()
        self.log_vm = LogViewModel()

        # ViewModels for the notebook tabs
        self.workflow_vm = WorkflowViewModel()
        self.prompts_model_vm = PromptsModelViewModel()
        self.advanced_vm = AdvancedViewModel()

        self._connect_signals()

    def _connect_signals(self):
        """Connects signals between different ViewModels."""
        # Example: When the footer's process button is clicked, log a message
        self.footer_vm.process_button_clicked.connect(
            lambda: self.log_vm.add_log("Image processing started...")
        )

        # Example: When the input path changes, update the header
        self.input_vm.input_path_changed.connect(
            lambda path: self.header_vm.update_summaries({"summary_output": f"Output: Custom → {path}"})
        )

        # Example of error handling
        self.input_vm.errorOccurred.connect(self.log_vm.add_log)
        self.footer_vm.errorOccurred.connect(self.log_vm.add_log)
        self.log_vm.errorOccurred.connect(self.log_vm.add_log)
