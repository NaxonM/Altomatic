"""Main application window with improved structure and organization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QPointF, QTimer, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QGraphicsOpacityEffect,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..theming import apply_theme
from ..viewmodels.main_viewmodel import MainViewModel
from .command_palette import Command, CommandPalette
from .footer_view import FooterView
from .input_view import InputView
from .log_view import LogView
from .quick_settings_view import DescribeView, OutputSettingsView
from .review_view import ReviewView
from .settings_panel import SettingsPanel


# ============================================================================
# Step Navigation Components
# ============================================================================

@dataclass
class StepDefinition:
    """Definition of a workflow step."""
    title: str
    caption: str
    
    def format_label(self, number: int) -> str:
        """Format the step label with number."""
        return f"{number:02}  {self.title}\n{self.caption}"


class StepperColumn(QWidget):
    """Vertical stepper navigation component."""
    
    step_selected = Signal(int)

    def __init__(
        self, 
        steps: List[StepDefinition], 
        interactive_count: int = 3, 
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StepperColumn")
        
        self._buttons: List[QPushButton] = []
        self._statuses: List[str] = ["pending"] * len(steps)
        self._active_index = 0
        self._interactive_limit = max(0, interactive_count - 1)
        self._summary_widget: Optional[QWidget] = None
        self._summary_spacing_item: Optional[QSpacerItem] = None

        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(8)
        self._layout.setContentsMargins(8, 12, 8, 12)

        self._create_step_buttons(steps)
        self._stretch_item = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self._layout.addItem(self._stretch_item)
        self._apply_states()

    def _create_step_buttons(self, steps: List[StepDefinition]) -> None:
        """Create buttons for each step."""
        for index, step in enumerate(steps):
            button = QPushButton(step.format_label(index + 1))
            button.setObjectName("StepperButton")
            button.setFlat(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(52)
            button.setProperty("state", "pending")
            button.clicked.connect(lambda _, i=index: self.step_selected.emit(i))
            
            self._layout.addWidget(button)
            self._buttons.append(button)

    def set_statuses(self, statuses: List[str]) -> None:
        """Update the status of each step (active, done, pending)."""
        padded = statuses + ["pending"] * (len(self._buttons) - len(statuses))
        self._statuses = padded[: len(self._buttons)]
        self._apply_states()

    def set_active(self, index: int) -> None:
        """Set the currently active step."""
        self._active_index = max(0, min(index, len(self._buttons) - 1))
        self._apply_states()

    def set_interactive_limit(self, limit: int) -> None:
        """Set the maximum step index that can be interacted with."""
        self._interactive_limit = max(0, min(limit, len(self._buttons) - 1))
        self._apply_states()

    def _apply_states(self) -> None:
        """Apply visual states to all buttons."""
        for i, button in enumerate(self._buttons):
            state = "active" if i == self._active_index else self._statuses[i]
            button.setProperty("state", state)
            button.setEnabled(i <= self._interactive_limit)
            
            # Force style update
            button.style().unpolish(button)
            button.style().polish(button)

    def set_summary_widget(self, widget: QWidget) -> None:
        """Add or replace the summary widget at the bottom."""
        if self._summary_widget is widget:
            return
            
        # Remove existing summary
        if self._summary_widget is not None:
            self._layout.removeWidget(self._summary_widget)
            self._summary_widget.deleteLater()
            self._summary_widget = None

        if self._summary_spacing_item is not None:
            self._layout.removeItem(self._summary_spacing_item)

        if hasattr(self, "_stretch_item") and self._stretch_item is not None:
            self._layout.removeItem(self._stretch_item)

        # Add spacing before summary
        if self._summary_spacing_item is None:
            self._summary_spacing_item = QSpacerItem(
                0, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
            )
        
        self._layout.addItem(self._summary_spacing_item)
        widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._layout.addWidget(widget)
        
        if hasattr(self, "_stretch_item") and self._stretch_item is not None:
            self._layout.addItem(self._stretch_item)
            
        self._summary_widget = widget


class SessionOverviewWidget(QFrame):
    """Session overview card within the stepper."""

    def __init__(self, header_vm, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._header_vm = header_vm


class WorkflowCanvas(QFrame):
    """Main canvas for displaying workflow pages with navigation."""
    
    page_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkflowCanvas")
        self._current_index = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 14, 16, 14)

        # Page stack
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.stack, 1)

        # Navigation controls
        self._create_navigation_controls(layout)

    def _create_navigation_controls(self, layout: QVBoxLayout) -> None:
        """Create prev/next navigation buttons."""
        controls = QHBoxLayout()
        controls.setContentsMargins(0, 8, 0, 0)
        controls.setSpacing(10)
        controls.addStretch()

        self.prev_button = QPushButton("Previous")
        self.prev_button.setProperty("text-role", "ghost")
        self.prev_button.clicked.connect(self._go_prev)
        self.prev_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        controls.addWidget(self.prev_button)

        self.next_button = QPushButton("Next")
        self.next_button.setProperty("text-role", "primary")
        self.next_button.clicked.connect(self._go_next)
        self.next_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        controls.addWidget(self.next_button)

        layout.addLayout(controls)

    def add_page(self, title: str, widget: QWidget) -> int:
        """Add a new page to the workflow."""
        index = self.stack.addWidget(widget)
        if index == 0:
            self.set_current_index(0)
        else:
            self._update_controls()
        return index

    def set_current_index(self, index: int) -> None:
        """Navigate to a specific page."""
        if index < 0 or index >= self.stack.count():
            return
            
        self._current_index = index
        self.stack.setCurrentIndex(index)
        self._update_controls()
        self.page_changed.emit(index)

    def current_index(self) -> int:
        """Get the current page index."""
        return self._current_index

    def _update_controls(self) -> None:
        """Update visibility of navigation buttons."""
        has_prev = self._current_index > 0
        has_next = self._current_index < self.stack.count() - 1

        self.prev_button.setVisible(has_prev)
        self.prev_button.setEnabled(has_prev)
        self.next_button.setVisible(has_next)
        self.next_button.setEnabled(has_next)

    def _go_prev(self) -> None:
        """Navigate to previous page."""
        self.set_current_index(self._current_index - 1)

    def _go_next(self) -> None:
        """Navigate to next page."""
        self.set_current_index(self._current_index + 1)


# ============================================================================
# Main Window
# ============================================================================

class MainWindow(QMainWindow):
    """
    Main application window with workflow-based UI.
    
    Features:
    - Step-based navigation
    - Command palette
    - Theme switching
    - Activity log
    - Notifications
    """

    # Constants
    DEFAULT_SIZE = (880, 540)
    MIN_SIZE = (760, 500)
    STEPPER_MIN_WIDTH = 170
    STEPPER_MAX_WIDTH = 240
    NOTIFICATION_MARGIN = 20
    NOTIFICATION_MIN_WIDTH = 320

    def __init__(self, view_model: MainViewModel):
        super().__init__()
        self.vm = view_model
        
        # State
        self._review_ready = False
        self._latest_results: List[Dict[str, Any]] = []

        # Setup UI
        self._setup_window()
        self._setup_ui()
        self._setup_shortcuts()
        self._setup_connections()
        
        # Initialize
        self._apply_theme(self.vm.advanced_vm.appearance_vm.ui_theme)
        self._update_status_text("Ready")
        self._refresh_stepper()

    # ------------------------------------------------------------------------
    # Window Setup
    # ------------------------------------------------------------------------

    def _setup_window(self) -> None:
        """Configure main window properties."""
        self.setWindowTitle("Altomatic")
        self.resize(*self.DEFAULT_SIZE)
        self.setMinimumSize(*self.MIN_SIZE)

    def _setup_ui(self) -> None:
        """Create and layout all UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # App bar
        self.app_bar = self._create_app_bar()
        main_layout.addWidget(self.app_bar)

        # Body with stepper and canvas
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 2, 0, 0)
        body_layout.setSpacing(14)
        main_layout.addLayout(body_layout, 1)

        self._create_stepper(body_layout)
        self._create_workflow_canvas(body_layout)

        # Footer
        self.footer_view = FooterView(self.vm.footer_vm, self.vm.header_vm)
        main_layout.addWidget(self.footer_view)

        # Additional components
        self._create_log_dock()
        self._create_notification_banner()
        self._create_command_palette()

    def _create_app_bar(self) -> QFrame:
        """Create the top application bar."""
        bar = QFrame(self)
        bar.setObjectName("AppBar")
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # Brand
        brand = QLabel("Altomatic")
        brand.setProperty("state", "title")
        layout.addWidget(brand)
        layout.addStretch()

        # Actions
        self._create_app_bar_actions(layout)

        return bar

    def _create_app_bar_actions(self, layout: QHBoxLayout) -> None:
        """Create action buttons for the app bar."""
        actions = [
            ("Command Palette", self._open_command_palette),
            ("Toggle Theme", self._toggle_theme),
            ("Settings", self._open_advanced_settings),
            ("Log", self._toggle_log),
        ]

        for text, callback in actions:
            button = QPushButton(text)
            button.setProperty("text-role", "ghost")
            button.clicked.connect(callback)
            button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            layout.addWidget(button)

    def _create_stepper(self, layout: QHBoxLayout) -> None:
        """Create the step navigation column."""
        steps = [
            StepDefinition("Sources", "Add files and folders"),
            StepDefinition("Describe", "Select provider and prompt"),
            StepDefinition("Output", "Choose destination"),
            StepDefinition("Review", "Inspect results"),
        ]
        
        self.stepper = StepperColumn(steps, interactive_count=3, parent=self)
        self.stepper.setMinimumWidth(self.STEPPER_MIN_WIDTH)
        self.stepper.setMaximumWidth(self.STEPPER_MAX_WIDTH)
        self.stepper.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.stepper.step_selected.connect(self._navigate_to_step)
        layout.addWidget(self.stepper)

        # Add summary card
        self._create_stepper_summary()

    def _create_stepper_summary(self) -> None:
        """Create the summary card for the stepper."""
        self.session_overview = SessionOverviewWidget(self.vm.header_vm, self)
        self.stepper.set_summary_widget(self.session_overview)

    def _create_workflow_canvas(self, layout: QHBoxLayout) -> None:
        """Create the main workflow canvas with pages."""
        self.workflow_canvas = WorkflowCanvas(self)
        layout.addWidget(self.workflow_canvas, 1)

        # Create and add pages
        self.input_view = InputView(self.vm.input_vm)
        self.describe_view = DescribeView(
            self.vm.prompts_model_vm, self.vm.workflow_vm
        )
        self.output_view = OutputSettingsView(self.vm.workflow_vm)
        self.review_view = ReviewView()

        self.workflow_canvas.add_page("Sources", self.input_view)
        self.workflow_canvas.add_page("Describe", self.describe_view)
        self.workflow_canvas.add_page("Output", self.output_view)
        self.workflow_canvas.add_page("Review", self.review_view)
        
        self.workflow_canvas.page_changed.connect(self._on_canvas_page_changed)
        self.workflow_canvas.set_current_index(0)

    def _create_log_dock(self) -> None:
        """Create the activity log dock widget."""
        self.log_view = LogView(self.vm.log_vm)
        self.log_view.dock_requested.connect(self._dock_log)

        self.log_dock = QDockWidget("Activity Log", self)
        self.log_dock.setObjectName("ActivityLogDock")
        self.log_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.log_dock.setWidget(self.log_view)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.log_dock)
        self.log_dock.hide()

    def _create_notification_banner(self) -> None:
        """Create the notification banner overlay."""
        self.notification_label = QLabel("", self)
        self.notification_label.setObjectName("NotificationBanner")
        self.notification_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.notification_label.hide()

    def _create_command_palette(self) -> None:
        """Create and configure the command palette."""
        self.command_palette = CommandPalette(self)
        self._register_commands()

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        QShortcut(
            QKeySequence("Ctrl+K"), 
            self, 
            activated=self._open_command_palette
        )

    # ------------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------------

    def _setup_connections(self) -> None:
        """Connect all signals and slots."""
        self._connect_appearance_signals()
        self._connect_processing_signals()
        self._connect_input_signals()
        self._connect_provider_signals()
        self._connect_prompts_signals()
        self._connect_output_signals()

    def _connect_appearance_signals(self) -> None:
        """Connect appearance-related signals."""
        appearance_vm = self.vm.advanced_vm.appearance_vm
        appearance_vm.ui_theme_changed.connect(self._apply_theme)
        appearance_vm.ui_theme_changed.connect(self._on_settings_changed)

    def _connect_processing_signals(self) -> None:
        """Connect processing workflow signals."""
        self.vm.processingStarted.connect(self._on_processing_started)
        self.vm.processingFinished.connect(self._on_processing_finished)
        self.vm.resultsReady.connect(self._on_results_ready)

    def _connect_input_signals(self) -> None:
        """Connect input view signals."""
        self.vm.input_vm.sources_changed.connect(self._on_sources_changed)
        self.vm.input_vm.include_subdirectories_changed.connect(
            lambda _: self._on_settings_changed()
        )

    def _connect_provider_signals(self) -> None:
        """Connect provider configuration signals."""
        provider_vm = self.vm.prompts_model_vm.provider_vm
        provider_vm.llm_provider_changed.connect(self._on_settings_changed)
        provider_vm.model_changed.connect(self._on_settings_changed)
        provider_vm.openai_api_key_changed.connect(self._on_settings_changed)
        provider_vm.openrouter_api_key_changed.connect(self._on_settings_changed)

    def _connect_prompts_signals(self) -> None:
        """Connect prompts configuration signals."""
        prompts_vm = self.vm.prompts_model_vm.prompts_vm
        prompts_vm.selected_prompt_changed.connect(
            lambda _: self._on_settings_changed()
        )

    def _connect_output_signals(self) -> None:
        """Connect output configuration signals."""
        output_vm = self.vm.workflow_vm.output_vm
        output_vm.output_folder_option_changed.connect(
            lambda _: self._on_settings_changed()
        )
        output_vm.custom_output_path_changed.connect(
            lambda _: self._on_settings_changed()
        )
        output_vm.show_results_table_changed.connect(
            lambda _: self._on_settings_changed()
        )

    # ------------------------------------------------------------------------
    # Command Palette
    # ------------------------------------------------------------------------

    def _register_commands(self) -> None:
        """Register available commands for the command palette."""
        commands = [
            Command(
                "Add sources",
                "Choose files or folders to analyze",
                self.input_view.trigger_add_sources,
            ),
            Command(
                "Run workflow",
                "Process the current sources",
                self.vm.footer_vm.process_images,
            ),
            Command(
                "Show results",
                "Jump to the review step",
                lambda: self.workflow_canvas.set_current_index(3),
            ),
            Command(
                "Open advanced settings",
                "Fine-tune providers, networking, and more",
                self._open_advanced_settings,
            ),
            Command(
                "Toggle theme",
                "Switch between Aurora light and dark",
                self._toggle_theme,
            ),
            Command(
                "Toggle log",
                "Show or hide the activity log",
                self._toggle_log,
            ),
            Command(
                "Clear sources",
                "Remove all selected files and folders",
                self.input_view.trigger_clear_sources,
            ),
        ]
        
        self.command_palette.set_commands(commands)

    def _open_command_palette(self) -> None:
        """Open the command palette centered on the window."""
        center_x = self.x() + (self.width() - self.command_palette.width()) // 2
        center_y = self.y() + (self.height() - self.command_palette.height()) // 2
        self.command_palette.move(max(center_x, 0), max(center_y, 0))
        self.command_palette.open_palette()

    # ------------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------------

    def _open_advanced_settings(self) -> None:
        """Open the advanced settings dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Advanced Settings")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        panel = SettingsPanel(
            self.vm.workflow_vm,
            self.vm.prompts_model_vm,
            self.vm.advanced_vm,
        )
        layout.addWidget(panel)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.resize(860, 560)
        dialog.exec()

    def _toggle_log(self) -> None:
        """Toggle visibility of the activity log."""
        if self.log_dock.isVisible():
            self.log_dock.hide()
        else:
            self.log_dock.show()
            self.log_dock.raise_()

    def _dock_log(self) -> None:
        """Ensure the log dock is re-attached to the main window."""
        if self.log_dock.isFloating():
            self.log_dock.setFloating(False)
        if not self.log_dock.isVisible():
            self.log_dock.show()
        self.log_dock.raise_()

    def _toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        appearance_vm = self.vm.advanced_vm.appearance_vm
        current_theme = appearance_vm.ui_theme
        new_theme = "Aurora Dark" if current_theme != "Aurora Dark" else "Aurora Light"
        appearance_vm.ui_theme = new_theme
        self._on_settings_changed()

    def _apply_theme(self, theme_name: str) -> None:
        """Apply the specified theme to the application."""
        app = QApplication.instance()
        apply_theme(app, theme_name)

    # ------------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------------

    def _navigate_to_step(self, index: int) -> None:
        """Navigate to a specific workflow step."""
        max_index = self.workflow_canvas.stack.count() - 1
        target = min(index, max(0, max_index))
        self.workflow_canvas.set_current_index(target)

    def _on_canvas_page_changed(self, index: int) -> None:
        """Handle page change in the workflow canvas."""
        self.stepper.set_active(index)

    # ------------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------------

    def show_notification(
        self, 
        message: str, 
        state: str = "info", 
        duration_ms: int = 3500
    ) -> None:
        """
        Display a temporary notification banner.
        
        Args:
            message: Notification text
            state: Visual state (info, success, warning, danger)
            duration_ms: How long to display the notification
        """
        self.notification_label.setText(message)
        self.notification_label.setProperty("state", state)
        self.notification_label.show()
        self._position_notification()
        
        # Force style update
        self.notification_label.style().unpolish(self.notification_label)
        self.notification_label.style().polish(self.notification_label)
        
        QTimer.singleShot(duration_ms, self.notification_label.hide)

    def _position_notification(self) -> None:
        """Position the notification banner at the bottom of the window."""
        label = self.notification_label
        label.adjustSize()
        
        width = max(
            self.NOTIFICATION_MIN_WIDTH,
            self.width() - self.NOTIFICATION_MARGIN * 2
        )
        label.resize(width, label.height())
        
        x = self.NOTIFICATION_MARGIN
        y = self.height() - label.height() - self.NOTIFICATION_MARGIN
        label.move(x, y)

    # ------------------------------------------------------------------------
    # Workflow State Management
    # ------------------------------------------------------------------------

    def _refresh_stepper(self) -> None:
        """Update stepper states based on current workflow progress."""
        # Check readiness of each step
        sources_ready = self._is_sources_ready()
        describe_ready = self._is_describe_ready(sources_ready)
        output_ready = self._is_output_ready(sources_ready)
        review_ready = self._review_ready

        # Compute statuses
        statuses = self._compute_step_statuses([
            sources_ready,
            describe_ready,
            output_ready,
            review_ready,
        ])

        # Update stepper UI
        self.stepper.set_statuses(statuses)
        
        # Set interactive limit
        max_enabled = self._compute_max_enabled_step(
            sources_ready, describe_ready, output_ready, review_ready
        )
        self.stepper.set_interactive_limit(max_enabled)
        self.stepper.set_active(self.workflow_canvas.current_index())

    def _is_sources_ready(self) -> bool:
        """Check if sources are configured."""
        return bool(self.vm.input_vm.sources())

    def _is_describe_ready(self, sources_ready: bool) -> bool:
        """Check if describe step is configured."""
        if not sources_ready:
            return False
            
        provider_vm = self.vm.prompts_model_vm.provider_vm
        prompts_vm = self.vm.prompts_model_vm.prompts_vm
        
        return (
            bool(provider_vm.llm_provider)
            and bool(provider_vm.model)
            and bool(prompts_vm.selected_prompt)
        )

    def _is_output_ready(self, sources_ready: bool) -> bool:
        """Check if output is configured."""
        if not sources_ready:
            return False
            
        output_vm = self.vm.workflow_vm.output_vm
        
        if output_vm.output_folder_option == "Custom":
            return bool(output_vm.custom_output_path)
        
        return True

    def _compute_step_statuses(self, readiness: List[bool]) -> List[str]:
        """
        Compute status strings for each step.
        
        Args:
            readiness: List of boolean flags indicating step completion
            
        Returns:
            List of status strings ('done', 'active', 'pending')
        """
        statuses: List[str] = []
        first_pending_found = False
        
        for ready in readiness:
            if ready:
                statuses.append("done")
            else:
                if not first_pending_found:
                    statuses.append("active")
                    first_pending_found = True
                else:
                    statuses.append("pending")
        
        # Ensure we have exactly 4 statuses
        while len(statuses) < 4:
            statuses.append("pending")
            
        return statuses[:4]

    def _compute_max_enabled_step(
        self,
        sources_ready: bool,
        describe_ready: bool,
        output_ready: bool,
        review_ready: bool,
    ) -> int:
        """Compute the maximum step index that should be enabled."""
        max_enabled = 0
        
        if sources_ready:
            max_enabled = 1
        if describe_ready:
            max_enabled = max(max_enabled, 2)
        if review_ready:
            max_enabled = 3
            
        max_index = self.workflow_canvas.stack.count() - 1
        return min(max_enabled, max_index)

    # ------------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------------

    def _on_processing_started(self) -> None:
        """Handle workflow processing start."""
        self._review_ready = False
        self.footer_view.process_button.setEnabled(False)
        self._update_status_text("Processing…")
        self._refresh_stepper()
        self.show_notification("Processing images…", "warning", duration_ms=2000)

    def _on_processing_finished(self, success: bool) -> None:
        """Handle workflow processing completion."""
        self.footer_view.process_button.setEnabled(True)
        self._review_ready = success
        self._refresh_stepper()
        
        if success:
            self._update_status_text("Completed – review results")
            self.show_notification(
                "Processing complete. View results to review output.",
                "success"
            )
            self.workflow_canvas.set_current_index(3)
        else:
            self._update_status_text("Processing interrupted")
            self.show_notification(
                "Processing did not produce results. Check the log for details.",
                "danger"
            )
        
        self._persist_settings()

    def _on_results_ready(self, results: List[Dict[str, Any]]) -> None:
        """Handle new results being available."""
        self._latest_results = list(results)
        show_table = self.vm.workflow_vm.output_vm.show_results_table
        self.review_view.set_results(self._latest_results, show_table)
        self._review_ready = bool(self._latest_results)
        self._refresh_stepper()

    def _on_sources_changed(self, _sources: Any) -> None:
        """Handle source files/folders being changed."""
        self._refresh_stepper()
        self._on_settings_changed()

    def _on_settings_changed(self, *_args: Any) -> None:
        """Handle any settings change."""
        self._refresh_stepper()
        self._persist_settings()

    def _update_status_text(self, text: str) -> None:
        """Update the footer status text."""
        self.vm.footer_vm.status_text = text

    def _persist_settings(self) -> None:
        """Save current settings and window geometry."""
        geometry = f"{self.width()}x{self.height()}"
        self.vm.save_settings(geometry)

    # ------------------------------------------------------------------------
    # Qt Event Overrides
    # ------------------------------------------------------------------------

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Handle window resize events."""
        super().resizeEvent(event)
        if hasattr(self, "notification_label") and self.notification_label.isVisible():
            self._position_notification()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Handle window close events."""
        self._persist_settings()
        super().closeEvent(event)