
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from .footer_view import FooterView
from ..viewmodels.footer_viewmodel import FooterViewModel
from .input_view import InputView
from ..viewmodels.input_viewmodel import InputViewModel
from .header_view import HeaderView
from ..viewmodels.header_viewmodel import HeaderViewModel

class MainWindow(QMainWindow):
    """
    The main window shell for the PySide6 application.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Altomatic")
        self.setGeometry(100, 100, 600, 720)

        # Create a central widget and a layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # --- Input View ---
        self.input_vm = InputViewModel()
        self.input_view = InputView(self.input_vm)
        self.main_layout.addWidget(self.input_view)

        # --- Header View ---
        self.header_vm = HeaderViewModel()
        self.header_view = HeaderView(self.header_vm)
        self.main_layout.addWidget(self.header_view)

        # --- Main Content Area (Placeholder) ---
        main_content = QWidget()
        self.main_layout.addWidget(main_content, 1) # Add with stretch factor

        # --- Footer ---
        self.footer_vm = FooterViewModel()
        self.footer_view = FooterView(self.footer_vm)
        self.main_layout.addWidget(self.footer_view)

        # Apply the stylesheet
        with open('src/app/resources/styles/generated.qss', 'r') as f:
            self.setStyleSheet(f.read())
