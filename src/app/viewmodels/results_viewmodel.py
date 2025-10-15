
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

class ResultsViewModel(BaseViewModel):
    """
    ViewModel for the Results window.
    """
    def __init__(self, results: List[Dict[str, Any]]):
        super().__init__()
        self.table_model = ResultsTableModel(results)
