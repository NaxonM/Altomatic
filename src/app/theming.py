"""
Theme management for the application.

This module loads QSS stylesheets from the resources/themes directory
and applies them to the application.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication


# ======================================================================================
# Theme Definitions
# ======================================================================================

THEMES: Dict[str, str] = {
    "Aurora Light": "aurora-light.qss",
    "Aurora Dark": "aurora-dark.qss",
    "Nord": "nord.qss",
    "Solarized Light": "solarized-light.qss",
    "Solarized Dark": "solarized-dark.qss",
}

DEFAULT_THEME = "Aurora Light"


# ======================================================================================
# Theme Application
# ======================================================================================

def _theme_path(theme_file: str) -> Path:
    """Returns the path to the QSS theme file."""
    return Path(__file__).resolve().parent / "resources" / "themes" / theme_file


def generate_stylesheet(theme_name: str) -> str:
    """Generates a stylesheet from the given theme name."""
    theme_file = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    path = _theme_path(theme_file)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def apply_theme(app: QApplication, theme_name: str) -> None:
    """Applies the specified theme to the application."""
    stylesheet = generate_stylesheet(theme_name)
    app.setStyleSheet(stylesheet)

    # Set global font
    font = QFont("Inter", 13)
    app.setFont(font)


def add_fonts() -> None:
    """Adds custom fonts to the application's font database."""
    font_path = Path(__file__).resolve().parent / "resources" / "fonts" / "Inter-Regular.ttf"
    if font_path.exists():
        QFontDatabase.addApplicationFont(str(font_path))


def get_theme_names() -> list[str]:
    """Returns a list of available theme names."""
    return list(THEMES.keys())


__all__ = [
    "THEMES",
    "DEFAULT_THEME",
    "generate_stylesheet",
    "apply_theme",
    "add_fonts",
    "get_theme_names",
]