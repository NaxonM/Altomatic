
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QLineEdit, QPushButton
)
from .base_view import BaseView
from ..viewmodels.network_viewmodel import NetworkViewModel

class NetworkView(BaseView):
    """
    The Network sub-tab view.
    """
    def __init__(self, view_model: NetworkViewModel):
        super().__init__(view_model)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        self.proxy_checkbox = QCheckBox("Use proxy for network requests")
        header_layout.addWidget(self.proxy_checkbox)
        self.refresh_button = QPushButton("Refresh detection")
        header_layout.addWidget(self.refresh_button)
        layout.addLayout(header_layout)

        layout.addWidget(QLabel("Detected system proxy:"))
        self.detected_proxy_label = QLabel()
        layout.addWidget(self.detected_proxy_label)

        layout.addWidget(QLabel("Effective proxy in use:"))
        self.effective_proxy_label = QLabel()
        layout.addWidget(self.effective_proxy_label)

        layout.addWidget(QLabel("Custom override (optional):"))
        self.proxy_override_edit = QLineEdit()
        layout.addWidget(self.proxy_override_edit)

        layout.addStretch()

    def _connect_signals(self):
        """Connects signals and slots."""
        # View to ViewModel
        self.proxy_checkbox.toggled.connect(self.view_model.proxy_enabled)
        self.proxy_override_edit.textChanged.connect(self.view_model.proxy_override)
        self.refresh_button.clicked.connect(self.view_model.refresh_detected_proxy)

        # ViewModel to View
        self.view_model.proxy_enabled_changed.connect(self.proxy_checkbox.setChecked)
        self.view_model.proxy_override_changed.connect(self.proxy_override_edit.setText)
        self.view_model.detected_proxy_changed.connect(self.detected_proxy_label.setText)
        self.view_model.effective_proxy_changed.connect(self.effective_proxy_label.setText)
