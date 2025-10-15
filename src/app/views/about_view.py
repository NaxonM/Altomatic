
import webbrowser
from PySide6.QtWidgets import QVBoxLayout, QLabel, QPushButton
from .base_view import BaseView
from ..viewmodels.about_viewmodel import AboutViewModel

class AboutView(BaseView):
    """
    The 'About' window view.
    """
    def __init__(self, view_model: AboutViewModel):
        super().__init__(view_model)
        self.setWindowTitle("About Altomatic")
        self.setFixedSize(520, 320)
        self._setup_ui()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)

        title = QLabel(self.view_model.app_name)
        title.setObjectName("TitleLabel")

        description = QLabel(self.view_model.description)
        description.setWordWrap(True)

        github_button = QPushButton("Visit GitHub Repository")
        github_button.clicked.connect(self._open_github)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
        layout.addWidget(github_button)

    def _open_github(self):
        """Opens the GitHub repository URL in a web browser."""
        webbrowser.open(self.view_model.github_url)
