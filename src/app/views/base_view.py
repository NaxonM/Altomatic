
from PySide6.QtWidgets import QWidget
from ..viewmodels.base_viewmodel import BaseViewModel

class BaseView(QWidget):
    """
    A base class for all views.
    """
    def __init__(self, view_model: BaseViewModel):
        super().__init__()
        self._view_model = view_model

    @property
    def view_model(self):
        return self._view_model
