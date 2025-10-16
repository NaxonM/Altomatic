from __future__ import annotations

from PySide6.QtWidgets import QListWidget, QListWidgetItem, QStackedWidget, QHBoxLayout, QWidget

from .workflow_view import WorkflowView
from .prompts_model_view import PromptsModelView
from .advanced_view import AdvancedView
from ..viewmodels.workflow_viewmodel import WorkflowViewModel
from ..viewmodels.prompts_model_viewmodel import PromptsModelViewModel
from ..viewmodels.advanced_viewmodel import AdvancedViewModel


class SettingsPanel(QWidget):
    """Side-nav settings panel consolidating workflow, prompts, and advanced controls."""

    def __init__(
        self,
        workflow_vm: WorkflowViewModel,
        prompts_model_vm: PromptsModelViewModel,
        advanced_vm: AdvancedViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsPanel")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("SettingsNav")
        self.nav_list.setFixedWidth(160)
        self.nav_list.setSpacing(2)
        self.nav_list.setUniformItemSizes(True)

        self.stack = QStackedWidget()

        self._add_page("Workflow", WorkflowView(workflow_vm))
        self._add_page("Prompts & Model", PromptsModelView(prompts_model_vm))
        self._add_page("Advanced", AdvancedView(advanced_vm))

        layout.addWidget(self.nav_list)
        layout.addWidget(self.stack, 1)

        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

    def _add_page(self, label: str, widget: QWidget) -> None:
        item = QListWidgetItem(label)
        self.nav_list.addItem(item)
        self.stack.addWidget(widget)
