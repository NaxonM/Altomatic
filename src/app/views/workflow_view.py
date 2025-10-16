
from PySide6.QtWidgets import QTabWidget, QVBoxLayout
from .base_view import BaseView
from ..viewmodels.workflow_viewmodel import WorkflowViewModel
from .context_view import ContextView
from .processing_view import ProcessingView
from .output_view import OutputView

class WorkflowView(BaseView):
    """
    The workflow view, containing sub-tabs for context, processing, and output.
    """
    def __init__(self, view_model: WorkflowViewModel):
        super().__init__(view_model)
        self._setup_ui()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        tab_widget = QTabWidget(self)

        # Create the sub-tab views
        context_view = ContextView(self.view_model.context_vm)
        processing_view = ProcessingView(self.view_model.processing_vm)
        output_view = OutputView(self.view_model.output_vm)

        tab_widget.addTab(context_view, "Context")
        tab_widget.addTab(processing_view, "Processing Options")
        tab_widget.addTab(output_view, "Output")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(tab_widget)
