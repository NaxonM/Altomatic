
from PySide6.QtCore import Signal, Property, str, bool
from .base_viewmodel import BaseViewModel

class OutputViewModel(BaseViewModel):
    """
    ViewModel for the Output sub-tab.
    """
    output_folder_option_changed = Signal(str)
    custom_output_path_changed = Signal(str)
    show_results_table_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self._output_folder_option = "Same as input"
        self._custom_output_path = ""
        self._show_results_table = True

    # --- Properties ---
    @Property(str, notify=output_folder_option_changed)
    def output_folder_option(self):
        return self._output_folder_option

    @output_folder_option.setter
    def output_folder_option(self, value):
        if self._output_folder_option != value:
            self._output_folder_option = value
            self.output_folder_option_changed.emit(value)

    @Property(str, notify=custom_output_path_changed)
    def custom_output_path(self):
        return self._custom_output_path

    @custom_output_path.setter
    def custom_output_path(self, value):
        if self._custom_output_path != value:
            self._custom_output_path = value
            self.custom_output_path_changed.emit(value)

    @Property(bool, notify=show_results_table_changed)
    def show_results_table(self):
        return self._show_results_table

    @show_results_table.setter
    def show_results_table(self, value):
        if self._show_results_table != value:
            self._show_results_table = value
            self.show_results_table_changed.emit(value)
