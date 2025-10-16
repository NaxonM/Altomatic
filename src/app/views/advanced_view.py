
from PySide6.QtWidgets import QTabWidget, QVBoxLayout
from .base_view import BaseView
from ..viewmodels.advanced_viewmodel import AdvancedViewModel
from .appearance_view import AppearanceView
from .automation_view import AutomationView
from .network_view import NetworkView
from .maintenance_view import MaintenanceView

class AdvancedView(BaseView):
    """
    The Advanced view, containing sub-tabs for various settings.
    """
    def __init__(self, view_model: AdvancedViewModel):
        super().__init__(view_model)
        self._setup_ui()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)
        notebook = QTabWidget(self)
        notebook.setObjectName("AdvancedTabs")

        # Create the sub-tab views
        appearance_view = AppearanceView(self.view_model.appearance_vm)
        automation_view = AutomationView(self.view_model.automation_vm)
        network_view = NetworkView(self.view_model.network_vm)
        maintenance_view = MaintenanceView(self.view_model.maintenance_vm)

        notebook.addTab(appearance_view, "Appearance")
        notebook.addTab(automation_view, "Automation")
        notebook.addTab(network_view, "Network")
        notebook.addTab(maintenance_view, "Maintenance")

        layout.addWidget(notebook)
