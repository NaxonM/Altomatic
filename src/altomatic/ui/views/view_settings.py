from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models import (
    AVAILABLE_PROVIDERS,
    get_models_for_provider,
    get_provider_label,
    refresh_openrouter_models,
    get_default_model,
)
from ..ui_toolkit import (
    CollapsiblePane,
    ScrollableFrame,
    _create_info_label,
    create_tooltip,
    set_status,
    update_model_pricing,
    update_prompt_preview,
    update_summary,
    validate_api_key,
    initialize_provider_ui,
    append_monitor_colored,
    pyperclip,
    refresh_prompt_choices,
    test_provider_connection,
)
from ..dialogs.prompt_editor import open_prompt_editor
from ...services.providers.exceptions import APIError, AuthenticationError, NetworkError


STATUS_SUCCESS_TIMEOUT = 5000
STATUS_WARNING_TIMEOUT = 7000


def build_tab_configuration(frame, state) -> None:
    """Build the consolidated configuration tab."""
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    # Create scrollable container
    scrollable = ScrollableFrame(frame)
    scrollable.grid(row=0, column=0, sticky="nsew")

    container = scrollable.scrollable_frame
    container.columnconfigure(0, weight=1)

    # Create accordion group for all collapsible panes
    accordion_group = []

    # AI Provider & Model
    pane1 = CollapsiblePane(
        container, text="🤖 AI Provider & Model", accordion_group=accordion_group, scroll_canvas=scrollable.canvas
    )
    pane1.grid(row=0, column=0, sticky="ew", pady=(0, 16))
    accordion_group.append(pane1)
    state["provider_pane"] = pane1
    _build_llm_provider_section(pane1.frame, state)

    # Prompt Management
    pane2 = CollapsiblePane(
        container, text="✍️ Prompt Management", accordion_group=accordion_group, scroll_canvas=scrollable.canvas
    )
    pane2.grid(row=1, column=0, sticky="ew", pady=(0, 16))
    accordion_group.append(pane2)
    state["prompt_pane"] = pane2
    _build_prompt_management_section(pane2.frame, state)


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

    ttk.Label(selection_frame, text="Active preset:", style="TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))

    display_map = state.get("prompt_display_map") or {
        key: entry.get("label") or key for key, entry in state["prompts"].items()
    }
    current_prompt_key = state["prompt_key"].get()
    prompt_label_var = tk.StringVar(value=display_map.get(current_prompt_key, current_prompt_key))
    state["prompt_label_var"] = prompt_label_var

    def on_prompt_select(label):
        current_map = state.get("prompt_display_map") or display_map
        for key, display in current_map.items():
            if display == label:
                state["prompt_key"].set(key)
                prompt_label_var.set(display)
                update_prompt_preview(state)
                update_summary(state)
                break

    prompt_menu = ttk.OptionMenu(
        selection_frame,
        prompt_label_var,
        prompt_label_var.get(),
        *display_map.values(),
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

    _create_info_label(prompt_card, "Use the editor to create custom prompts or modify existing presets.").grid(
        row=3, column=0, sticky="w", pady=(12, 0)
    )

    refresh_prompt_choices(state)


def _build_llm_provider_section(parent, state) -> None:
    """Build the redesigned LLM provider section with original show/hide behavior."""
    parent.columnconfigure(0, weight=1)

    # Main container with compact padding
    main_container = ttk.Frame(parent, style="Card.TFrame", padding=16)
    main_container.grid(row=0, column=0, sticky="nsew")
    main_container.columnconfigure(0, weight=1)

    # --- Provider Selection ---
    provider_select_frame = ttk.Frame(main_container, style="Section.TFrame")
    provider_select_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    provider_select_frame.columnconfigure(1, weight=1)

    ttk.Label(provider_select_frame, text="Provider:", style="TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))

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
    state["provider_option_widget"] = provider_menu
    state["provider_option_menu"] = provider_menu["menu"]
    state["provider_option_tooltip"] = create_tooltip(
        provider_menu,
        "Choose which AI provider Altomatic should use for descriptions.",
    )

    # Provider status
    provider_status_var = tk.StringVar(value="● Ready")
    provider_status_label = ttk.Label(provider_select_frame, textvariable=provider_status_var, style="Small.TLabel")
    provider_status_label.grid(row=0, column=2, sticky="e", padx=(16, 0))
    state["provider_status_label"] = provider_status_label
    state["provider_status_var"] = provider_status_var
    state["provider_status_tooltip"] = create_tooltip(
        provider_status_label,
        "Shows whether the selected provider is configured with an API key.",
    )

    # --- Model Selection ---
    model_select_frame = ttk.Frame(main_container, style="Section.TFrame")
    model_select_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
    model_select_frame.columnconfigure(1, weight=1)

    ttk.Label(model_select_frame, text="Model:", style="TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))

    model_label_var = tk.StringVar()
    state["model_label_var"] = model_label_var

    model_menu = ttk.OptionMenu(model_select_frame, model_label_var, "")
    model_menu.grid(row=0, column=1, sticky="w")
    state["model_option_widget"] = model_menu
    state["model_option_menu"] = model_menu["menu"]
    state["model_option_tooltip"] = create_tooltip(
        model_menu,
        "Pick the primary model used for image descriptions.",
    )

    def _refresh_openrouter_models_ui() -> None:
        try:
            set_status(state, "Refreshing OpenRouter models...", persist=False)
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
            set_status(state, f"✓ Refreshed {model_count} OpenRouter models", duration_ms=STATUS_SUCCESS_TIMEOUT)

        except Exception as exc:
            error_msg = f"Could not refresh OpenRouter models: {str(exc)}"
            set_status(state, error_msg)
            append_monitor_colored(state, error_msg, "error")

    refresh_button = ttk.Button(
        model_select_frame, text="⟳ Refresh", command=_refresh_openrouter_models_ui, style="Secondary.TButton"
    )
    refresh_button.grid(row=0, column=2, sticky="e", padx=(16, 0))
    state["refresh_openrouter_button"] = refresh_button
    state["refresh_openrouter_tooltip"] = create_tooltip(
        refresh_button,
        "Fetch the latest list of models available from OpenRouter.",
    )

    # Model information display
    model_info_frame = ttk.Frame(main_container, style="Section.TFrame")
    model_info_frame.grid(row=2, column=0, sticky="ew", pady=(4, 12))
    model_info_frame.columnconfigure(0, weight=1)

    state["lbl_model_pricing"] = ttk.Label(
        model_info_frame,
        text="Select a model to view pricing and capabilities",
        justify="left",
        style="Small.TLabel",
        wraplength=600,
    )
    state["lbl_model_pricing"].grid(row=0, column=0, sticky="w")
    state["model_pricing_tooltip"] = create_tooltip(
        state["lbl_model_pricing"],
        "Pricing and capability details update when you change the selected model.",
    )

    capabilities_label = ttk.Label(model_info_frame, text="Capabilities: Vision, Text", style="Small.TLabel")
    capabilities_label.grid(row=1, column=0, sticky="w", pady=(4, 0))
    state["model_capabilities_label"] = capabilities_label
    state["model_capabilities_tooltip"] = create_tooltip(
        capabilities_label,
        "Highlights the major abilities advertised by the selected model.",
    )

    # --- API Keys ---
    # OpenAI section (show/hide based on provider)
    openai_frame = ttk.Frame(main_container, style="Section.TFrame")
    openai_frame.grid(row=3, column=0, sticky="ew", pady=(0, 4))
    openai_frame.columnconfigure(1, weight=1)
    _build_compact_openai_config(openai_frame, state)
    state["openai_section"] = openai_frame

    # OpenRouter section (show/hide based on provider)
    openrouter_frame = ttk.Frame(main_container, style="Section.TFrame")
    openrouter_frame.grid(row=4, column=0, sticky="ew", pady=(0, 4))
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

    provider_label = ttk.Label(header_frame, text="OpenAI", font=("Segoe UI Semibold", 10), foreground="#10a37f")
    provider_label.grid(row=0, column=0, sticky="w")

    # API key input row
    ttk.Label(parent, text="API Key:", style="TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8))

    api_key_entry = ttk.Entry(parent, textvariable=state["openai_api_key"], show="*", width=35)
    api_key_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8))
    state["openai_api_entry"] = api_key_entry
    state["openai_api_entry_tooltip"] = create_tooltip(
        api_key_entry,
        "Enter your OpenAI API key. It stays hidden unless you reveal it.",
    )

    show_key_var = tk.BooleanVar()

    def _toggle_openai_key() -> None:
        api_key_entry.config(show="" if show_key_var.get() else "*")

    show_key_cb = ttk.Checkbutton(
        parent, text="Show", variable=show_key_var, command=_toggle_openai_key, style="Small.TCheckbutton"
    )
    show_key_cb.grid(row=1, column=2, sticky="w")
    state["openai_show_key_tooltip"] = create_tooltip(
        show_key_cb,
        "Temporarily reveal the API key text while the box is checked.",
    )

    # Controls in same row
    controls_frame = ttk.Frame(parent, style="Section.TFrame")
    controls_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(4, 0))
    controls_frame.columnconfigure(1, weight=1)

    def _test_openai_key() -> None:
        try:
            set_status(state, "Testing OpenAI connection…", persist=False)
            result = test_provider_connection(state, "openai")
        except AuthenticationError as exc:
            message = f"OpenAI authentication failed: {exc}"
            openai_status_var.set(f"⚠ {exc}")
            openai_status_label.config(foreground="#dc2626")
            set_status(state, f"⚠ {message}", duration_ms=STATUS_WARNING_TIMEOUT)
            append_monitor_colored(state, message, "error")
        except NetworkError as exc:
            message = f"OpenAI network error: {exc}"
            openai_status_var.set(f"⚠ {exc}")
            openai_status_label.config(foreground="#d97706")
            set_status(state, f"⚠ {message}", duration_ms=STATUS_WARNING_TIMEOUT)
            append_monitor_colored(state, message, "warn")
        except APIError as exc:
            message = f"OpenAI API error: {exc}"
            openai_status_var.set(f"⚠ {exc}")
            openai_status_label.config(foreground="#d97706")
            set_status(state, f"⚠ {message}", duration_ms=STATUS_WARNING_TIMEOUT)
            append_monitor_colored(state, message, "warn")
        except Exception as exc:
            message = f"Unexpected OpenAI test failure: {exc}".strip()
            openai_status_var.set("⚠ Unexpected error")
            openai_status_label.config(foreground="#d97706")
            set_status(state, f"⚠ {message}", duration_ms=STATUS_WARNING_TIMEOUT)
            append_monitor_colored(state, message, "error")
        else:
            message = result.get("message", "OpenAI connection verified")
            count = result.get("count")
            if isinstance(count, int) and count:
                message = f"{message} ({count} model{'s' if count != 1 else ''} visible)"
            openai_status_var.set(f"✓ {message}")
            openai_status_label.config(foreground="#059669")
            set_status(state, f"✓ {message}", duration_ms=STATUS_SUCCESS_TIMEOUT)
            append_monitor_colored(state, f"[OpenAI Test] {message}", "info")

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
                        set_status(state, "✓ OpenAI API key pasted and validated")
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

    paste_button = ttk.Button(controls_frame, text="📋 Paste", command=_paste_openai_key, style="Secondary.TButton")
    paste_button.grid(row=0, column=0, sticky="w")
    state["openai_paste_tooltip"] = create_tooltip(
        paste_button,
        "Paste an API key directly from your clipboard.",
    )

    openai_status_var = tk.StringVar(value="Not configured")
    openai_status_label = ttk.Label(controls_frame, textvariable=openai_status_var, style="Small.TLabel")
    openai_status_label.grid(row=0, column=1, sticky="e")
    state["openai_status_label"] = openai_status_label
    state["openai_status_var"] = openai_status_var
    state["openai_status_tooltip"] = create_tooltip(
        openai_status_label,
        "Latest connection check result for OpenAI.",
    )

    test_button = ttk.Button(controls_frame, text="🔌 Test", command=_test_openai_key, style="Secondary.TButton")
    test_button.grid(row=0, column=2, sticky="e", padx=(8, 0))
    state["openai_test_tooltip"] = create_tooltip(
        test_button,
        "Verify that your OpenAI credentials are valid.",
    )


def _build_compact_openrouter_config(parent, state) -> None:
    """Build compact OpenRouter configuration section."""
    parent.columnconfigure(1, weight=1)

    # Header and API key in one row
    header_frame = ttk.Frame(parent, style="TFrame")
    header_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
    header_frame.columnconfigure(0, weight=1)

    provider_label = ttk.Label(header_frame, text="OpenRouter", font=("Segoe UI Semibold", 10), foreground="#ff6b35")
    provider_label.grid(row=0, column=0, sticky="w")

    # API key input row
    ttk.Label(parent, text="API Key:", style="TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8))

    api_key_entry = ttk.Entry(parent, textvariable=state["openrouter_api_key"], show="*", width=35)
    api_key_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8))
    state["openrouter_api_entry"] = api_key_entry
    state["openrouter_api_entry_tooltip"] = create_tooltip(
        api_key_entry,
        "Enter your OpenRouter API key. Keep it private unless you need to view it.",
    )

    show_key_var = tk.BooleanVar()

    def _toggle_openrouter_key() -> None:
        api_key_entry.config(show="" if show_key_var.get() else "*")

    show_key_cb = ttk.Checkbutton(
        parent, text="Show", variable=show_key_var, command=_toggle_openrouter_key, style="Small.TCheckbutton"
    )
    show_key_cb.grid(row=1, column=2, sticky="w")
    state["openrouter_show_key_tooltip"] = create_tooltip(
        show_key_cb,
        "Hold to reveal the OpenRouter key while checked.",
    )

    # Controls in same row
    controls_frame = ttk.Frame(parent, style="Section.TFrame")
    controls_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(4, 0))
    controls_frame.columnconfigure(1, weight=1)

    def _test_openrouter_key() -> None:
        try:
            set_status(state, "Testing OpenRouter connection…", persist=False)
            result = test_provider_connection(state, "openrouter")
        except AuthenticationError as exc:
            message = f"OpenRouter authentication failed: {exc}"
            openrouter_status_var.set(f"⚠ {exc}")
            openrouter_status_label.config(foreground="#dc2626")
            set_status(state, f"⚠ {message}", duration_ms=STATUS_WARNING_TIMEOUT)
            append_monitor_colored(state, message, "error")
        except NetworkError as exc:
            message = f"OpenRouter network error: {exc}"
            openrouter_status_var.set(f"⚠ {exc}")
            openrouter_status_label.config(foreground="#d97706")
            set_status(state, f"⚠ {message}", duration_ms=STATUS_WARNING_TIMEOUT)
            append_monitor_colored(state, message, "warn")
        except APIError as exc:
            message = f"OpenRouter API error: {exc}"
            openrouter_status_var.set(f"⚠ {exc}")
            openrouter_status_label.config(foreground="#d97706")
            set_status(state, f"⚠ {message}", duration_ms=STATUS_WARNING_TIMEOUT)
            append_monitor_colored(state, message, "warn")
        except Exception as exc:
            message = f"Unexpected OpenRouter test failure: {exc}".strip()
            openrouter_status_var.set("⚠ Unexpected error")
            openrouter_status_label.config(foreground="#d97706")
            set_status(state, f"⚠ {message}", duration_ms=STATUS_WARNING_TIMEOUT)
            append_monitor_colored(state, message, "error")
        else:
            message = result.get("message", "OpenRouter connection verified")
            quota = result.get("quota")
            if isinstance(quota, dict):
                remaining = quota.get("remaining")
                if remaining is not None:
                    message = f"{message} (remaining: {remaining})"
            openrouter_status_var.set(f"✓ {message}")
            openrouter_status_label.config(foreground="#059669")
            set_status(state, f"✓ {message}", duration_ms=STATUS_SUCCESS_TIMEOUT)
            append_monitor_colored(state, f"[OpenRouter Test] {message}", "info")

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
                        set_status(state, "✓ OpenRouter API key pasted and validated")
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

    paste_button = ttk.Button(controls_frame, text="📋 Paste", command=_paste_openrouter_key, style="Secondary.TButton")
    paste_button.grid(row=0, column=0, sticky="w")
    state["openrouter_paste_tooltip"] = create_tooltip(
        paste_button,
        "Paste an OpenRouter API key from your clipboard.",
    )

    openrouter_status_var = tk.StringVar(value="Not configured")
    openrouter_status_label = ttk.Label(controls_frame, textvariable=openrouter_status_var, style="Small.TLabel")
    openrouter_status_label.grid(row=0, column=1, sticky="e")
    state["openrouter_status_label"] = openrouter_status_label
    state["openrouter_status_var"] = openrouter_status_var
    state["openrouter_status_tooltip"] = create_tooltip(
        openrouter_status_label,
        "Latest connection check result for OpenRouter.",
    )

    test_button = ttk.Button(controls_frame, text="🔌 Test", command=_test_openrouter_key, style="Secondary.TButton")
    test_button.grid(row=0, column=2, sticky="e", padx=(8, 0))
    state["openrouter_test_tooltip"] = create_tooltip(
        test_button,
        "Verify that your OpenRouter credentials are working.",
    )

    # Compact features display
    features_frame = ttk.Frame(parent, style="Section.TFrame")
    features_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=(2, 0))

    features_text = "✨ Free models • 🔄 Auto-refresh • 💰 Pay-per-use • 🌐 100+ models"

    features_label = ttk.Label(features_frame, text=features_text, style="Small.TLabel", justify="left")
    features_label.grid(row=0, column=0, sticky="w")
