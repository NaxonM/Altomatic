from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...config import open_config_folder
from ..themes import PALETTE
from ..ui_toolkit import (
    _create_info_label,
    _create_section_header,
    _apply_proxy_preferences,
    _refresh_detected_proxy,
    _save_settings,
    _reset_token_usage,
    _reset_global_stats,
)


def open_settings_dialog(state) -> None:
    """Open the settings dialog."""
    dialog = tk.Toplevel(state["root"])
    dialog.title("Settings")
    dialog.transient(state["root"])
    dialog.grab_set()
    dialog.geometry("540x340")
    dialog.resizable(False, False)

    dialog.rowconfigure(0, weight=1)
    dialog.columnconfigure(0, weight=1)

    main_frame = ttk.Frame(dialog, padding=(16, 8, 16, 16))
    main_frame.grid(row=0, column=0, sticky="nsew")
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(0, weight=1)

    notebook = ttk.Notebook(main_frame)
    notebook.grid(row=0, column=0, sticky="nsew")
    notebook.rowconfigure(0, weight=1)
    notebook.columnconfigure(0, weight=1)

    # Appearance Tab
    appearance_tab = ttk.Frame(notebook, padding=(0, 16, 0, 0))
    notebook.add(appearance_tab, text="🎨 Appearance")
    _build_appearance_section(appearance_tab, state)

    # Network Tab
    network_tab = ttk.Frame(notebook, padding=(0, 16, 0, 0))
    notebook.add(network_tab, text="🌐 Network")
    _build_proxy_section(network_tab, state)

    # Maintenance Tab
    maintenance_tab = ttk.Frame(notebook, padding=(0, 16, 0, 0))
    notebook.add(maintenance_tab, text="🛠️ Maintenance")
    _build_maintenance_section(maintenance_tab, state)

    ttk.Button(main_frame, text="Close", command=dialog.destroy).grid(row=1, column=0, sticky="e", pady=(16, 0))


def _build_appearance_section(parent, state) -> None:
    """Build the appearance settings section."""
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)
    appearance_card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    appearance_card.grid(row=0, column=0, sticky="nsew")
    appearance_card.columnconfigure(0, weight=1)
    appearance_card.rowconfigure(2, weight=1)

    # Theme selection
    theme_frame = ttk.Frame(appearance_card, style="Section.TFrame")
    theme_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
    theme_frame.columnconfigure(1, weight=1)

    ttk.Label(theme_frame, text="UI Theme:", style="TLabel").grid(
        row=0, column=0, sticky="w", padx=(0, 8)
    )

    themes = list(PALETTE.keys())
    theme_var = tk.StringVar(value=state["ui_theme"].get())

    def on_theme_change(theme_name):
        theme_var.set(theme_name)
        state["ui_theme"].set(theme_name)

    theme_menu = ttk.OptionMenu(
        theme_frame,
        theme_var,
        theme_var.get(),
        *themes,
        command=on_theme_change,
    )
    theme_menu.grid(row=0, column=1, sticky="w")

    _create_info_label(
        appearance_card,
        "Choose your preferred color theme for the interface."
    ).grid(row=2, column=0, sticky="w", pady=(12, 0))


def _build_proxy_section(parent, state) -> None:
    """Build the network proxy settings section."""
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)
    proxy_card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    proxy_card.grid(row=0, column=0, sticky="nsew")
    proxy_card.columnconfigure(0, weight=1)
    proxy_card.rowconfigure(4, weight=1)

    # Proxy enabled checkbox
    proxy_frame = ttk.Frame(proxy_card, style="Section.TFrame")
    proxy_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
    proxy_frame.columnconfigure(0, weight=1)

    ttk.Checkbutton(
        proxy_frame,
        text="Enable proxy",
        variable=state["proxy_enabled"]
    ).grid(row=0, column=0, sticky="w")

    # Proxy override entry
    override_frame = ttk.Frame(proxy_card, style="Section.TFrame")
    override_frame.grid(row=2, column=0, sticky="ew", pady=(0, 4))
    override_frame.columnconfigure(1, weight=1)

    ttk.Label(override_frame, text="Proxy override:", style="TLabel").grid(
        row=0, column=0, sticky="w", padx=(0, 8)
    )

    proxy_entry = ttk.Entry(override_frame, textvariable=state["proxy_override"])
    proxy_entry.grid(row=0, column=1, sticky="ew")
    state["proxy_override_entry"] = proxy_entry

    # Detected and effective proxy display
    proxy_info_frame = ttk.Frame(proxy_card, style="Section.TFrame")
    proxy_info_frame.grid(row=3, column=0, sticky="ew", pady=(0, 4))
    proxy_info_frame.columnconfigure(0, weight=1)

    ttk.Label(proxy_info_frame, text="Detected proxies:", style="Small.TLabel").grid(
        row=0, column=0, sticky="w", pady=(0, 4)
    )
    detected_label = ttk.Label(
        proxy_info_frame,
        textvariable=state["proxy_detected_label"],
        style="Small.TLabel",
        justify="left"
    )
    detected_label.grid(row=1, column=0, sticky="w")

    ttk.Label(proxy_info_frame, text="Effective proxies:", style="Small.TLabel").grid(
        row=2, column=0, sticky="w", pady=(8, 4)
    )
    effective_label = ttk.Label(
        proxy_info_frame,
        textvariable=state["proxy_effective_label"],
        style="Small.TLabel",
        justify="left"
    )
    effective_label.grid(row=3, column=0, sticky="w")

    _create_info_label(
        proxy_card,
        "Configure proxy settings for API requests. Leave override empty to use system proxy."
    ).grid(row=4, column=0, sticky="w", pady=(12, 0))


def _build_maintenance_section(parent, state) -> None:
    """Build the maintenance and statistics section."""
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)
    maintenance_card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    maintenance_card.grid(row=0, column=0, sticky="nsew")
    maintenance_card.columnconfigure(0, weight=1)
    maintenance_card.rowconfigure(3, weight=1)

    # Statistics frame
    stats_frame = ttk.Frame(maintenance_card, style="Section.TFrame")
    stats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
    stats_frame.columnconfigure(1, weight=1)

    # Global statistics
    global_stats_label = tk.StringVar(value="Images processed: 0")
    state["global_images_count"] = global_stats_label

    ttk.Label(stats_frame, text="Global Statistics:", style="TLabel").grid(
        row=0, column=0, sticky="w", padx=(0, 8)
    )

    ttk.Label(
        stats_frame,
        textvariable=global_stats_label,
        style="Small.TLabel"
    ).grid(row=0, column=1, sticky="w")

    # Reset buttons
    reset_frame = ttk.Frame(maintenance_card, style="Section.TFrame")
    reset_frame.grid(row=2, column=0, sticky="ew", pady=(0, 4))
    reset_frame.columnconfigure(2, weight=1)

    ttk.Button(
        reset_frame,
        text="Reset Token Usage",
        command=lambda: _reset_token_usage(state),
        style="Secondary.TButton"
    ).grid(row=0, column=0, sticky="w", padx=(0, 8))

    ttk.Button(
        reset_frame,
        text="Reset Statistics",
        command=lambda: _reset_global_stats(state),
        style="Secondary.TButton"
    ).grid(row=0, column=1, sticky="w", padx=(0, 8))

    # Save settings button
    ttk.Button(
        reset_frame,
        text="Save Settings",
        command=lambda: _save_settings(state),
        style="Accent.TButton"
    ).grid(row=0, column=2, sticky="e")

    _create_info_label(
        maintenance_card,
        "Reset counters and save current configuration. Settings are automatically saved when changed."
    ).grid(row=3, column=0, sticky="w", pady=(12, 0))
