
from .base_viewmodel import BaseViewModel

class AboutViewModel(BaseViewModel):
    """
    ViewModel for the About window.
    """
    def __init__(self):
        super().__init__()
        self.app_name = "Altomatic"
        self.github_url = "https://github.com/MehdiDevX"
        self.description = (
            "Altomatic helps you batch-generate file names and alt text for images using multimodal LLMs.\\n"
            "Choose your provider, drop images, and let the app handle OCR, compression, and AI prompts."
        )
