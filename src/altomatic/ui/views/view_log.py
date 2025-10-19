from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..themes import PALETTE
from ..ui_toolkit import _copy_monitor, _clear_monitor


def build_log(parent, state) -> None:
    """Build the activity log tab."""
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(1, weight=1)

    # Toolbar
    toolbar = ttk.Frame(parent, style="Section.TFrame")
    toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))

    ttk.Button(
        toolbar,
        text="Copy Log",
        command=lambda: _copy_monitor(state),
        style="Secondary.TButton"
    ).pack(side="left", padx=(0, 8))

    ttk.Button(
        toolbar,
        text="Clear Log",
        command=lambda: _clear_monitor(state),
        style="Secondary.TButton"
    ).pack(side="left")

    # Log text area
    log_frame = ttk.Frame(parent, style="Section.TFrame")
    log_frame.grid(row=1, column=0, sticky="nsew")
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(0, weight=1)

    log_text = tk.Text(
        log_frame,
        wrap="word",
        height=12,
        state="disabled",
        relief="solid",
        borderwidth=1
    )
    log_text.grid(row=0, column=0, sticky="nsew")
    state["log_text"] = log_text

    scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    log_text.configure(yscrollcommand=scrollbar.set)

    # Configure color tags
    current_theme = state["ui_theme"].get()
    palette = PALETTE.get(current_theme, PALETTE.get("Arctic Light", {}))
    log_text.tag_config("info", foreground=palette.get("info"))
    log_text.tag_config("warn", foreground=palette.get("warning"))
    log_text.tag_config("error", foreground=palette.get("danger"))
    log_text.tag_config("success", foreground=palette.get("success"))
    log_text.tag_config("debug", foreground=palette.get("muted"))
    log_text.tag_config("token", foreground=palette.get("primary"))
