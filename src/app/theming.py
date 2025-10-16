"""Theme management utilities using external QSS templates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication


@dataclass(frozen=True)
class ThemePalette:
    """Base palette colors for a theme."""

    name: str
    is_dark: bool
    background: str
    background_alt: str
    surface: str
    surface_alt: str
    border: str
    text: str
    text_muted: str


@dataclass(frozen=True)
class Accent:
    """Accent colors applied to interactive elements."""

    name: str
    primary: str
    primary_alt: str
    success: str
    warning: str
    danger: str


THEMES: Dict[str, ThemePalette] = {
    "Aurora Light": ThemePalette(
        name="Aurora Light",
        is_dark=False,
        background="#f4f5f9",
        background_alt="#eceff7",
        surface="#ffffff",
        surface_alt="#f2f4fa",
        border="#d8dbea",
        text="#1c2030",
        text_muted="#757b8d",
    ),
    "Aurora Dark": ThemePalette(
        name="Aurora Dark",
        is_dark=True,
        background="#0f111a",
        background_alt="#161a26",
        surface="#1b2130",
        surface_alt="#232a3d",
        border="#30384c",
        text="#f3f6ff",
        text_muted="#a7adc7",
    ),
}


ACCENTS: Dict[str, Accent] = {
    "Electric Blue": Accent(
        name="Electric Blue",
        primary="#4f67ff",
        primary_alt="#4052d6",
        success="#33d6a6",
        warning="#fbbf24",
        danger="#ff6584",
    ),
    "Neon Violet": Accent(
        name="Neon Violet",
        primary="#8764ff",
        primary_alt="#6f4fe1",
        success="#34d399",
        warning="#f59e0b",
        danger="#f87171",
    ),
    "Sunrise": Accent(
        name="Sunrise",
        primary="#ff7a5c",
        primary_alt="#e06445",
        success="#22c55e",
        warning="#fbbf24",
        danger="#ef4444",
    ),
}


DEFAULT_THEME = "Aurora Light"
DEFAULT_ACCENT = "Electric Blue"


class ColorUtils:
    """Utility helpers for color manipulation."""

    @staticmethod
    def blend(color_a: str, color_b: str, ratio: float) -> str:
        ca = QColor(color_a)
        cb = QColor(color_b)
        r = int(ca.red() + (cb.red() - ca.red()) * ratio)
        g = int(ca.green() + (cb.green() - ca.green()) * ratio)
        b = int(ca.blue() + (cb.blue() - ca.blue()) * ratio)
        return QColor(r, g, b).name()

    @staticmethod
    def with_alpha(color: str, alpha: float) -> str:
        qcolor = QColor(color)
        qcolor.setAlphaF(alpha)
        return qcolor.name(QColor.NameFormat.HexArgb)


def _theme_template_path() -> Path:
    return Path(__file__).resolve().parent / "resources" / "themes" / "aurora.qss"


def _build_color_map(
    palette: ThemePalette,
    accent: Accent,
    *,
    high_contrast: bool = False,
) -> Dict[str, str]:
    utils = ColorUtils
    border = palette.border if not high_contrast else utils.blend(palette.border, palette.text, 0.55)

    return {
        "background": palette.background,
        "background_alt": palette.background_alt,
        "surface": palette.surface,
        "surface_alt": palette.surface_alt,
        "border": border,
        "inset_border": utils.blend(border, palette.background, 0.35),
        "text": palette.text,
        "text_muted": palette.text_muted,
        "primary": accent.primary,
        "primary_alt": accent.primary_alt,
        "primary_text": "#ffffff",
        "primary_hover": utils.blend(accent.primary, accent.primary_alt, 0.45),
        "primary_active": accent.primary_alt,
        "hover_surface": utils.blend(palette.surface_alt, palette.background_alt, 0.4),
        "focus_bg": utils.with_alpha(accent.primary, 0.12 if palette.is_dark else 0.06),
        "selection_bg": utils.with_alpha(accent.primary, 0.18),
        "selection_fg": palette.text if palette.is_dark else "#10121d",
        "disabled_fg": utils.blend(
            palette.text_muted,
            palette.surface if palette.is_dark else palette.background,
            0.55,
        ),
        "disabled_bg": utils.blend(palette.surface, palette.background, 0.25),
        "disabled_primary_bg": utils.blend(accent.primary, border, 0.7),
        "disabled_primary_fg": utils.blend("#ffffff", palette.background, 0.3),
        "divider": utils.blend(border, palette.background_alt, 0.5),
        "placeholder": utils.blend(
            palette.text_muted,
            palette.surface if palette.is_dark else palette.background,
            0.45,
        ),
        "done_color": utils.blend(accent.primary, "#ffffff", 0.35 if not palette.is_dark else 0.5),
        "success": accent.success,
        "warning": accent.warning,
        "danger": accent.danger,
        "status_bg": utils.with_alpha(accent.primary, 0.16 if palette.is_dark else 0.1),
        "status_text": "#f5f7ff" if palette.is_dark else accent.primary,
        "border_soft": utils.blend(border, palette.background, 0.7),
        "border_strong": utils.blend(border, palette.text, 0.2),
        "shadow_light": utils.with_alpha(palette.text, 0.06 if palette.is_dark else 0.08),
        "shadow_medium": utils.with_alpha(palette.text, 0.12 if palette.is_dark else 0.16),
        "shadow_strong": utils.with_alpha(palette.text, 0.2 if palette.is_dark else 0.24),
        "accent_glow": utils.with_alpha(accent.primary, 0.22),
        "accent_glow_strong": utils.with_alpha(accent.primary, 0.32),
        "primary_alpha_06": utils.with_alpha(accent.primary, 0.06),
        "primary_alpha_09": utils.with_alpha(accent.primary, 0.09),
        "primary_alpha_14": utils.with_alpha(accent.primary, 0.14),
        "primary_alpha_22": utils.with_alpha(accent.primary, 0.22),
        "primary_alpha_40": utils.with_alpha(accent.primary, 0.4),
        "primary_alpha_60": utils.with_alpha(accent.primary, 0.6),
        "primary_alpha_80": utils.with_alpha(accent.primary, 0.8),
        "border_alpha_40": utils.with_alpha(border, 0.4),
        "border_alpha_60": utils.with_alpha(border, 0.6),
        "border_alpha_80": utils.with_alpha(border, 0.8),
        "drop_area_border": utils.blend(border, palette.background_alt, 0.55),
        "drop_area_bg": utils.blend(palette.surface_alt, palette.background, 0.55),
        "surface_mix_20": utils.blend(palette.surface, palette.background, 0.2),
    }


def _render_template(template: str, colors: Dict[str, str]) -> str:
    rendered = template
    for key in sorted(colors.keys(), key=len, reverse=True):
        rendered = rendered.replace(f"{{{key}}}", colors[key])
    return rendered


def generate_stylesheet(
    theme_name: str,
    accent_name: str,
    *,
    high_contrast: bool = False,
) -> str:
    palette = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    accent = ACCENTS.get(accent_name, ACCENTS[DEFAULT_ACCENT])
    colors = _build_color_map(palette, accent, high_contrast=high_contrast)
    template = _theme_template_path().read_text(encoding="utf-8")
    return _render_template(template, colors)


def apply_theme(
    app: QApplication | None,
    theme_name: str,
    accent_name: str = DEFAULT_ACCENT,
    *,
    high_contrast: bool = False,
) -> None:
    if app is None:
        return
    stylesheet = generate_stylesheet(theme_name, accent_name, high_contrast=high_contrast)
    app.setStyleSheet(stylesheet)


__all__ = [
    "ThemePalette",
    "Accent",
    "THEMES",
    "ACCENTS",
    "DEFAULT_THEME",
    "DEFAULT_ACCENT",
    "generate_stylesheet",
    "apply_theme",
]
