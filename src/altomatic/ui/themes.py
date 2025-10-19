"""Modern ttk theme helpers for Altomatic with enhanced color palettes."""

from __future__ import annotations

import ctypes
import os
import tkinter as tk
from tkinter import ttk
if os.name == "nt":
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
    DWMWA_CAPTION_COLOR = 35
    DWMWA_TEXT_COLOR = 36

from tkinterdnd2 import TkinterDnD


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in range(0, 6, 2))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{channel:02x}" for channel in rgb)


def _hex_to_colorref(value: str) -> int:
    r, g, b = _hex_to_rgb(value)
    return (b << 16) | (g << 8) | r


def _blend(color: str, target: str, amount: float) -> str:
    base = _hex_to_rgb(color)
    mix = _hex_to_rgb(target)
    blended = tuple(int(round(base[i] + (mix[i] - base[i]) * amount)) for i in range(3))
    return _rgb_to_hex(blended)


def _is_dark_palette(palette: dict[str, str | bool]) -> bool:
    return palette.get("is_dark", False)


def _set_titlebar_mode(widget: tk.Misc, palette: dict[str, str]) -> None:
    if os.name != "nt":
        return
    try:
        hwnd = widget.winfo_id()
    except Exception:
        return
    dark_mode = bool(_is_dark_palette(palette))
    value = ctypes.c_bool(dark_mode)
    hr = ctypes.windll.dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_USE_IMMERSIVE_DARK_MODE,
        ctypes.byref(value),
        ctypes.sizeof(value),
    )
    if hr != 0:
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
        except Exception:
            pass

    if dark_mode:
        try:
            caption_color = _hex_to_colorref(palette.get("background", "#1f1f1f"))
            text_color = _hex_to_colorref(palette.get("foreground", "#f5f5f5"))
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_CAPTION_COLOR,
                ctypes.byref(ctypes.c_int(caption_color)),
                ctypes.sizeof(ctypes.c_int),
            )
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_TEXT_COLOR,
                ctypes.byref(ctypes.c_int(text_color)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass


def _style_menu_widget(menu: tk.Menu, palette: dict[str, str]) -> None:
    highlight = _blend(palette["surface"], palette["primary"], 0.18)
    menu.configure(
        background=palette["surface"],
        foreground=palette["foreground"],
        activebackground=highlight,
        activeforeground=palette["primary-foreground"],
        borderwidth=0,
        relief="flat",
        tearoff=False,
    )

    end_index = menu.index("end")
    if end_index is None:
        return
    for idx in range(end_index + 1):
        try:
            menu.entryconfigure(
                idx,
                background=palette["surface"],
                foreground=palette["foreground"],
                activebackground=highlight,
                activeforeground=palette["primary-foreground"],
            )
        except tk.TclError:
            continue


def _style_menus(widget: tk.Widget, palette: dict[str, str]) -> None:
    if isinstance(widget, (tk.Tk, tk.Toplevel)):
        _set_titlebar_mode(widget, palette)
        try:
            menu_name = widget.cget("menu")
        except tk.TclError:
            menu_name = None
        if menu_name:
            try:
                menu = widget.nametowidget(menu_name)
                _style_menu_widget(menu, palette)
            except (KeyError, tk.TclError):
                pass

    try:
        menu_name = widget.cget("menu")
    except tk.TclError:
        menu_name = None
    if menu_name:
        try:
            menu_widget = widget.nametowidget(menu_name)
            _style_menu_widget(menu_widget, palette)
        except (KeyError, tk.TclError):
            pass

    for child in widget.winfo_children():
        _style_menus(child, palette)


# Enhanced color palettes with improved contrast and readability
PALETTE = {
    "Arctic Light": {
        "background": "#f5f8fc",
        "foreground": "#0a1628",
        "surface": "#ffffff",
        "surface-2": "#e1e8f0",
        "primary": "#1d4ed8",
        "primary-foreground": "#ffffff",
        "secondary": "#475569",
        "secondary-foreground": "#ffffff",
        "muted": "#64748b",
        "success": "#059669",
        "warning": "#d97706",
        "danger": "#dc2626",
        "info": "#2563eb",
        "is_dark": False,
    },
    "Midnight": {
        "background": "#0f1419",
        "foreground": "#e6edf3",
        "surface": "#1c2128",
        "surface-2": "#2d333b",
        "primary": "#22d3ee",
        "primary-foreground": "#0c1117",
        "secondary": "#58a6ff",
        "secondary-foreground": "#0c1117",
        "muted": "#8b949e",
        "success": "#3fb950",
        "warning": "#f0883e",
        "danger": "#f85149",
        "info": "#58a6ff",
        "is_dark": True,
    },
    "Forest": {
        "background": "#f0f7f0",
        "foreground": "#0d2818",
        "surface": "#ffffff",
        "surface-2": "#d4e8d9",
        "primary": "#0f7a4f",
        "primary-foreground": "#ffffff",
        "secondary": "#3f6f54",
        "secondary-foreground": "#ffffff",
        "muted": "#5a7463",
        "success": "#15803d",
        "warning": "#d97706",
        "danger": "#b91c1c",
        "info": "#0d9488",
        "is_dark": False,
    },
    "Sunset": {
        "background": "#1a0e1f",
        "foreground": "#f5e9e6",
        "surface": "#271833",
        "surface-2": "#3a2447",
        "primary": "#fb923c",
        "primary-foreground": "#1a0a14",
        "secondary": "#ec4899",
        "secondary-foreground": "#fdf2f8",
        "muted": "#c4b5d4",
        "success": "#84cc16",
        "warning": "#fbbf24",
        "danger": "#f43f5e",
        "info": "#d8b4fe",
        "is_dark": True,
    },
    "Lavender": {
        "background": "#faf8ff",
        "foreground": "#2e1065",
        "surface": "#ffffff",
        "surface-2": "#ede9fe",
        "primary": "#7c3aed",
        "primary-foreground": "#ffffff",
        "secondary": "#6d28d9",
        "secondary-foreground": "#ffffff",
        "muted": "#7c3aed",
        "success": "#16a34a",
        "warning": "#d97706",
        "danger": "#dc2626",
        "info": "#8b5cf6",
        "is_dark": False,
    },
    "Charcoal": {
        "background": "#18181b",
        "foreground": "#fafafa",
        "surface": "#27272a",
        "surface-2": "#3f3f46",
        "primary": "#fbbf24",
        "primary-foreground": "#18181b",
        "secondary": "#a1a1aa",
        "secondary-foreground": "#18181b",
        "muted": "#a1a1aa",
        "success": "#4ade80",
        "warning": "#fb923c",
        "danger": "#f87171",
        "info": "#60a5fa",
        "is_dark": True,
    },
    "Ocean Blue": {
        "background": "#f0f7ff",
        "foreground": "#1e3a8a",
        "surface": "#ffffff",
        "surface-2": "#dbeafe",
        "primary": "#2563eb",
        "primary-foreground": "#ffffff",
        "secondary": "#1e40af",
        "secondary-foreground": "#ffffff",
        "muted": "#475569",
        "success": "#059669",
        "warning": "#d97706",
        "danger": "#dc2626",
        "info": "#0ea5e9",
        "is_dark": False,
    },
    "Deep Space": {
        "background": "#0c0a1f",
        "foreground": "#e7e5ff",
        "surface": "#1a1836",
        "surface-2": "#2d2958",
        "primary": "#a78bfa",
        "primary-foreground": "#1c1532",
        "secondary": "#818cf8",
        "secondary-foreground": "#1c1532",
        "muted": "#a5b4fc",
        "success": "#34d399",
        "warning": "#fbbf24",
        "danger": "#f87171",
        "info": "#93c5fd",
        "is_dark": True,
    },
    "Warm Sand": {
        "background": "#faf8f3",
        "foreground": "#3e2723",
        "surface": "#ffffff",
        "surface-2": "#f5ead6",
        "primary": "#ca8a04",
        "primary-foreground": "#ffffff",
        "secondary": "#92400e",
        "secondary-foreground": "#ffffff",
        "muted": "#78716c",
        "success": "#16a34a",
        "warning": "#ea580c",
        "danger": "#dc2626",
        "info": "#0891b2",
        "is_dark": False,
    },
    "Cherry Blossom": {
        "background": "#fdf4f8",
        "foreground": "#701a3f",
        "surface": "#ffffff",
        "surface-2": "#fce7f3",
        "primary": "#db2777",
        "primary-foreground": "#ffffff",
        "secondary": "#be185d",
        "secondary-foreground": "#ffffff",
        "muted": "#9f1239",
        "success": "#16a34a",
        "warning": "#d97706",
        "danger": "#be123c",
        "info": "#ec4899",
        "is_dark": False,
    },
    "Emerald Night": {
        "background": "#022c22",
        "foreground": "#d1fae5",
        "surface": "#064e3b",
        "surface-2": "#065f46",
        "primary": "#34d399",
        "primary-foreground": "#022c22",
        "secondary": "#10b981",
        "secondary-foreground": "#022c22",
        "muted": "#6ee7b7",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "danger": "#f87171",
        "info": "#2dd4bf",
        "is_dark": True,
    },
    "Monochrome": {
        "background": "#fafafa",
        "foreground": "#18181b",
        "surface": "#ffffff",
        "surface-2": "#e4e4e7",
        "primary": "#3f3f46",
        "primary-foreground": "#ffffff",
        "secondary": "#71717a",
        "secondary-foreground": "#ffffff",
        "muted": "#71717a",
        "success": "#16a34a",
        "warning": "#d97706",
        "danger": "#dc2626",
        "info": "#52525b",
        "is_dark": False,
    },
    "Nord": {
        "background": "#2e3440",
        "foreground": "#eceff4",
        "surface": "#3b4252",
        "surface-2": "#434c5e",
        "primary": "#88c0d0",
        "primary-foreground": "#2e3440",
        "secondary": "#81a1c1",
        "secondary-foreground": "#2e3440",
        "muted": "#d8dee9",
        "success": "#a3be8c",
        "warning": "#ebcb8b",
        "danger": "#bf616a",
        "info": "#8fbcbb",
        "is_dark": True,
    },
    "Monokai": {
        "background": "#1e1e1e",
        "foreground": "#f8f8f2",
        "surface": "#272822",
        "surface-2": "#3e3d32",
        "primary": "#a6e22e",
        "primary-foreground": "#1e1e1e",
        "secondary": "#66d9ef",
        "secondary-foreground": "#1e1e1e",
        "muted": "#75715e",
        "success": "#a6e22e",
        "warning": "#e6db74",
        "danger": "#f92672",
        "info": "#66d9ef",
        "is_dark": True,
    },
    "Solarized Light": {
        "background": "#fdf6e3",
        "foreground": "#002b36",
        "surface": "#eee8d5",
        "surface-2": "#e3dcc8",
        "primary": "#268bd2",
        "primary-foreground": "#fdf6e3",
        "secondary": "#2aa198",
        "secondary-foreground": "#fdf6e3",
        "muted": "#657b83",
        "success": "#859900",
        "warning": "#b58900",
        "danger": "#dc322f",
        "info": "#268bd2",
        "is_dark": False,
    },
    "Dracula": {
        "background": "#21222c",
        "foreground": "#f8f8f2",
        "surface": "#282a36",
        "surface-2": "#44475a",
        "primary": "#bd93f9",
        "primary-foreground": "#21222c",
        "secondary": "#ff79c6",
        "secondary-foreground": "#21222c",
        "muted": "#6272a4",
        "success": "#50fa7b",
        "warning": "#f1fa8c",
        "danger": "#ff5555",
        "info": "#8be9fd",
        "is_dark": True,
    },
}


def apply_theme_to_window(window: tk.Misc, theme_name: str) -> None:
    palette = PALETTE.get(theme_name, PALETTE["Arctic Light"])
    try:
        window.configure(bg=palette["background"])
    except tk.TclError:
        pass
    _style_text_widgets(window, palette)
    _style_menus(window, palette)


def _style_text_widgets(widget: tk.Widget, palette: dict[str, str]) -> None:
    for child in widget.winfo_children():
        if isinstance(child, tk.Text):
            child.configure(
                bg=palette["surface"],
                fg=palette["foreground"],
                insertbackground=palette["foreground"],
                highlightthickness=1,
                highlightcolor=palette["surface-2"],
                relief="flat",
            )
            if hasattr(child, "tag_config"):
                child.tag_config("info", foreground=palette["info"])
                child.tag_config("warn", foreground=palette["warning"])
                child.tag_config("error", foreground=palette["danger"])
                child.tag_config("success", foreground=palette["success"])
                child.tag_config("debug", foreground=palette["muted"])
                child.tag_config("token", foreground=palette["primary"])
        elif isinstance(child, tk.Listbox):
            child.configure(
                bg=palette["surface"],
                fg=palette["foreground"],
                selectbackground=_blend(palette["primary"], "#000000", 0.2),
                selectforeground=palette["primary-foreground"],
                highlightthickness=0,
                relief="flat",
            )
        elif isinstance(child, tk.Scrollbar):
            try:
                child.configure(
                    background=palette["surface-2"],
                    troughcolor=palette["surface"],
                )
            except tk.TclError:
                pass
        elif isinstance(child, ttk.Scrollbar):
            try:
                orientation = child.cget("orient")
                style_name = (
                    "Altomatic.Vertical.TScrollbar" if orientation == "vertical" else "Altomatic.Horizontal.TScrollbar"
                )
                child.configure(style=style_name)
            except tk.TclError:
                pass

        if isinstance(child, tk.Toplevel):
            child.configure(bg=palette["background"])

        _style_text_widgets(child, palette)


def apply_theme(root: TkinterDnD.Tk, theme_name: str) -> None:
    """Apply the modern Altomatic theme to the entire app."""

    palette = PALETTE.get(theme_name, PALETTE["Arctic Light"])
    style = ttk.Style(root)
    style.theme_use("clam")

    # Typography
    font_body = ("Segoe UI", 10)
    font_h1 = ("Segoe UI Semibold", 14)
    font_h2 = ("Segoe UI Semibold", 12)
    font_small = ("Segoe UI", 9)
    font_button = ("Segoe UI Semibold", 10)
    font_h3 = ("Segoe UI Semibold", 11)

    root.configure(bg=palette["background"])
    root.option_add("*Font", font_body)
    root.option_add("*Menu.font", font_body)
    root.option_add("*Menu.background", palette["surface"])
    root.option_add("*Menu.foreground", palette["foreground"])

    # Base styles
    style.configure("TFrame", background=palette["background"])
    style.configure(
        "Card.TFrame",
        background=palette["surface"],
        relief="solid",
        borderwidth=1,
        bordercolor=palette["surface-2"],
    )
    style.configure(
        "Section.TFrame",
        background=palette["surface"],
    )
    style.configure(
        "Chrome.TFrame",
        background=palette["surface"],
    )
    style.configure(
        "ChromeTitle.TLabel",
        background=palette["surface"],
        foreground=palette["foreground"],
        font=font_h2,
    )
    style.configure(
        "ChromeMenu.TLabel",
        background=palette["surface"],
        foreground=palette["muted"],
        padding=(10, 6),
        font=font_body,
    )
    style.map(
        "ChromeMenu.TLabel",
        foreground=[("active", palette["foreground"])],
        background=[("active", _blend(palette["background"], palette["primary"], 0.12))],
    )
    style.configure(
        "Section.TLabelframe",
        background=palette["background"],
        foreground=palette["muted"],
        padding=(16, 12, 16, 16),
        relief="solid",
        borderwidth=1,
        bordercolor=palette["surface-2"],
    )
    style.configure(
        "Section.TLabelframe.Label",
        background=palette["background"],
        foreground=palette["muted"],
        font=font_body,
    )

    # Text and inputs
    style.configure(
        "TLabel",
        background=palette["surface"],
        foreground=palette["foreground"],
        font=font_body,
    )
    style.configure(
        "Header.TLabel",
        background=palette["surface"],
        foreground=palette["foreground"],
        font=font_h3,
    )
    style.configure(
        "Card.TLabel",
        background=palette["surface"],
        foreground=palette["foreground"],
    )
    style.configure(
        "Small.TLabel",
        background=palette["surface"],
        font=font_small,
        foreground=palette["muted"],
    )
    style.configure(
        "Accent.TLabel",
        background=palette["surface"],
        foreground=palette["primary"],
    )
    style.configure(
        "Status.TLabel",
        background=palette["surface"],
        font=font_small,
        foreground=palette["muted"],
    )

    field_border = palette["surface-2"]
    focus_border = palette["primary"]
    style.configure(
        "TEntry",
        fieldbackground=palette["surface"],
        background=palette["surface"],
        foreground=palette["foreground"],
        insertcolor=palette["foreground"],
        padding=(8, 6),
        relief="solid",
        borderwidth=1,
        bordercolor=field_border,
    )
    style.map(
        "TEntry",
        bordercolor=[("focus", focus_border)],
        background=[("active", _blend(palette["surface"], palette["primary"], 0.05))],
    )

    style.map(
        "TButton",
        background=[
            ("pressed", _blend(palette["primary"], "#000000", 0.2)),
            ("active", _blend(palette["primary"], "#ffffff", 0.1)),
        ],
    )

    # Warning style for validation feedback
    warning_border = palette.get("warning", "#d97706")
    style.configure(
        "Warning.TEntry",
        fieldbackground=_blend(palette["surface"], palette.get("warning", "#d97706"), 0.05),
        background=palette["surface"],
        foreground=palette["foreground"],
        insertcolor=palette["foreground"],
        padding=(8, 6),
        relief="solid",
        borderwidth=1,
        bordercolor=warning_border,
    )
    style.map(
        "Warning.TEntry",
        bordercolor=[("focus", warning_border)],
        fieldbackground=[("focus", _blend(palette["surface"], palette.get("warning", "#d97706"), 0.1))],
    )

    style.configure(
        "TCombobox",
        fieldbackground=palette["surface"],
        background=palette["surface"],
        foreground=palette["foreground"],
        bordercolor=field_border,
        arrowcolor=palette["muted"],
        selectbackground=palette["surface-2"],
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", palette["surface"]), ("focus", palette["surface"])],
        bordercolor=[("focus", focus_border)],
    )

    style.configure(
        "TMenubutton",
        background=palette["surface-2"],
        foreground=palette["foreground"],
        borderwidth=1,
        bordercolor=field_border,
        padding=(10, 6),
    )
    style.map(
        "TMenubutton",
        background=[("active", _blend(palette["surface-2"], palette["primary"], 0.15))],
        bordercolor=[("active", focus_border)],
        foreground=[("active", palette["foreground"])],
    )

    style.configure(
        "TCheckbutton",
        background=palette["surface"],
        foreground=palette["foreground"],
        padding=(6, 4),
    )
    style.map(
        "TCheckbutton",
        background=[("active", palette["surface-2"])],
        foreground=[("disabled", _blend(palette["foreground"], palette["background"], 0.5))],
    )

    style.configure(
        "TRadiobutton",
        background=palette["surface"],
        foreground=palette["foreground"],
        padding=(6, 4),
    )

    # Notebook and tabs
    style.configure(
        "TNotebook",
        background=palette["background"],
        borderwidth=0,
        tabposition="n",
    )
    style.configure(
        "TNotebook.Tab",
        background=palette["background"],
        foreground=palette["muted"],
        padding=(18, 10),
        font=font_button,
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", palette["surface"])],
        foreground=[("selected", palette["foreground"])],
    )

    # Buttons
    button_base = palette["surface-2"]
    button_hover = _blend(button_base, palette["primary"], 0.12)
    button_pressed = _blend(button_base, palette["primary"], 0.24)
    style.configure(
        "TButton",
        background=button_base,
        foreground=palette["foreground"],
        padding=(12, 8),
        relief="flat",
        borderwidth=1,
        bordercolor=button_base,
        font=font_button,
    )
    style.map(
        "TButton",
        background=[("active", button_hover), ("pressed", button_pressed), ("focus", button_hover)],
        bordercolor=[("focus", focus_border), ("active", focus_border)],
        foreground=[("disabled", _blend(palette["foreground"], palette["background"], 0.6))],
    )

    accent_hover = _blend(palette["primary"], "#ffffff", 0.18)
    accent_pressed = _blend(palette["primary"], "#000000", 0.2)
    style.configure(
        "Accent.TButton",
        background=palette["primary"],
        foreground=palette["primary-foreground"],
        bordercolor=palette["primary"],
    )
    style.map(
        "Accent.TButton",
        background=[("active", accent_hover), ("pressed", accent_pressed)],
        bordercolor=[("focus", accent_pressed)],
    )

    secondary_hover = _blend(palette["secondary"], "#ffffff", 0.18)
    secondary_pressed = _blend(palette["secondary"], "#000000", 0.2)
    style.configure(
        "Secondary.TButton",
        background=palette["secondary"],
        foreground=palette["secondary-foreground"],
        bordercolor=palette["secondary"],
    )
    style.map(
        "Secondary.TButton",
        background=[("active", secondary_hover), ("pressed", secondary_pressed)],
        bordercolor=[("focus", secondary_pressed)],
    )

    # Progressbar & scrollbars
    style.configure(
        "TProgressbar",
        background=palette["primary"],
        troughcolor=palette["surface-2"],
        thickness=8,
        bordercolor=palette["surface-2"],
    )

    scrollbar_common = {
        "background": palette["surface-2"],
        "troughcolor": palette["surface"],
        "bordercolor": palette["surface"],
        "arrowcolor": palette["muted"],
    }
    style.configure("Altomatic.Vertical.TScrollbar", **scrollbar_common)
    style.configure("Altomatic.Horizontal.TScrollbar", **scrollbar_common)
    style.map(
        "Altomatic.Vertical.TScrollbar",
        background=[("active", button_hover)],
    )
    style.map(
        "Altomatic.Horizontal.TScrollbar",
        background=[("active", button_hover)],
    )

    _style_text_widgets(root, palette)
    _style_menus(root, palette)