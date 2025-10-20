from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...config import open_config_folder
from ...models import AVAILABLE_PROVIDERS, get_models_for_provider, get_provider_label, refresh_openrouter_models, get_default_model, format_pricing
from ..themes import PALETTE
from ..ui_toolkit import (
    CollapsiblePane,
    _create_info_label,
    _create_section_header,
    set_status,
    validate_api_key,
    update_api_key_validation_display,
    initialize_provider_ui,
    _apply_proxy_preferences,
    _refresh_detected_proxy,
    _save_settings,
    _reset_token_usage,
    _reset_global_stats,
    append_monitor_colored,
    pyperclip,
    refresh_prompt_choices,
)
from ..dialogs.prompt_editor import open_prompt_editor


def build_tab_configuration(frame, state) -> None:
    """Build the consolidated configuration tab."""
    frame.columnconfigure(0, weight=1)

    # Create accordion group for all collapsible panes
    accordion_group = []

    # AI Provider & Model
    pane1 = CollapsiblePane(frame, text="🤖 AI Provider & Model", accordion_group=accordion_group)
    pane1.grid(row=0, column=0, sticky="ew", pady=(0, 16))
    accordion_group.append(pane1)
    _build_llm_provider_section(pane1.frame, state)

    # Prompt Management
    pane2 = CollapsiblePane(frame, text="✍️ Prompt Management", accordion_group=accordion_group)
    pane2.grid(row=1, column=0, sticky="ew", pady=(0, 16))
    accordion_group.append(pane2)
    _build_prompt_management_section(pane2.frame, state)

    # Appearance
    pane3 = CollapsiblePane(frame, text="🎨 Appearance", accordion_group=accordion_group)
    pane3.grid(row=2, column=0, sticky="ew", pady=(0, 16))
    accordion_group.append(pane3)
    _build_appearance_section(pane3.frame, state)

    # Network
    pane4 = CollapsiblePane(frame, text="🌐 Network", accordion_group=accordion_group)
    pane4.grid(row=3, column=0, sticky="ew", pady=(0, 16))
    accordion_group.append(pane4)
    _build_proxy_section(pane4.frame, state)

    # Maintenance
    pane5 = CollapsiblePane(frame, text="🛠️ Maintenance", accordion_group=accordion_group)
    pane5.grid(row=4, column=0, sticky="ew", pady=(0, 16))
    accordion_group.append(pane5)
    _build_maintenance_section(pane5.frame, state)


def _build_prompt_management_section(parent, state) -> None:
    """Build the prompt management section."""
    parent.columnconfigure(0, weight=1)
    prompt_card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    prompt_card.grid(row=0, column=0, sticky="nsew")
    prompt_card.columnconfigure(0, weight=1)
    prompt_card.rowconfigure(2, weight=1)

    # Prompt selection
    selection_frame = ttk.Frame(prompt_card, style="Section.TFrame")
    selection_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
    selection_frame.columnconfigure(1, weight=1)

    ttk.Label(selection_frame, text="Active preset:", style="TLabel").grid(
        row=0, column=0, sticky="w", padx=(0, 8)
    )

    prompt_labels = {v["label"]: k for k, v in state["prompts"].items()}
    prompt_label_var = tk.StringVar(value=state["prompts"][state["prompt_key"].get()]["label"])

    def on_prompt_select(label):
        key = prompt_labels[label]
        state["prompt_key"].set(key)
        prompt_label_var.set(label)

    prompt_menu = ttk.OptionMenu(
        selection_frame,
        prompt_label_var,
        prompt_label_var.get(),
        *prompt_labels.keys(),
        command=on_prompt_select,
    )
    prompt_menu.grid(row=0, column=1, sticky="w")
    state["prompt_option_widget"] = prompt_menu
    state["prompt_option_menu"] = prompt_menu["menu"]

    ttk.Button(
        selection_frame,
        text="Edit Prompts...",
        command=lambda: open_prompt_editor(state),
        style="Accent.TButton",
    ).grid(row=0, column=2, sticky="e", padx=(16, 0))

    # Preview
    preview_frame = ttk.Frame(prompt_card, style="Section.TFrame")
    preview_frame.grid(row=2, column=0, sticky="nsew")
    preview_frame.columnconfigure(0, weight=1)
    preview_frame.rowconfigure(0, weight=1)

    prompt_preview = tk.Text(
        preview_frame,
        height=12,
        wrap="word",
        state="disabled",
        relief="solid",
        borderwidth=1,
    )
    prompt_preview.grid(row=0, column=0, sticky="nsew")

    preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=prompt_preview.yview)
    preview_scrollbar.grid(row=0, column=1, sticky="ns")
    prompt_preview.configure(yscrollcommand=preview_scrollbar.set)
    state["prompt_preview"] = prompt_preview

    _create_info_label(
        prompt_card,
        "Use the editor to create custom prompts or modify existing presets."
    ).grid(row=3, column=0, sticky="w", pady=(12, 0))

    refresh_prompt_choices(state)


def _build_llm_provider_section(parent, state) -> None:
    """Build the redesigned LLM provider section with original show/hide behavior."""
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)

    # Main container with compact padding
    main_container = ttk.Frame(parent, style="TFrame")
    main_container.grid(row=0, column=0, sticky="nsew")
    main_container.columnconfigure(0, weight=1)
    main_container.rowconfigure(1, weight=1)

    # === Provider Selection (Compact) ===
    provider_card = ttk.Frame(main_container, style="Card.TFrame", padding=8)
    provider_card.grid(row=0, column=0, sticky="ew", pady=(0, 4))
    provider_card.columnconfigure(1, weight=1)

    # Provider selection with status
    provider_select_frame = ttk.Frame(provider_card, style="Section.TFrame")
    provider_select_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
    provider_select_frame.columnconfigure(1, weight=1)

    ttk.Label(provider_select_frame, text="Provider:", style="TLabel").grid(
        row=0, column=0, sticky="w", padx=(0, 8)
    )

    provider_labels = {get_provider_label(pid): pid for pid in AVAILABLE_PROVIDERS}
    provider_label_var = tk.StringVar(value=get_provider_label(state["llm_provider"].get()))
    state["provider_label_var"] = provider_label_var

    provider_menu = ttk.OptionMenu(
        provider_select_frame,
        provider_label_var,
        provider_label_var.get(),
        *provider_labels.keys(),
        command=lambda label: state["llm_provider"].set(provider_labels[label]),
    )
    provider_menu.grid(row=0, column=1, sticky="w")
    state["provider_option_menu"] = provider_menu["menu"]

    # Provider status
    provider_status_var = tk.StringVar(value="● Ready")
    provider_status_label = ttk.Label(
        provider_select_frame,
        textvariable=provider_status_var,
        style="Small.TLabel"
    )
    provider_status_label.grid(row=0, column=2, sticky="e", padx=(16, 0))
    state["provider_status_label"] = provider_status_label
    state["provider_status_var"] = provider_status_var

    # === Model Selection (Compact) ===
    model_card = ttk.Frame(main_container, style="Card.TFrame", padding=0)
    model_card.grid(row=1, column=0, sticky="ew", pady=(0, 4))
    model_card.columnconfigure(2, weight=1)

    # Model selection controls
    model_select_frame = ttk.Frame(model_card, style="Section.TFrame")
    model_select_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
    model_select_frame.columnconfigure(1, weight=1)

    ttk.Label(model_select_frame, text="Model:", style="TLabel").grid(
        row=0, column=0, sticky="w", padx=(0, 8)
    )

    model_label_var = tk.StringVar()
    state["model_label_var"] = model_label_var

    model_menu = ttk.OptionMenu(model_select_frame, model_label_var, "")
    model_menu.grid(row=0, column=1, sticky="w")
    state["model_option_widget"] = model_menu
    state["model_option_menu"] = model_menu["menu"]

    def _refresh_openrouter_models_ui() -> None:
        try:
            set_status(state, "Refreshing OpenRouter models...")
            refresh_openrouter_models()

            models = get_models_for_provider("openrouter")
            if not models:
                set_status(state, "No OpenRouter models available")
                return

            current = state["openrouter_model"].get()
            if current not in models:
                fallback = get_default_model("openrouter")
                state["openrouter_model"].set(fallback)
                if state["llm_provider"].get() == "openrouter":
                    state["llm_model"].set(fallback)

            state["provider_model_map"]["openrouter"] = state["openrouter_model"].get()
            # Refresh model choices in the dropdown
            if "model_option_menu" in state:
                menu = state["model_option_menu"]
                menu.delete(0, "end")
                for model_id, info in models.items():
                    label = info.get("label", model_id)
                    menu.add_command(label=label, command=lambda value=model_id: state["llm_model"].set(value))

                current_model = state["llm_model"].get()
                if current_model in models:
                    state["model_label_var"].set(models[current_model].get("label", current_model))

            update_model_pricing(state)
            update_summary(state)

            model_count = len(models)
            set_status(state, f"✓ Refreshed {model_count} OpenRouter models")

        except Exception as exc:
            error_msg = f"Could not refresh OpenRouter models: {str(exc)}"
            set_status(state, error_msg)
            append_monitor_colored(state, error_msg, "error")

    refresh_button = ttk.Button(
        model_select_frame,
        text="⟳ Refresh",
        command=_refresh_openrouter_models_ui,
        style="Secondary.TButton"
    )
    refresh_button.grid(row=0, column=2, sticky="e", padx=(16, 0))
    state["refresh_openrouter_button"] = refresh_button

    # Model information display
    model_info_frame = ttk.Frame(model_card, style="Section.TFrame")
    model_info_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(4, 0))
    model_info_frame.columnconfigure(0, weight=1)

    state["lbl_model_pricing"] = ttk.Label(
        model_info_frame,
        text="Select a model to view pricing and capabilities",
        justify="left",
        style="Small.TLabel",
        wraplength=600
    )
    state["lbl_model_pricing"].grid(row=0, column=0, sticky="w")

    capabilities_label = ttk.Label(
        model_info_frame,
        text="Capabilities: Vision, Text",
        style="Small.TLabel"
    )
    capabilities_label.grid(row=1, column=0, sticky="w", pady=(4, 0))
    state["model_capabilities_label"] = capabilities_label

    # === API Keys Section (Show/Hide) ===
    api_card = ttk.Frame(main_container, style="Card.TFrame", padding=0)
    api_card.grid(row=2, column=0, sticky="ew", pady=(0, 4))
    api_card.columnconfigure(0, weight=1)

    # OpenAI section (show/hide based on provider)
    openai_frame = ttk.Frame(api_card, style="Section.TFrame", padding=8)
    openai_frame.grid(row=1, column=0, sticky="ew")
    openai_frame.columnconfigure(1, weight=1)
    _build_compact_openai_config(openai_frame, state)
    state["openai_section"] = openai_frame

    # OpenRouter section (show/hide based on provider)
    openrouter_frame = ttk.Frame(api_card, style="Section.TFrame", padding=8)
    openrouter_frame.grid(row=2, column=0, sticky="ew")
    openrouter_frame.columnconfigure(1, weight=1)
    _build_compact_openrouter_config(openrouter_frame, state)
    state["openrouter_section"] = openrouter_frame

    # Initialize the UI
    initialize_provider_ui(state)


def _build_compact_openai_config(parent, state) -> None:
    """Build compact OpenAI configuration section."""
    parent.columnconfigure(1, weight=1)

    # Header and API key in one row
    header_frame = ttk.Frame(parent, style="TFrame")
    header_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
    header_frame.columnconfigure(0, weight=1)

    provider_label = ttk.Label(
        header_frame,
        text="OpenAI",
        font=("Segoe UI Semibold", 10),
        foreground="#10a37f"
    )
    provider_label.grid(row=0, column=0, sticky="w")

    # API key input row
    ttk.Label(parent, text="API Key:", style="TLabel").grid(
        row=1, column=0, sticky="w", padx=(0, 8)
    )

    api_key_entry = ttk.Entry(parent, textvariable=state["openai_api_key"], show="*", width=35)
    api_key_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8))
    state["openai_api_entry"] = api_key_entry

    show_key_var = tk.BooleanVar()

    def _toggle_openai_key() -> None:
        api_key_entry.config(show="" if show_key_var.get() else "*")

    show_key_cb = ttk.Checkbutton(
        parent,
        text="Show",
        variable=show_key_var,
        command=_toggle_openai_key,
        style="Small.TCheckbutton"
    )
    show_key_cb.grid(row=1, column=2, sticky="w")

    # Controls in same row
    controls_frame = ttk.Frame(parent, style="Section.TFrame")
    controls_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(4, 0))
    controls_frame.columnconfigure(1, weight=1)

    def _paste_openai_key() -> None:
        if pyperclip is None:
            set_status(state, "Clipboard support not available")
            return
        try:
            if content := pyperclip.paste():
                content = content.strip()
                if content:
                    is_valid, message = validate_api_key("openai", content)
                    state["openai_api_key"].set(content)
                    if is_valid:
                        set_status(state, f"✓ OpenAI API key pasted and validated")
                    else:
                        set_status(state, f"⚠ OpenAI API key pasted but {message.lower()}")
                else:
                    set_status(state, "Clipboard is empty")
            else:
                set_status(state, "Clipboard is empty")
        except (pyperclip.PyperclipException, tk.TclError) as e:
            set_status(state, f"Could not access clipboard: {str(e)}")
        except Exception as e:
            set_status(state, f"Unexpected error pasting API key: {str(e)}")

    paste_button = ttk.Button(
        controls_frame,
        text="📋 Paste",
        command=_paste_openai_key,
        style="Secondary.TButton"
    )
    paste_button.grid(row=0, column=0, sticky="w")

    openai_status_var = tk.StringVar(value="Not configured")
    openai_status_label = ttk.Label(
        controls_frame,
        textvariable=openai_status_var,
        style="Small.TLabel"
    )
    openai_status_label.grid(row=0, column=1, sticky="e")
    state["openai_status_label"] = openai_status_label
    state["openai_status_var"] = openai_status_var


def _build_compact_openrouter_config(parent, state) -> None:
    """Build compact OpenRouter configuration section."""
    parent.columnconfigure(1, weight=1)

    # Header and API key in one row
    header_frame = ttk.Frame(parent, style="TFrame")
    header_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
    header_frame.columnconfigure(0, weight=1)

    provider_label = ttk.Label(
        header_frame,
        text="OpenRouter",
        font=("Segoe UI Semibold", 10),
        foreground="#ff6b35"
    )
    provider_label.grid(row=0, column=0, sticky="w")

    # API key input row
    ttk.Label(parent, text="API Key:", style="TLabel").grid(
        row=1, column=0, sticky="w", padx=(0, 8)
    )

    api_key_entry = ttk.Entry(parent, textvariable=state["openrouter_api_key"], show="*", width=35)
    api_key_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8))
    state["openrouter_api_entry"] = api_key_entry

    show_key_var = tk.BooleanVar()

    def _toggle_openrouter_key() -> None:
        api_key_entry.config(show="" if show_key_var.get() else "*")

    show_key_cb = ttk.Checkbutton(
        parent,
        text="Show",
        variable=show_key_var,
        command=_toggle_openrouter_key,
        style="Small.TCheckbutton"
    )
    show_key_cb.grid(row=1, column=2, sticky="w")

    # Controls in same row
    controls_frame = ttk.Frame(parent, style="Section.TFrame")
    controls_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(4, 0))
    controls_frame.columnconfigure(1, weight=1)

    def _paste_openrouter_key() -> None:
        if pyperclip is None:
            set_status(state, "Clipboard support not available")
            return
        try:
            if content := pyperclip.paste():
                content = content.strip()
                if content:
                    is_valid, message = validate_api_key("openrouter", content)
                    state["openrouter_api_key"].set(content)
                    if is_valid:
                        set_status(state, f"✓ OpenRouter API key pasted and validated")
                    else:
                        set_status(state, f"⚠ OpenRouter API key pasted but {message.lower()}")
                else:
                    set_status(state, "Clipboard is empty")
            else:
                set_status(state, "Clipboard is empty")
        except (pyperclip.PyperclipException, tk.TclError) as e:
            set_status(state, f"Could not access clipboard: {str(e)}")
        except Exception as e:
            set_status(state, f"Unexpected error pasting API key: {str(e)}")

    paste_button = ttk.Button(
        controls_frame,
        text="📋 Paste",
        command=_paste_openrouter_key,
        style="Secondary.TButton"
    )
    paste_button.grid(row=0, column=0, sticky="w")

    openrouter_status_var = tk.StringVar(value="Not configured")
    openrouter_status_label = ttk.Label(
        controls_frame,
        textvariable=openrouter_status_var,
        style="Small.TLabel"
    )
    openrouter_status_label.grid(row=0, column=1, sticky="e")
    state["openrouter_status_label"] = openrouter_status_label

    # Compact features display
    features_frame = ttk.Frame(parent, style="Section.TFrame")
    features_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=(2, 0))

    features_text = "✨ Free models • 🔄 Auto-refresh • 💰 Pay-per-use • 🌐 100+ models"

    features_label = ttk.Label(
        features_frame,
        text=features_text,
        style="Small.TLabel",
        justify="left"
    )
    features_label.grid(row=0, column=0, sticky="w")


def _build_appearance_section(parent, state) -> None:
    """Build the appearance settings section."""
    parent.columnconfigure(0, weight=1)
    appearance_card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    appearance_card.grid(row=0, column=0, sticky="nsew")
    appearance_card.columnconfigure(0, weight=1)

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
    proxy_card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    proxy_card.grid(row=0, column=0, sticky="nsew")
    proxy_card.columnconfigure(0, weight=1)

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
    maintenance_card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    maintenance_card.grid(row=0, column=0, sticky="nsew")
    maintenance_card.columnconfigure(0, weight=1)

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
