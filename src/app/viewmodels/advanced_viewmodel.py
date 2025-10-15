
from .base_viewmodel import BaseViewModel
from .appearance_viewmodel import AppearanceViewModel
from .automation_viewmodel import AutomationViewModel
from .network_viewmodel import NetworkViewModel
from .maintenance_viewmodel import MaintenanceViewModel

class AdvancedViewModel(BaseViewModel):
    """
    ViewModel for the Advanced tab.
    """
    def __init__(self):
        super().__init__()
        self.appearance_vm = AppearanceViewModel()
        self.automation_vm = AutomationViewModel()
        self.network_vm = NetworkViewModel()
        self.maintenance_vm = MaintenanceViewModel()
