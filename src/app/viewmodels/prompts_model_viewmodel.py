
from .base_viewmodel import BaseViewModel
from .provider_viewmodel import ProviderViewModel
from .prompts_viewmodel import PromptsViewModel

class PromptsModelViewModel(BaseViewModel):
    """
    ViewModel for the Prompts & Model tab.
    """
    def __init__(self):
        super().__init__()
        self.provider_vm = ProviderViewModel()
        self.prompts_vm = PromptsViewModel()
