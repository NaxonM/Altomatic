
from PySide6.QtCore import QObject, Signal

class BaseViewModel(QObject):
    """
    A base class for all view models.
    """
    errorOccurred = Signal(str)

    def __init__(self):
        super().__init__()
