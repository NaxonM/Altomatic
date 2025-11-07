from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..themes import PALETTE
from ..ui_toolkit import _clear_monitor, _copy_monitor, refresh_log_view


def build_log(parent, state) -> None:
    """Build the activity log tab with filtering and auto-scroll controls."""
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(1, weight=1)

    levels = {"info": "Info", "success": "Success", "warn": "Warnings", "error": "Errors", "debug": "Debug"}
    filters = state.setdefault("activity_filters", {"levels": {key: True for key in levels}, "keyword": ""})
    level_vars = state.setdefault("activity_filter_vars", {})

    def _toggle_level(level_key: str) -> None:
        filters["levels"][level_key] = level_vars[level_key].get()
        refresh_log_view(state)
    # Toolbar
    toolbar = ttk.Frame(parent, style="Section.TFrame")
    toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    toolbar.columnconfigure(5, weight=1)

    ttk.Button(toolbar, text="Copy Log", command=lambda: _copy_monitor(state), style="Secondary.TButton").grid(
        row=0, column=0, padx=(0, 8)
    )
    ttk.Button(toolbar, text="Clear Log", command=lambda: _clear_monitor(state), style="Secondary.TButton").grid(
        row=0, column=1, padx=(0, 12)
    )

    ttk.Label(toolbar, text="Keyword", style="Small.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 6))
    keyword_var = tk.StringVar(value=filters.get("keyword", ""))
    state["activity_filter_keyword_var"] = keyword_var
    keyword_entry = ttk.Entry(toolbar, textvariable=keyword_var, width=20)
    keyword_entry.grid(row=0, column=3, sticky="w")

    def _apply_keyword_filter(*_) -> None:
        filters["keyword"] = keyword_var.get().strip()
        refresh_log_view(state)

    keyword_entry.bind("<KeyRelease>", _apply_keyword_filter)

    # Toggle options
    options_frame = ttk.Frame(toolbar, style="Section.TFrame")
    options_frame.grid(row=0, column=4, sticky="w", padx=(12, 0))

    show_timestamps = state.setdefault("show_timestamps", tk.BooleanVar(value=False))
    ttk.Checkbutton(
        options_frame,
        text="Timestamps",
        variable=show_timestamps,
        style="Small.TCheckbutton",
        command=lambda: refresh_log_view(state),
    ).grid(row=0, column=0, padx=(0, 8))

    follow_log = state.setdefault("log_auto_scroll", tk.BooleanVar(value=True))

    def _toggle_follow() -> None:
        if follow_log.get() and "log_text" in state:
            state["log_text"].yview_moveto(1.0)

    ttk.Checkbutton(
        options_frame,
        text="Auto-scroll",
        variable=follow_log,
        style="Small.TCheckbutton",
        command=_toggle_follow,
    ).grid(row=0, column=1)

    # Log text area
    log_frame = ttk.Frame(parent, style="Section.TFrame")
    log_frame.grid(row=1, column=0, sticky="nsew")
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(0, weight=1)

    log_container = ttk.Frame(log_frame, style="Section.TFrame")
    log_container.grid(row=0, column=0, sticky="nsew")
    log_container.columnconfigure(0, weight=1)
    log_container.rowconfigure(0, weight=1)

    log_text = tk.Text(log_container, wrap="word", height=12, state="disabled", relief="solid", borderwidth=1)
    log_text.grid(row=0, column=0, sticky="nsew")
    state["log_text"] = log_text

    scrollbar = ttk.Scrollbar(log_container, orient="vertical", command=log_text.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    log_text.configure(yscrollcommand=lambda *args: _on_log_scroll(*args, scrollbar=scrollbar))

    sidebar = ttk.Frame(log_frame, style="Section.TFrame")
    sidebar.grid(row=0, column=1, sticky="nsw", padx=(12, 0))
    sidebar.columnconfigure(0, weight=1)

    ttk.Label(sidebar, text="Levels", style="Small.TLabel").grid(row=0, column=0, sticky="w")
    for row_index, (level_key, label) in enumerate(levels.items(), start=1):
        var = tk.BooleanVar(value=filters["levels"].get(level_key, True))
        level_vars[level_key] = var
        ttk.Checkbutton(
            sidebar,
            text=label,
            variable=var,
            style="Small.TCheckbutton",
            command=lambda key=level_key: _toggle_level(key),
        ).grid(row=row_index, column=0, sticky="w", pady=(2 if row_index > 1 else 4, 0))

    state.setdefault("log_entry_limit", 1000)

    def _scroll_canvas(direction: int) -> str:
        log_text.yview_scroll(direction, "units")
        follow_log.set(False)
        return "break"

    def _on_mousewheel(event):
        if event.state & 0x0004:  # Control key pressed -> zoom, ignore
            return
        direction = -1 if event.delta > 0 else 1
        return _scroll_canvas(direction)

    log_text.bind("<Enter>", lambda _: log_text.bind("<MouseWheel>", _on_mousewheel))
    log_text.bind("<Leave>", lambda _: log_text.unbind("<MouseWheel>"))
    log_text.bind("<Button-4>", lambda _e: _scroll_canvas(-1))
    log_text.bind("<Button-5>", lambda _e: _scroll_canvas(1))
    log_text.bind("<ButtonPress-1>", lambda _: follow_log.set(False))
    log_text.bind("<KeyPress>", lambda _: follow_log.set(False))
    scrollbar.bind("<ButtonPress-1>", lambda _: follow_log.set(False))

    # Configure color tags
    current_theme = state["ui_theme"].get()
    palette = PALETTE.get(current_theme, PALETTE.get("Arctic Light", {}))
    log_text.tag_config("info", foreground=palette.get("info"))
    log_text.tag_config("warn", foreground=palette.get("warning"))
    log_text.tag_config("error", foreground=palette.get("danger"))
    log_text.tag_config("success", foreground=palette.get("success"))
    log_text.tag_config("debug", foreground=palette.get("muted"))
    log_text.tag_config("token", foreground=palette.get("primary"))

    refresh_log_view(state)


def _on_log_scroll(*args, scrollbar):
    scrollbar.set(*args)
