
from PySide6.QtCore import Signal, Property, QAbstractTableModel, Qt, QModelIndex
from .base_viewmodel import BaseViewModel
from typing import List, Dict, Any

class ResultsTableModel(QAbstractTableModel):
    def __init__(self, data: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["Original Filename", "New Filename", "Alt Text"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            row = self._data[index.row()]
            if index.column() == 0:
                return row["original_filename"]
            elif index.column() == 1:
                return row["new_filename"]
            elif index.column() == 2:
                return row["alt_text"]
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None

    def update_data(self, data: List[Dict[str, Any]]) -> None:
        self.beginResetModel()
        self._data = data
        self.endResetModel()

class ResultsViewModel(BaseViewModel):
    """
    ViewModel for the Results window.
    """
    def __init__(self, results: List[Dict[str, Any]]):
        super().__init__()
        self._results = results
        self.table_model = ResultsTableModel(results)

    @property
    def results(self) -> List[Dict[str, Any]]:
        return list(self._results)

    def update_results(self, results: List[Dict[str, Any]]) -> None:
        self._results = list(results)
        self.table_model.update_data(self._results)
