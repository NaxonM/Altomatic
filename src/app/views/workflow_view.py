
from PySide6.QtWidgets import QTabWidget
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
        layout = QTabWidget(self)

        # Create the sub-tab views
        context_view = ContextView(self.view_model.context_vm)
        processing_view = ProcessingView(self.view_model.processing_vm)
        output_view = OutputView(self.view_model.output_vm)

        layout.addTab(context_view, "Context")
        layout.addTab(processing_view, "Processing Options")
        layout.addTab(output_view, "Output")

        # Add the tab widget to the main layout of the view
        import PySide6
        self.setLayout(PySide6.QtWidgets.QVBoxLayout())
        self.layout().addWidget(layout)
