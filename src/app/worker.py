
from PySide6.QtCore import QRunnable, Slot, QObject, Signal
from src.core.core.processor import process_images
from .viewmodels.main_viewmodel import MainViewModel
from typing import List, Dict, Any

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    finished = Signal(list)

class Worker(QRunnable):
    """
    A worker thread for running the image processing task.
    """
    def __init__(self, main_vm: MainViewModel):
        super().__init__()
        self.main_vm = main_vm
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        """
        Runs the image processing task and emits the results.
        """
        results = process_images(self.main_vm)
        self.signals.finished.emit(results)
