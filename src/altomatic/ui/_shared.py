"""Shared UI helper functions."""

from __future__ import annotations

from tkinter import ttk


def _create_section_header(parent, text: str, style="Header.TLabel") -> ttk.Label:
    """Create a consistent section header."""
    return ttk.Label(parent, text=text, style=style)


def _create_info_label(parent, text: str, wraplength=500) -> ttk.Label:
    """Create a consistent info/help label."""
    return ttk.Label(parent, text=text, style="Small.TLabel", wraplength=wraplength, justify="left")
