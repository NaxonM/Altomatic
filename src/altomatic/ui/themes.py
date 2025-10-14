"""Modern ttk theme helpers for Altomatic."""

from __future__ import annotations

import ctypes
import os
import tkinter as tk
from tkinter import ttk
if os.name == "nt":
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19

from tkinterdnd2 import TkinterDnD


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in range(0, 6, 2))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{channel:02x}" for channel in rgb)


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
    dark_mode = 1 if _is_dark_palette(palette) else 0
    value = ctypes.c_int(dark_mode)
    try:
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception:
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                ctypes.byref(value),
                ctypes.sizeof(value),
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


PALETTE = {
    "Arctic Light": {
        "background": "#f8fafc",
        "foreground": "#0f172a",
        "surface": "#ffffff",
        "surface-2": "#e2e8f0",
        "primary": "#0ea5e9",
        "primary-foreground": "#ffffff",
        "secondary": "#64748b",
        "secondary-foreground": "#ffffff",
        "muted": "#94a3b8",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#3b82f6",
        "is_dark": False,
    },
    "Midnight": {
        "background": "#0a0e1a",
        "foreground": "#f1f5f9",
        "surface": "#141b2d",
        "surface-2": "#1e293b",
        "primary": "#06b6d4",
        "primary-foreground": "#0a0e1a",
        "secondary": "#475569",
        "secondary-foreground": "#f1f5f9",
        "muted": "#94a3b8",
        "success": "#22c55e",
        "warning": "#fbbf24",
        "danger": "#f43f5e",
        "info": "#38bdf8",
        "is_dark": True,
    },
    "Forest": {
        "background": "#f0fdf4",
        "foreground": "#052e16",
        "surface": "#ffffff",
        "surface-2": "#d1fae5",
        "primary": "#059669",
        "primary-foreground": "#ffffff",
        "secondary": "#047857",
        "secondary-foreground": "#ffffff",
        "muted": "#6b7280",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#dc2626",
        "info": "#0891b2",
        "is_dark": False,
    },
    "Sunset": {
        "background": "#1a0f1e",
        "foreground": "#fef3f2",
        "surface": "#2d1b2e",
        "surface-2": "#432837",
        "primary": "#f97316",
        "primary-foreground": "#ffffff",
        "secondary": "#ec4899",
        "secondary-foreground": "#ffffff",
        "muted": "#d8b4fe",
        "success": "#84cc16",
        "warning": "#fbbf24",
        "danger": "#ef4444",
        "info": "#c084fc",
        "is_dark": True,
    },
    "Lavender": {
        "background": "#faf5ff",
        "foreground": "#3b0764",
        "surface": "#ffffff",
        "surface-2": "#f3e8ff",
        "primary": "#9333ea",
        "primary-foreground": "#ffffff",
        "secondary": "#7c3aed",
        "secondary-foreground": "#ffffff",
        "muted": "#a78bfa",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#8b5cf6",
        "is_dark": False,
    },
    "Charcoal": {
        "background": "#18181b",
        "foreground": "#fafafa",
        "surface": "#27272a",
        "surface-2": "#3f3f46",
        "primary": "#facc15",
        "primary-foreground": "#18181b",
        "secondary": "#71717a",
        "secondary-foreground": "#fafafa",
        "muted": "#a1a1aa",
        "success": "#4ade80",
        "warning": "#fb923c",
        "danger": "#f87171",
        "info": "#60a5fa",
        "is_dark": True,
    },
    "Ocean Blue": {
        "background": "#eff6ff",
        "foreground": "#1e3a8a",
        "surface": "#ffffff",
        "surface-2": "#dbeafe",
        "primary": "#2563eb",
        "primary-foreground": "#ffffff",
        "secondary": "#1e40af",
        "secondary-foreground": "#ffffff",
        "muted": "#60a5fa",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#dc2626",
        "info": "#0ea5e9",
        "is_dark": False,
    },
    "Deep Space": {
        "background": "#0c0a1d",
        "foreground": "#e0e7ff",
        "surface": "#1a1633",
        "surface-2": "#2e2657",
        "primary": "#818cf8",
        "primary-foreground": "#0c0a1d",
        "secondary": "#6366f1",
        "secondary-foreground": "#ffffff",
        "muted": "#a5b4fc",
        "success": "#34d399",
        "warning": "#fcd34d",
        "danger": "#f87171",
        "info": "#93c5fd",
        "is_dark": True,
    },
    "Warm Sand": {
        "background": "#fefcf3",
        "foreground": "#451a03",
        "surface": "#ffffff",
        "surface-2": "#fef3c7",
        "primary": "#d97706",
        "primary-foreground": "#ffffff",
        "secondary": "#92400e",
        "secondary-foreground": "#ffffff",
        "muted": "#78716c",
        "success": "#16a34a",
        "warning": "#f59e0b",
        "danger": "#dc2626",
        "info": "#0891b2",
        "is_dark": False,
    },
    "Cherry Blossom": {
        "background": "#fdf2f8",
        "foreground": "#831843",
        "surface": "#ffffff",
        "surface-2": "#fce7f3",
        "primary": "#ec4899",
        "primary-foreground": "#ffffff",
        "secondary": "#db2777",
        "secondary-foreground": "#ffffff",
        "muted": "#f472b6",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "danger": "#be123c",
        "info": "#f9a8d4",
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
        "secondary-foreground": "#ffffff",
        "muted": "#6ee7b7",
        "success": "#22c55e",
        "warning": "#fbbf24",
        "danger": "#f43f5e",
        "info": "#2dd4bf",
        "is_dork": True,
    },
    "Monochrome": {
        "background": "#fafafa",
        "foreground": "#171717",
        "surface": "#ffffff",
        "surface-2": "#e5e5e5",
        "primary": "#404040",
        "primary-foreground": "#ffffff",
        "secondary": "#737373",
        "secondary-foreground": "#ffffff",
        "muted": "#a3a3a3",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "danger": "#dc2626",
        "info": "#525252",
        "is_dark": False,
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

    root.configure(bg=palette["background"])
    root.option_add("*Font", "{Segoe UI} 10")
    root.option_add("*Menu.font", "{Segoe UI} 10")
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
        "Section.TLabelframe",
        background=palette["surface"],
        foreground=palette["muted"],
        padding=(16, 12, 16, 16),
        relief="solid",
        borderwidth=1,
        bordercolor=palette["surface-2"],
    )
    style.configure(
        "Section.TLabelframe.Label",
        background=palette["surface"],
        foreground=palette["muted"],
        font=("Segoe UI Semibold", 10),
    )

    # Text and inputs
    style.configure(
        "TLabel",
        background=palette["background"],
        foreground=palette["foreground"],
        font=("Segoe UI", 10),
    )
    style.configure(
        "Card.TLabel",
        background=palette["surface"],
    )
    style.configure(
        "Small.TLabel",
        font=("Segoe UI", 9),
        foreground=palette["muted"],
        background=palette["surface"],
    )
    style.configure(
        "Accent.TLabel",
        foreground=palette["primary"],
        background=palette["background"],
    )
    style.configure(
        "Status.TLabel",
        font=("Segoe UI", 9),
        foreground=palette["muted"],
        background=palette["background"],
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
        font=("Segoe UI Semibold", 10),
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
        font=("Segoe UI Semibold", 10),
    )
    style.map(
        "TButton",
        background=[("active", button_hover), ("pressed", button_pressed)],
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