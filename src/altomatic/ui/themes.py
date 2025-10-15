"""Modern ttk theme helpers for Altomatic."""

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


PALETTE = {
    "Arctic Light": {
        "background": "#eef2fb",
        "foreground": "#0f172a",
        "surface": "#f9fbff",
        "surface-2": "#dce4f5",
        "primary": "#2563eb",
        "primary-foreground": "#ffffff",
        "secondary": "#4f5d7a",
        "secondary-foreground": "#ffffff",
        "muted": "#7b8aaf",
        "success": "#16a34a",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#3b82f6",
        "is_dark": False,
    },
    "Midnight": {
        "background": "#10172a",
        "foreground": "#f1f5f9",
        "surface": "#192237",
        "surface-2": "#253149",
        "primary": "#06b6d4",
        "primary-foreground": "#07121c",
        "secondary": "#4c5a6f",
        "secondary-foreground": "#f8fafc",
        "muted": "#9aa9c5",
        "success": "#22c55e",
        "warning": "#fbbf24",
        "danger": "#f43f5e",
        "info": "#38bdf8",
        "is_dark": True,
    },
    "Forest": {
        "background": "#e7f6ed",
        "foreground": "#08311f",
        "surface": "#f8fdf9",
        "surface-2": "#ccebd8",
        "primary": "#0d9a6d",
        "primary-foreground": "#ffffff",
        "secondary": "#0b7a59",
        "secondary-foreground": "#ffffff",
        "muted": "#6a7c70",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#dc2626",
        "info": "#0f8ba4",
        "is_dark": False,
    },
    "Sunset": {
        "background": "#201425",
        "foreground": "#fde5e2",
        "surface": "#302034",
        "surface-2": "#46304a",
        "primary": "#fb7d3a",
        "primary-foreground": "#ffffff",
        "secondary": "#f472b6",
        "secondary-foreground": "#1c0c16",
        "muted": "#e3c4ff",
        "success": "#84cc16",
        "warning": "#fbbb45",
        "danger": "#ff5f6d",
        "info": "#d0a2ff",
        "is_dark": True,
    },
    "Lavender": {
        "background": "#f4f0ff",
        "foreground": "#32125a",
        "surface": "#fbf9ff",
        "surface-2": "#e4d8ff",
        "primary": "#8a3ef5",
        "primary-foreground": "#ffffff",
        "secondary": "#6f3bec",
        "secondary-foreground": "#ffffff",
        "muted": "#ab9ef0",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#8b5cf6",
        "is_dark": False,
    },
    "Charcoal": {
        "background": "#1f1f24",
        "foreground": "#f5f5f6",
        "surface": "#2c2c33",
        "surface-2": "#3e3e46",
        "primary": "#f7c948",
        "primary-foreground": "#1f1f24",
        "secondary": "#888895",
        "secondary-foreground": "#1f1f24",
        "muted": "#b8b8c3",
        "success": "#4ade80",
        "warning": "#fbbf54",
        "danger": "#f87171",
        "info": "#74a6ff",
        "is_dark": True,
    },
    "Ocean Blue": {
        "background": "#e8f1ff",
        "foreground": "#1a3c76",
        "surface": "#f6f9ff",
        "surface-2": "#ccdcfb",
        "primary": "#2b6be9",
        "primary-foreground": "#ffffff",
        "secondary": "#1f4db1",
        "secondary-foreground": "#ffffff",
        "muted": "#7aa4f8",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#dc2626",
        "info": "#0ea5e9",
        "is_dark": False,
    },
    "Deep Space": {
        "background": "#111129",
        "foreground": "#e4e7ff",
        "surface": "#1f1f3c",
        "surface-2": "#303061",
        "primary": "#94a3ff",
        "primary-foreground": "#0f1026",
        "secondary": "#6f74ff",
        "secondary-foreground": "#0f1026",
        "muted": "#bac3ff",
        "success": "#40ddac",
        "warning": "#f8d85a",
        "danger": "#ff7a86",
        "info": "#a0c2ff",
        "is_dark": True,
    },
    "Warm Sand": {
        "background": "#f8f3e6",
        "foreground": "#4a2b0c",
        "surface": "#fdf9f0",
        "surface-2": "#f2e4c8",
        "primary": "#d0801f",
        "primary-foreground": "#ffffff",
        "secondary": "#a15912",
        "secondary-foreground": "#ffffff",
        "muted": "#8a7669",
        "success": "#16a34a",
        "warning": "#f59f3d",
        "danger": "#dc2626",
        "info": "#0f8aa8",
        "is_dark": False,
    },
    "Cherry Blossom": {
        "background": "#f9eef4",
        "foreground": "#7a1439",
        "surface": "#fff9fb",
        "surface-2": "#f3d6e3",
        "primary": "#f062a6",
        "primary-foreground": "#ffffff",
        "secondary": "#dd3c89",
        "secondary-foreground": "#ffffff",
        "muted": "#f2a6cb",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "danger": "#c0174e",
        "info": "#f8add8",
        "is_dark": False,
    },
    "Emerald Night": {
        "background": "#07332a",
        "foreground": "#cffae7",
        "surface": "#0c4b3d",
        "surface-2": "#116152",
        "primary": "#38d9a9",
        "primary-foreground": "#042a22",
        "secondary": "#18b892",
        "secondary-foreground": "#042a22",
        "muted": "#74e8c7",
        "success": "#22c55e",
        "warning": "#f7c948",
        "danger": "#f87171",
        "info": "#2dd4bf",
        "is_dark": True,
    },
    "Monochrome": {
        "background": "#f3f3f3",
        "foreground": "#1f1f1f",
        "surface": "#fdfdfd",
        "surface-2": "#dedede",
        "primary": "#4b4b4b",
        "primary-foreground": "#ffffff",
        "secondary": "#6f6f6f",
        "secondary-foreground": "#ffffff",
        "muted": "#a6a6a6",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "danger": "#dc2626",
        "info": "#5f5f5f",
        "is_dark": False,
    },
    "Nord": {
        "background": "#2e3440",
        "foreground": "#eceff4",
        "surface": "#3b4252",
        "surface-2": "#434c5e",
        "primary": "#88c0d0",
        "primary-foreground": "#1b1f29",
        "secondary": "#81a1c1",
        "secondary-foreground": "#1b1f29",
        "muted": "#aebbd5",
        "success": "#a3be8c",
        "warning": "#ebcb8b",
        "danger": "#bf616a",
        "info": "#8fbcbb",
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
        "Chrome.TFrame",
        background=palette["surface"],
    )
    style.configure(
        "ChromeTitle.TLabel",
        background=palette["surface"],
        foreground=palette["foreground"],
        font=("Segoe UI Semibold", 12),
    )
    style.configure(
        "ChromeMenu.TLabel",
        background=palette["surface"],
        foreground=palette["muted"],
        padding=(10, 6),
        font=("Segoe UI", 10),
    )
    style.map(
        "ChromeMenu.TLabel",
        foreground=[("active", palette["foreground"])],
        background=[("active", _blend(palette["surface"], palette["primary"], 0.12))],
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