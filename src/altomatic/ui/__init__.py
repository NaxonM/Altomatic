"""UI package for Altomatic."""

from .components import build_ui, append_monitor_colored, cleanup_temp_drop_folder, update_token_label
from .dragdrop import configure_drag_and_drop
from .themes import apply_theme

__all__ = [
    "build_ui",
    "append_monitor_colored",
    "configure_drag_and_drop",
    "apply_theme",
    "update_token_label",
    "cleanup_temp_drop_folder",
]
