"""UI construction helpers with improved organization and visual hierarchy."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

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
from ._shared import _create_section_header
from .dialogs.about import show_about
from .dialogs.settings import open_settings_dialog
from .dialogs.prompt_editor import open_prompt_editor
from .ui_toolkit import (
    PlaceholderEntry,
    update_summary,
    update_model_pricing,
    update_prompt_preview,
    _apply_proxy_preferences,
    _update_provider_status_labels,
    _format_proxy_mapping,
    _select_input,
    update_global_stats_label,
    refresh_recent_input_menu,
    open_folder_location,
    create_tooltip,
)


class _StatusMarquee:
    """Animate long status messages without shifting adjacent controls."""

    def __init__(self, root: tk.Misc, source_var: tk.StringVar, label: ttk.Label) -> None:
        self._root = root
        self._source_var = source_var
        self._label = label
        self._display_var = tk.StringVar(value=source_var.get())
        self._label.configure(textvariable=self._display_var, anchor="w")
        self._font = self._resolve_font()
        self._marquee_text: str = ""
        self._scroll_text: str = ""
        self._offset = 0
        self._after_id: str | None = None
        self._label_width = 0

        source_var.trace_add("write", self._on_source_change)
        self._label.bind("<Configure>", self._on_label_configure)
        self._apply_text(source_var.get())

    def _resolve_font(self) -> tkfont.Font:
        name = self._label.cget("font")
        try:
            return tkfont.nametofont(name)
        except Exception:
            return tkfont.nametofont("TkDefaultFont")

    def _on_source_change(self, *_args: object) -> None:
        self._apply_text(self._source_var.get())

    def _on_label_configure(self, _event: tk.Event) -> None:  # type: ignore[override]
        self._font = self._resolve_font()
        width = self._label.winfo_width()
        if width != self._label_width:
            self._label_width = width
            self._evaluate()

    def _apply_text(self, text: str) -> None:
        self._marquee_text = text or ""
        self._scroll_text = ""
        self._offset = 0
        self._evaluate()

    def _evaluate(self) -> None:
        self._stop_animation()
        if not self._marquee_text:
            self._display_var.set("")
            return

        if self._label_width <= 1:
            self._root.after(60, self._evaluate)
            return

        text_width = self._font.measure(self._marquee_text)
        if text_width <= self._label_width:
            self._display_var.set(self._marquee_text)
            return

        gap = "   "
        self._scroll_text = f"{self._marquee_text}{gap}"
        self._animate()

    def _animate(self) -> None:
        if not self._scroll_text:
            return
        if self._label_width <= 1:
            self._after_id = self._root.after(80, self._animate)
            return

        slice_text = self._build_slice()
        self._display_var.set(slice_text)
        self._offset = (self._offset + 1) % len(self._scroll_text)
        self._after_id = self._root.after(120, self._animate)

    def _build_slice(self) -> str:
        length = len(self._scroll_text)
        if length == 0:
            return ""

        chars: list[str] = []
        width = 0
        idx = self._offset
        limit = length * 2  # prevent runaway loops if measurement misbehaves
        while width < self._label_width and limit > 0:
            chars.append(self._scroll_text[idx % length])
            width = self._font.measure("".join(chars))
            idx += 1
            limit -= 1
        return "".join(chars)

    def _stop_animation(self) -> None:
        if self._after_id is not None:
            try:
                self._root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None


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
    root.config(menu=menubar)

    file_menu_items = [
        ("Settings", lambda: open_settings_dialog(state), "Ctrl+,"),
        ("Exit", root.destroy, "Alt+F4"),
    ]
    help_menu_items = [
        ("About", lambda: show_about(state), "F1"),
    ]

    def _open_popup_menu(button: tk.Widget, items, event=None):
        menu = tk.Menu(button, tearoff=False)
        for label, command, accelerator in items:
            kwargs = {"label": label, "command": command}
            if accelerator:
                kwargs["accelerator"] = accelerator
            menu.add_command(**kwargs)
        if event is not None:
            x, y = event.x_root, event.y_root
        else:
            x = button.winfo_rootx()
            y = button.winfo_rooty() + button.winfo_height()
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    file_button = ttk.Button(menu_frame, text="File", style="ChromeMenu.TButton", takefocus=True)
    file_button.grid(row=0, column=0, padx=(0, 6))
    file_button.configure(command=lambda: _open_popup_menu(file_button, file_menu_items))
    file_button["underline"] = 0

    help_button = ttk.Button(menu_frame, text="Help", style="ChromeMenu.TButton", takefocus=True)
    help_button.grid(row=0, column=1, padx=(0, 0))
    help_button.configure(command=lambda: _open_popup_menu(help_button, help_menu_items))
    help_button["underline"] = 0

    def _open_file_menu_event(event):
        _open_popup_menu(file_button, file_menu_items, event)
        return "break"

    def _open_help_menu_event(event):
        _open_popup_menu(help_button, help_menu_items, event)
        return "break"

    file_button.bind("<Button-1>", _open_file_menu_event)
    help_button.bind("<Button-1>", _open_help_menu_event)

    def _open_file_menu_from_key(event):
        _open_popup_menu(file_button, file_menu_items)
        return "break"

    def _open_help_menu_from_key(event):
        _open_popup_menu(help_button, help_menu_items)
        return "break"

    file_button.bind("<KeyPress-Down>", _open_file_menu_from_key)
    help_button.bind("<KeyPress-Down>", _open_help_menu_from_key)

    def _activate_file_menu(event):
        file_button.focus_set()
        _open_popup_menu(file_button, file_menu_items)
        return "break"

    def _activate_help_menu(event):
        help_button.focus_set()
        _open_popup_menu(help_button, help_menu_items)
        return "break"

    root.bind_all("<Alt-f>", _activate_file_menu)
    root.bind_all("<Alt-F>", _activate_file_menu)
    root.bind_all("<Alt-h>", _activate_help_menu)
    root.bind_all("<Alt-H>", _activate_help_menu)

    def _open_settings(event=None):
        open_settings_dialog(state)
        return "break"

    def _open_about(event=None):
        show_about(state)
        return "break"

    root.bind_all("<Control-comma>", _open_settings)
    root.bind_all("<F1>", _open_about)

    ttk.Separator(main_container, orient="horizontal").grid(row=1, column=0, sticky="ew")

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
        "auto_open_results": tk.BooleanVar(value=user_config.get("auto_open_results", False)),
        "recent_input_paths": list(user_config.get("recent_input_paths", [])),
        "summary_chip_model_var": tk.StringVar(value="Model"),
        "summary_chip_prompt_var": tk.StringVar(value="Prompt"),
        "summary_chip_output_var": tk.StringVar(value="Output"),
        "summary_chip_alttext_var": tk.StringVar(value="Alt text"),
        "auto_clear_input": tk.BooleanVar(value=user_config.get("auto_clear_input", False)),
        "status_width_pixels": 360,
        "status_height_pixels": 28,
        "status_idle_default": "Ready",
        "_status_after_id": None,
    }

    # Backward compatibility: some processors expect include_subdirectories
    state["include_subdirectories"] = state["recursive_search"]

    state["global_images_count"] = tk.IntVar(value=user_config.get("global_images_count", 0))
    state["global_images_label"] = tk.StringVar()
    update_global_stats_label(state)
    state["global_images_count"].trace_add("write", lambda *_: update_global_stats_label(state))

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
    tab_workflow = ttk.Frame(notebook, padding=0)
    tab_configuration = ttk.Frame(notebook, padding=0)
    tab_log = ttk.Frame(notebook, padding=0)

    notebook.add(tab_workflow, text="Workflow")
    notebook.add(tab_configuration, text="Prompts & Models")
    notebook.add(tab_log, text="Activity Log")

    state["tab_workflow"] = tab_workflow
    state["tab_configuration"] = tab_configuration
    state["tab_log"] = tab_log

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
        if is_custom:
            state["custom_output_label"].grid()
            state["custom_output_entry"].grid()
            state["custom_output_browse_button"].grid()
        else:
            state["custom_output_label"].grid_remove()
            state["custom_output_entry"].grid_remove()
            state["custom_output_browse_button"].grid_remove()
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

    # Input path selection
    input_frame = ttk.Frame(input_card, style="Section.TFrame")
    input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
    input_frame.columnconfigure(0, weight=1)

    entry = PlaceholderEntry(
        input_frame,
        textvariable=state["input_path"],
        placeholder="Drop files/folders here or browse...",
        width=50,
    )
    entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    state["input_entry"] = entry
    state["input_entry_tooltip"] = create_tooltip(
        entry,
        "Drop folders here or click Browse to choose where images will be read from.",
    )

    browse_button = ttk.Button(input_frame, text="Browse...", command=lambda: _select_input(state), style="TButton")
    browse_button.grid(row=0, column=1)
    state["browse_button"] = browse_button
    state["browse_button_tooltip"] = create_tooltip(
        browse_button,
        "Open a file dialog to pick an input folder or image set.",
    )

    recent_button = ttk.Menubutton(input_frame, text="Recent folders", direction="below", style="ChromeMenu.TButton")
    recent_button.grid(row=1, column=0, sticky="w", pady=(8, 0))
    recent_menu = tk.Menu(recent_button, tearoff=False)
    recent_button["menu"] = recent_menu
    state["recent_input_button"] = recent_button
    state["recent_input_menu"] = recent_menu
    state["recent_button_tooltip"] = create_tooltip(
        recent_button,
        "Quickly reopen one of your recently processed folders.",
    )

    open_folder_button = ttk.Button(
        input_frame,
        text="Open folder",
        command=lambda: open_folder_location(state, state["input_path"].get()),
        style="Secondary.TButton",
    )
    open_folder_button.grid(row=1, column=1, sticky="w", pady=(8, 0))
    state["open_folder_button"] = open_folder_button
    state["open_folder_button_tooltip"] = create_tooltip(
        open_folder_button,
        "Open the currently selected input folder in your file browser.",
    )

    # Options row
    options_frame = ttk.Frame(input_card, style="Section.TFrame")
    options_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
    options_frame.columnconfigure(0, weight=0)
    options_frame.columnconfigure(1, weight=0)
    options_frame.columnconfigure(2, weight=1)

    recursive_checkbox = ttk.Checkbutton(options_frame, text="Include subdirectories", variable=state["recursive_search"])
    recursive_checkbox.grid(row=0, column=0, sticky="w")
    state["recursive_checkbox"] = recursive_checkbox
    state["recursive_checkbox_tooltip"] = create_tooltip(
        recursive_checkbox,
        "When enabled, Altomatic will scan nested folders for images as well.",
    )

    auto_clear_toggle = ttk.Checkbutton(
        options_frame,
        text="Auto clear input after processing",
        variable=state["auto_clear_input"],
        style="Small.TCheckbutton",
    )
    auto_clear_toggle.grid(row=0, column=1, sticky="w", padx=(16, 0))
    state["auto_clear_toggle"] = auto_clear_toggle
    state["auto_clear_tooltip"] = create_tooltip(
        auto_clear_toggle,
        "When enabled, Altomatic will empty the input path once processing finishes.",
    )

    image_count_label = ttk.Label(options_frame, textvariable=state["image_count"], style="Small.TLabel")
    image_count_label.grid(row=0, column=2, sticky="e")
    state["image_count_label"] = image_count_label
    state["image_count_tooltip"] = create_tooltip(
        image_count_label,
        "Displays how many images were detected in the selected input path.",
    )

    # Summary bar with scrolling support
    summary_frame = ttk.Frame(input_card, style="Section.TFrame")
    summary_frame.grid(row=3, column=0, sticky="ew")
    summary_frame.columnconfigure(0, weight=1)
    state["summary_container"] = summary_frame

    chips_frame = ttk.Frame(summary_frame, style="Section.TFrame")
    chips_frame.grid(row=0, column=0, sticky="w")
    state["summary_chips_frame"] = chips_frame

    summary_chip_model = ttk.Label(
        chips_frame,
        textvariable=state["summary_chip_model_var"],
        style="SummaryChip.TLabel",
        cursor="hand2",
    )
    summary_chip_model.grid(row=0, column=0, padx=(0, 6))
    state["summary_chip_model_widget"] = summary_chip_model
    state["summary_chip_model_tooltip"] = create_tooltip(summary_chip_model, "Model details")

    summary_chip_prompt = ttk.Label(
        chips_frame,
        textvariable=state["summary_chip_prompt_var"],
        style="SummaryChip.TLabel",
        cursor="hand2",
    )
    summary_chip_prompt.grid(row=0, column=1, padx=(0, 6))
    state["summary_chip_prompt_widget"] = summary_chip_prompt
    state["summary_chip_prompt_tooltip"] = create_tooltip(summary_chip_prompt, "Prompt details")

    summary_chip_output = ttk.Label(
        chips_frame,
        textvariable=state["summary_chip_output_var"],
        style="SummaryChip.TLabel",
        cursor="hand2",
    )
    summary_chip_output.grid(row=0, column=2, padx=(0, 6))
    state["summary_chip_output_widget"] = summary_chip_output
    state["summary_chip_output_tooltip"] = create_tooltip(summary_chip_output, "Output details")

    summary_chip_alttext = ttk.Label(
        chips_frame,
        textvariable=state["summary_chip_alttext_var"],
        style="SummaryChip.TLabel",
        cursor="hand2",
    )
    summary_chip_alttext.grid(row=0, column=3)
    state["summary_chip_alttext_widget"] = summary_chip_alttext
    state["summary_chip_alttext_tooltip"] = create_tooltip(summary_chip_alttext, "Alt-text language")

    def _open_prompt_editor_quick() -> None:
        open_prompt_editor(state)

    def _focus_provider_controls() -> None:
        pane = state.get("provider_pane")
        if pane is not None:
            pane.expand()
        widget = state.get("provider_option_widget")
        if widget is not None:
            widget.focus_set()

    def _open_provider_settings() -> None:
        notebook = state.get("notebook")
        tab = state.get("tab_configuration")
        if notebook is not None and tab is not None:
            notebook.select(tab)
        state["root"].after(100, _focus_provider_controls)

    def _open_output_settings() -> None:
        notebook = state.get("notebook")
        workflow_tab = state.get("tab_workflow")
        if notebook is not None and workflow_tab is not None:
            notebook.select(workflow_tab)
        def _expand_output():
            pane = state.get("output_pane")
            if pane is not None:
                pane.expand()
        state["root"].after(100, _expand_output)

    def _open_processing_options() -> None:
        notebook = state.get("notebook")
        workflow_tab = state.get("tab_workflow")
        if notebook is not None and workflow_tab is not None:
            notebook.select(workflow_tab)

        def _expand_processing() -> None:
            pane = state.get("processing_pane")
            if pane is not None:
                pane.expand()

        state["root"].after(100, _expand_processing)

    summary_chip_model.bind("<Button-1>", lambda _e: _open_provider_settings(), add="+")
    summary_chip_model.bind("<Enter>", lambda _e, w=summary_chip_model: w.state(["active"]), add="+")
    summary_chip_model.bind("<Leave>", lambda _e, w=summary_chip_model: w.state(["!active"]), add="+")
    summary_chip_prompt.bind("<Button-1>", lambda _e: _open_prompt_editor_quick(), add="+")
    summary_chip_prompt.bind("<Enter>", lambda _e, w=summary_chip_prompt: w.state(["active"]), add="+")
    summary_chip_prompt.bind("<Leave>", lambda _e, w=summary_chip_prompt: w.state(["!active"]), add="+")
    summary_chip_output.bind("<Button-1>", lambda _e: _open_output_settings(), add="+")
    summary_chip_output.bind("<Enter>", lambda _e, w=summary_chip_output: w.state(["active"]), add="+")
    summary_chip_output.bind("<Leave>", lambda _e, w=summary_chip_output: w.state(["!active"]), add="+")
    summary_chip_alttext.bind("<Button-1>", lambda _e: _open_processing_options(), add="+")
    summary_chip_alttext.bind("<Enter>", lambda _e, w=summary_chip_alttext: w.state(["active"]), add="+")
    summary_chip_alttext.bind("<Leave>", lambda _e, w=summary_chip_alttext: w.state(["!active"]), add="+")

    refresh_recent_input_menu(state)


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
    footer.columnconfigure(0, weight=1)
    footer.columnconfigure(1, weight=1)

    status_stack = ttk.Frame(footer, style="TFrame")
    status_stack.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
    status_stack.columnconfigure(0, weight=1)

    status_width = state.get("status_width_pixels") or 360
    status_height = state.get("status_height_pixels") or 28
    status_label_frame = ttk.Frame(status_stack, style="TFrame", width=status_width, height=status_height)
    status_label_frame.grid(row=0, column=0, sticky="w")
    status_label_frame.grid_propagate(False)
    status_label_frame.columnconfigure(0, weight=1)

    state["status_label"] = ttk.Label(status_label_frame, style="Status.TLabel")
    state["status_label"].grid(row=0, column=0, sticky="ew")
    state["status_marquee"] = _StatusMarquee(state["root"], state["status_var"], state["status_label"])

    state["progress_bar"] = ttk.Progressbar(status_stack, mode="determinate")
    state["progress_bar"].grid(row=1, column=0, sticky="ew", pady=(4, 0))

    actions_frame = ttk.Frame(footer, style="TFrame")
    actions_frame.grid(row=0, column=1, sticky="e")

    state["process_button"] = ttk.Button(actions_frame, text="Describe Images", style="Accent.TButton")
    state["process_button"].grid(row=0, column=0, sticky="e", padx=(0, 16))
    state["process_button_tooltip"] = create_tooltip(
        state["process_button"],
        "Start describing the images in the selected folder using the current settings.",
    )

    state["lbl_token_usage"] = ttk.Label(actions_frame, text="Tokens: 0", style="Status.TLabel")
    state["lbl_token_usage"].grid(row=0, column=1, sticky="e")
    state["token_usage_tooltip"] = create_tooltip(
        state["lbl_token_usage"],
        "Shows the cumulative tokens consumed during this session.",
    )


def _build_menus(menubar, root, state) -> None:
    """Build the menu bar."""
    file_menu = tk.Menu(menubar, tearoff=False)
    file_menu.add_command(label="Settings", accelerator="Ctrl+,", command=lambda: open_settings_dialog(state))
    file_menu.add_command(label="Exit", command=root.destroy)
    menubar.add_cascade(label="File", menu=file_menu)

    help_menu = tk.Menu(menubar, tearoff=False)
    help_menu.add_command(label="About", accelerator="F1", command=lambda: show_about(state))
    menubar.add_cascade(label="Help", menu=help_menu)
