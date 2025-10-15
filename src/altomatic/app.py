
"""Application bootstrap for Altomatic."""

import sys
import os
from PySide6.QtWidgets import QApplication

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.app.views.main_window import MainWindow
from src.app.viewmodels.main_viewmodel import MainViewModel

def run() -> None:
    """Initialize the UI, wire dependencies, and start the main loop."""
    app = QApplication(sys.argv)
    main_vm = MainViewModel()
    window = MainWindow(main_vm)
    window.show()
    sys.exit(app.exec())
