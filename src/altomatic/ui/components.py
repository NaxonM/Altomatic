"""UI construction helpers with improved organization and visual hierarchy."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..models import (
    AVAILABLE_PROVIDERS,
    DEFAULT_MODELS,
    DEFAULT_PROVIDER,
    get_default_model,
    get_models_for_provider,
)
from ..prompts import load_prompts
from ..utils import (
    detect_system_proxies,
    get_requests_proxies,
)
from .themes import apply_theme
from ._shared import _create_section_header, _create_info_label
from .dialogs.about import show_about
from .ui_toolkit import (
    AnimatedLabel,
    update_summary,
    update_model_pricing,
    update_prompt_preview,
    _apply_proxy_preferences,
    _update_provider_status_labels,
    _format_proxy_mapping,
    _select_input,
)


def build_ui(root, user_config):
    """Build the main UI with improved layout and organization."""
    # Main container
    main_container = ttk.Frame(root, padding=0)
    main_container.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # Chrome bar (top menu area)
    chrome_bar = ttk.Frame(main_container, style="Chrome.TFrame", padding=(20, 12))
    chrome_bar.grid(row=0, column=0, sticky="ew")
    chrome_bar.columnconfigure(0, weight=1)

    title_label = ttk.Label(chrome_bar, text="Altomatic", style="ChromeTitle.TLabel")
    title_label.grid(row=0, column=0, sticky="w")

    menu_frame = ttk.Frame(chrome_bar, style="Chrome.TFrame")
    menu_frame.grid(row=0, column=1, sticky="e")

    menubar = tk.Menu(root, tearoff=False)
    root.config(menu="")

    def _popup_menu(items, event):
        menu = tk.Menu(menu_frame, tearoff=False)
        for label, command in items:
            menu.add_command(label=label, command=command)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _on_file(event):
        _popup_menu([("Exit", root.destroy)], event)

    def _on_help(event):
        _popup_menu([("About", lambda: show_about(state))], event)

    file_button = ttk.Label(menu_frame, text="File", style="ChromeMenu.TLabel")
    file_button.grid(row=0, column=0, padx=(0, 12))
    file_button.bind("<Button-1>", _on_file)

    help_button = ttk.Label(menu_frame, text="Help", style="ChromeMenu.TLabel")
    help_button.grid(row=0, column=1)
    help_button.bind("<Button-1>", _on_help)

    # Content area with padding between header and input section
    content_frame = ttk.Frame(main_container, padding=(20, 8, 20, 20))
    content_frame.grid(row=1, column=0, sticky="nsew")
    main_container.columnconfigure(0, weight=1)
    main_container.rowconfigure(1, weight=1)

    # Initialize state
    prompts_data = load_prompts()
    prompt_names = list(prompts_data.keys()) or ["default"]
    active_prompt = user_config.get("prompt_key", "default")
    if active_prompt not in prompts_data:
        active_prompt = prompt_names[0]

    provider = user_config.get("llm_provider", DEFAULT_PROVIDER)
    if provider not in AVAILABLE_PROVIDERS:
        provider = DEFAULT_PROVIDER

    provider_model_map = {
        "openai": user_config.get("openai_model", DEFAULT_MODELS["openai"]),
        "openrouter": user_config.get("openrouter_model", get_default_model("openrouter")),
    }

    for key, fallback in (
        ("openai", DEFAULT_MODELS["openai"]),
        ("openrouter", get_default_model("openrouter")),
    ):
        models_for_provider = get_models_for_provider(key)
        value = provider_model_map.get(key)
        if value not in models_for_provider:
            provider_model_map[key] = fallback

    active_model = user_config.get("llm_model") or provider_model_map.get(provider) or get_default_model(provider)
    if active_model not in get_models_for_provider(provider):
        active_model = get_default_model(provider)
    provider_model_map[provider] = active_model

    # Central state dictionary
    state = {
        "root": root,
        "menubar": menubar,
        "input_type": tk.StringVar(value="Folder"),
        "input_path": tk.StringVar(value=""),
        "recursive_search": tk.BooleanVar(value=user_config.get("recursive_search", False)),
        "show_results_table": tk.BooleanVar(value=user_config.get("show_results_table", True)),
        "custom_output_path": tk.StringVar(value=user_config.get("custom_output_path", "")),
        "output_folder_option": tk.StringVar(value=user_config.get("output_folder_option", "Same as input")),
        "openai_api_key": tk.StringVar(value=user_config.get("openai_api_key", "")),
        "openrouter_api_key": tk.StringVar(value=user_config.get("openrouter_api_key", "")),
        "proxy_enabled": tk.BooleanVar(value=user_config.get("proxy_enabled", True)),
        "proxy_override": tk.StringVar(value=user_config.get("proxy_override", "")),
        "filename_language": tk.StringVar(value=user_config.get("filename_language", "English")),
        "alttext_language": tk.StringVar(value=user_config.get("alttext_language", "English")),
        "name_detail_level": tk.StringVar(value=user_config.get("name_detail_level", "Detailed")),
        "vision_detail": tk.StringVar(value=user_config.get("vision_detail", "auto")),
        "ocr_enabled": tk.BooleanVar(value=user_config.get("ocr_enabled", False)),
        "tesseract_path": tk.StringVar(value=user_config.get("tesseract_path", "")),
        "ocr_language": tk.StringVar(value=user_config.get("ocr_language", "eng")),
        "ui_theme": tk.StringVar(value=user_config.get("ui_theme", "Arctic Light")),
        "openai_model": tk.StringVar(value=provider_model_map["openai"]),
        "openrouter_model": tk.StringVar(value=provider_model_map["openrouter"]),
        "llm_provider": tk.StringVar(value=provider),
        "llm_model": tk.StringVar(value=active_model),
        "prompt_key": tk.StringVar(value=active_prompt),
        "context_text": tk.StringVar(value=user_config.get("context_text", "")),
        "status_var": tk.StringVar(value="Ready"),
        "image_count": tk.StringVar(value=""),
        "total_tokens": tk.IntVar(value=0),
        "logs": [],
        "prompts": prompts_data,
        "prompt_names": prompt_names,
        "temp_drop_folder": None,
        "provider_model_map": provider_model_map,
        "_proxy_last_settings": None,
    }

    # Proxy setup
    detected_initial = detect_system_proxies()
    state["proxy_detected_label"] = tk.StringVar(value=_format_proxy_mapping(detected_initial))
    effective_initial = get_requests_proxies(
        enabled=state["proxy_enabled"].get(),
        override=state["proxy_override"].get().strip() or None,
    )
    state["proxy_effective_label"] = tk.StringVar(value=_format_proxy_mapping(effective_initial))
    state["_proxy_last_settings"] = (
        state["proxy_enabled"].get(),
        state["proxy_override"].get().strip(),
    )

    # Build UI sections
    content_frame.rowconfigure(0, weight=0)  # Input card
    content_frame.rowconfigure(1, weight=1)  # Notebook
    content_frame.rowconfigure(2, weight=0)  # Footer
    content_frame.columnconfigure(0, weight=1)

    _build_input_card(content_frame, state)
    notebook = _build_main_notebook(content_frame, state)
    _build_footer(content_frame, state)

    # Build tabs
    tab_workflow = ttk.Frame(notebook, padding=(0, 16, 0, 0))
    tab_configuration = ttk.Frame(notebook, padding=(0, 16, 0, 0))
    tab_log = ttk.Frame(notebook, padding=(0, 16, 0, 0))

    notebook.add(tab_workflow, text="Workflow")
    notebook.add(tab_configuration, text="Configuration")
    notebook.add(tab_log, text="Activity Log")

    from .views.view_workflow import build_tab_workflow
    from .views.view_settings import build_tab_configuration
    from .views.view_log import build_log

    build_tab_workflow(tab_workflow, state)
    build_tab_configuration(tab_configuration, state)
    build_log(tab_log, state)

    # Build menus
    _build_menus(menubar, root, state)

    def on_output_folder_change(*args):
        is_custom = state["output_folder_option"].get() == "Custom"
        state["custom_output_entry"].config(state="normal" if is_custom else "disabled")
        update_summary(state)

    def on_model_change(*_):
        provider_key = state["llm_provider"].get()
        current_model = state["llm_model"].get()
        state["provider_model_map"][provider_key] = current_model
        model_var_key = f"{provider_key}_model"
        if model_var_key in state:
            state[model_var_key].set(current_model)
        update_model_pricing(state)
        update_summary(state)

    def on_provider_change(*_):
        selected = state["llm_provider"].get()
        if selected not in AVAILABLE_PROVIDERS:
            selected = DEFAULT_PROVIDER
            state["llm_provider"].set(selected)
        model_choice = state["provider_model_map"].get(selected) or get_default_model(selected)
        if model_choice not in get_models_for_provider(selected):
            model_choice = get_default_model(selected)
        if state["llm_model"].get() != model_choice:
            state["llm_model"].set(model_choice)
        else:
            on_model_change()

    # Trace additions
    state["llm_model"].trace_add("write", lambda *_: on_model_change())
    state["llm_provider"].trace_add("write", lambda *_: on_provider_change())
    state["prompt_key"].trace_add("write", lambda *_: (update_prompt_preview(state), update_summary(state)))
    state["output_folder_option"].trace_add("write", on_output_folder_change)
    state["custom_output_path"].trace_add("write", lambda *_: update_summary(state))
    state["ui_theme"].trace_add("write", lambda *_, **kwargs: apply_theme(root, state["ui_theme"].get()))
    state["proxy_enabled"].trace_add("write", lambda *_: _apply_proxy_preferences(state))
    state["proxy_override"].trace_add("write", lambda *_: _apply_proxy_preferences(state))
    state["openai_api_key"].trace_add("write", lambda *_: _update_provider_status_labels(state))
    state["openrouter_api_key"].trace_add("write", lambda *_: _update_provider_status_labels(state))

    # Trigger initial state
    on_output_folder_change()
    update_model_pricing(state)
    update_prompt_preview(state)
    update_summary(state)
    _apply_proxy_preferences(state, force=True)
    _update_provider_status_labels(state)

    return state


def _build_input_card(parent, state) -> None:
    """Build the input selection card with drag-and-drop support."""
    input_card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    input_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
    input_card.columnconfigure(0, weight=1)
    state["input_card"] = input_card

    # Header
    header_frame = ttk.Frame(input_card, style="Section.TFrame")
    header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    header_frame.columnconfigure(0, weight=1)
    _create_section_header(header_frame, "Input Selection").grid(row=0, column=0, sticky="w")
    _create_info_label(header_frame, "Drop files or folders here, or use the browse button to select images.").grid(
        row=1, column=0, sticky="w", pady=(4, 0)
    )

    # Input path selection
    input_frame = ttk.Frame(input_card, style="Section.TFrame")
    input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
    input_frame.columnconfigure(0, weight=1)

    entry = ttk.Entry(input_frame, textvariable=state["input_path"], width=50)
    entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    state["input_entry"] = entry
    ttk.Button(input_frame, text="Browse...", command=lambda: _select_input(state), style="TButton").grid(
        row=0, column=1
    )

    # Options row
    options_frame = ttk.Frame(input_card, style="Section.TFrame")
    options_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
    options_frame.columnconfigure(1, weight=1)

    ttk.Checkbutton(options_frame, text="Include subdirectories", variable=state["recursive_search"]).grid(
        row=0, column=0, sticky="w"
    )

    ttk.Label(options_frame, textvariable=state["image_count"], style="Small.TLabel").grid(row=0, column=1, sticky="e")

    # Summary bar with scrolling support
    summary_frame = ttk.Frame(input_card, style="Section.TFrame")
    summary_frame.grid(row=3, column=0, sticky="ew")
    summary_frame.columnconfigure(0, weight=1)

    # Create a single animated label for the summary "train"
    summary_label = AnimatedLabel(summary_frame, style="Small.TLabel")
    summary_label.grid(row=0, column=0, sticky="ew")
    state["summary_label"] = summary_label


def _build_main_notebook(parent, state) -> ttk.Notebook:
    """Build the main tabbed notebook."""
    notebook = ttk.Notebook(parent)
    notebook.grid(row=1, column=0, sticky="nsew", pady=(0, 16))
    state["notebook"] = notebook
    return notebook


def _build_footer(parent, state) -> None:
    """Build the footer with status bar and action buttons."""
    footer = ttk.Frame(parent, style="TFrame")
    footer.grid(row=2, column=0, sticky="ew")
    footer.columnconfigure(1, weight=1)

    # Status label on the far left
    state["status_label"] = ttk.Label(footer, textvariable=state["status_var"], style="Status.TLabel")
    state["status_label"].grid(row=0, column=0, sticky="w", padx=(0, 16))

    # Progress bar in the middle
    state["progress_bar"] = ttk.Progressbar(footer, mode="determinate")
    state["progress_bar"].grid(row=0, column=1, sticky="ew")

    # Action buttons and token usage on the far right
    actions_frame = ttk.Frame(footer, style="TFrame")
    actions_frame.grid(row=0, column=2, sticky="e", padx=(16, 0))

    state["process_button"] = ttk.Button(actions_frame, text="Describe Images", style="Accent.TButton")
    state["process_button"].grid(row=0, column=0, sticky="e", padx=(0, 16))

    state["lbl_token_usage"] = ttk.Label(actions_frame, text="Tokens: 0", style="Status.TLabel")
    state["lbl_token_usage"].grid(row=0, column=1, sticky="e")


def _build_menus(menubar, root, state) -> None:
    """Build the menu bar."""
    file_menu = tk.Menu(menubar, tearoff=False)
    file_menu.add_command(label="Exit", command=root.destroy)
    menubar.add_cascade(label="File", menu=file_menu)

    help_menu = tk.Menu(menubar, tearoff=False)
    help_menu.add_command(label="About", command=lambda: show_about(state))
    menubar.add_cascade(label="Help", menu=help_menu)
