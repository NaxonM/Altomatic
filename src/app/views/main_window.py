
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from ..viewmodels.main_viewmodel import MainViewModel
from .input_view import InputView
from .header_view import HeaderView
from .main_notebook_view import MainNotebookView
from .log_view import LogView
from .footer_view import FooterView

class MainWindow(QMainWindow):
    """
    The main window shell for the PySide6 application.
    """
    def __init__(self, view_model: MainViewModel):
        super().__init__()
        self.vm = view_model
        self.setWindowTitle("Altomatic")
        self.setGeometry(100, 100, 900, 720)

        # Create a central widget and a main horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_hbox = QHBoxLayout(central_widget)

        # --- Left Panel ---
        left_panel = QWidget()
        left_vbox = QVBoxLayout(left_panel)
        main_hbox.addWidget(left_panel, 1)

        # --- Right Panel ---
        right_panel = QWidget()
        right_vbox = QVBoxLayout(right_panel)
        main_hbox.addWidget(right_panel)

        # --- Components for the Left Panel ---
        self.input_view = InputView(self.vm.input_vm)
        left_vbox.addWidget(self.input_view)

        self.header_view = HeaderView(self.vm.header_vm)
        left_vbox.addWidget(self.header_view)

        self.main_notebook = MainNotebookView(
            self.vm.workflow_vm,
            self.vm.prompts_model_vm,
            self.vm.advanced_vm
        )
        left_vbox.addWidget(self.main_notebook, 1)

        self.footer_view = FooterView(self.vm.footer_vm)
        left_vbox.addWidget(self.footer_view)

        # --- Components for the Right Panel ---
        self.log_view = LogView(self.vm.log_vm)
        right_vbox.addWidget(self.log_view)

        # Apply the stylesheet
        with open('src/app/resources/styles/generated.qss', 'r') as f:
            self.setStyleSheet(f.read())
