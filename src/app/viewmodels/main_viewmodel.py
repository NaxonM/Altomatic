
from PySide6.QtCore import QThreadPool
from .base_viewmodel import BaseViewModel
from .input_viewmodel import InputViewModel
from .header_viewmodel import HeaderViewModel
from .footer_viewmodel import FooterViewModel
from .log_viewmodel import LogViewModel
from .workflow_viewmodel import WorkflowViewModel
from .prompts_model_viewmodel import PromptsModelViewModel
from .advanced_viewmodel import AdvancedViewModel
from ..worker import Worker
from ..views.results_view import ResultsView
from .results_viewmodel import ResultsViewModel
from typing import List, Dict, Any

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

        self.thread_pool = QThreadPool()
        self._connect_signals()

    def _connect_signals(self):
        """Connects signals between different ViewModels."""
        self.footer_vm.process_button_clicked.connect(self.start_processing)

        self.input_vm.input_path_changed.connect(
            lambda path: self.header_vm.update_summaries({"summary_output": f"Output: Custom → {path}"})
        )

        self.input_vm.errorOccurred.connect(self.log_vm.add_log)
        self.footer_vm.errorOccurred.connect(self.log_vm.add_log)
        self.log_vm.errorOccurred.connect(self.log_vm.add_log)

    def start_processing(self):
        """Starts the image processing in a background thread."""
        worker = Worker(self)
        worker.signals.finished.connect(self.show_results)
        self.thread_pool.start(worker)

    def show_results(self, results: List[Dict[str, Any]]):
        """Displays the results window."""
        if self.workflow_vm.output_vm.show_results_table and results:
            results_vm = ResultsViewModel(results)
            self.results_view = ResultsView(results_vm)
            self.results_view.show()
