
"""UI construction helpers."""

from __future__ import annotations

import os
import shutil
import tkinter as tk
from importlib import resources
from tkinter import filedialog, messagebox, simpledialog, ttk
import sys

# Add the project root to the Python path for PySide6 imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from PySide6.QtWidgets import QApplication
from src.app.services.settings_service import SettingsService
from src.app.views.about_view import AboutView
from src.app.viewmodels.about_viewmodel import AboutViewModel

try:
    import pyperclip
except ModuleNotFoundError:  # pragma: no cover - optional in frozen build
    pyperclip = None

from ..config import open_config_folder, save_config
from ..models import (
    AVAILABLE_PROVIDERS,
    DEFAULT_MODEL,
    DEFAULT_MODELS,
    DEFAULT_PROVIDER,
    format_pricing,
    get_default_model,
    get_models_for_provider,
    get_provider_label,
    refresh_openrouter_models,
)
from ..prompts import get_prompt_template, load_prompts, save_prompts
from ..utils import (
    configure_global_proxy,
    detect_system_proxies,
    get_image_count_in_folder,
    get_requests_proxies,
    reload_system_proxies,
    set_proxy_preferences,
    slugify,
)
from .themes import PALETTE, apply_theme, apply_theme_to_window


def _scaled_geometry(widget: tk.Misc, base_width: int, base_height: int) -> str:
    widget.update_idletasks()
    screen_w = widget.winfo_screenwidth()
    screen_h = widget.winfo_screenheight()

    min_w = int(screen_w * 0.5)
    max_w = int(screen_w * 0.9)
    min_h = int(screen_h * 0.5)
    max_h = int(screen_h * 0.9)

    width = min(max(base_width, min_w), max_w)
    height = min(max(base_height, min_h), max_h)

    width = max(600, min(width, screen_w - 40))
    height = max(420, min(height, screen_h - 80))

    return f"{width}x{height}"


def _apply_window_icon(window: tk.Misc) -> None:
    try:
        with resources.as_file(
            resources.files("altomatic.resources") / "altomatic_icon.ico"
        ) as icon_path:
            window.iconbitmap(default=str(icon_path))
    except Exception:
        pass


def update_token_label(state) -> None:
    if "lbl_token_usage" in state:
        state["lbl_token_usage"].config(text=f"Tokens used: {state['total_tokens'].get()}")


def update_model_pricing(state) -> None:
    if "lbl_model_pricing" not in state:
        return

    provider_var = state.get("llm_provider")
    provider = provider_var.get() if provider_var is not None else DEFAULT_PROVIDER
    model_var = state.get("llm_model")
    model_id = model_var.get() if model_var is not None else DEFAULT_MODEL

    models = get_models_for_provider(provider)
    details = models.get(model_id)

    if not details:
        state["lbl_model_pricing"].config(text="Model pricing unavailable")
        return

    provider_label = get_provider_label(provider)
    model_label = details.get("label", model_id)
    vendor = details.get("vendor")
    vendor_line = f"\\nVendor: {vendor}" if vendor else ""
    state["lbl_model_pricing"].config(
        text=f"{provider_label} • {model_label}\\n{format_pricing(provider, model_id)}{vendor_line}"
    )


def _format_proxy_mapping(mapping: dict[str, str]) -> str:
    if not mapping:
        return "None"
    lines = [f"{scheme}: {value}" for scheme, value in sorted(mapping.items())]
    return "\\n".join(lines)


def update_summary(state) -> None:
    if "summary_model" not in state:
        return

    provider_var = state.get("llm_provider")
    provider = provider_var.get() if provider_var is not None else DEFAULT_PROVIDER
    model_var = state.get("llm_model")
    model_id = model_var.get() if model_var is not None else DEFAULT_MODEL
    models = get_models_for_provider(provider)
    model_label = models.get(model_id, {}).get("label", model_id)
    state["summary_model"].set(f"{get_provider_label(provider)}: {model_label}")

    prompts = state.get("prompts") or load_prompts()
    prompt_key = state["prompt_key"].get()
    prompt_entry = prompts.get(prompt_key) or prompts.get("default") or next(iter(prompts.values()), {})
    state["summary_prompt"].set(f"Prompt: {prompt_entry.get('label', prompt_key)}")

    destination = state["output_folder_option"].get()
    if destination == "Custom":
        path = state["custom_output_path"].get().strip() or "(not set)"
        state["summary_output"].set(f"Output: Custom → {path}")
    else:
        state["summary_output"].set(f"Output: {destination}")


def set_status(state, message: str) -> None:
    if "status_var" in state:
        state["status_var"].set(message)


def update_summary(state) -> None:
    if "summary_model" not in state:
        return

    provider_var = state.get("llm_provider")
    provider = provider_var.get() if provider_var is not None else DEFAULT_PROVIDER
    model_var = state.get("llm_model")
    model_id = model_var.get() if model_var is not None else DEFAULT_MODEL
    models = get_models_for_provider(provider)
    model_label = models.get(model_id, {}).get("label", model_id)
    state["summary_model"].set(f"{get_provider_label(provider)}: {model_label}")

    prompts = state.get("prompts") or load_prompts()
    prompt_key = state["prompt_key"].get()
    prompt_entry = prompts.get(prompt_key) or prompts.get("default") or next(iter(prompts.values()), {})
    state["summary_prompt"].set(f"Prompt: {prompt_entry.get('label', prompt_key)}")

    destination = state["output_folder_option"].get()
    if destination == "Custom":
        path = state["custom_output_path"].get().strip() or "(not set)"
        state["summary_output"].set(f"Output: Custom → {path}")
    else:
        state["summary_output"].set(f"Output: {destination}")


def update_prompt_preview(state) -> None:
    if "prompt_preview" not in state:
        return
    prompts = state.get("prompts") or load_prompts()
    key = state["prompt_key"].get()
    entry = prompts.get(key)
    if entry is None:
        prompts = load_prompts()
        entry = prompts.get(key) or prompts.get("default") or next(iter(prompts.values()))
        state["prompts"] = prompts
        state["prompt_names"] = list(prompts.keys())
    label = entry.get("label", key)
    template = entry.get("template", "")
    widget = state["prompt_preview"]
    widget.config(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", f"{label}\\n\\n{template}".strip())
    widget.config(state="disabled")


def refresh_prompt_choices(state) -> None:
    prompts = load_prompts()
    state["prompts"] = prompts
    state["prompt_names"] = list(prompts.keys())
    menu = state.get("prompt_option_menu")
    if menu:
        menu.delete(0, "end")
        for key, entry in prompts.items():
            label = entry.get("label", key)
            menu.add_command(label=label, command=lambda value=key: state["prompt_key"].set(value))
    current = state["prompt_key"].get()
    if current not in prompts and prompts:
        state["prompt_key"].set(next(iter(prompts.keys())))
    else:
        state["prompt_key"].set(state["prompt_key"].get())
    update_prompt_preview(state)


def cleanup_temp_drop_folder(state) -> None:
    folder = state.get("temp_drop_folder")
    if folder and os.path.isdir(folder):
        try:
            shutil.rmtree(folder)
        except OSError:
            pass
    state["temp_drop_folder"] = None


def open_prompt_editor(state) -> None:
    root = state.get("root")
    editor = tk.Toplevel(root)
    editor.title("Prompt Editor")
    editor.geometry(_scaled_geometry(editor, 960, 680))
    editor.minsize(720, 540)
    editor.grab_set()
    current_theme = state["ui_theme"].get()
    palette = PALETTE.get(current_theme)
    if palette is None:
        default_theme = next(iter(PALETTE.keys()))
        palette = PALETTE[default_theme]
        current_theme = default_theme
    editor.configure(bg=palette["background"])
    _apply_window_icon(editor)

    prompts = load_prompts()
    working = {key: dict(value) for key, value in prompts.items()}

    container = ttk.Frame(editor, padding=12, style="Section.TFrame")
    container.pack(fill="both", expand=True)
    container.columnconfigure(0, weight=1)
    container.rowconfigure(0, weight=1)

    paned = ttk.Panedwindow(container, orient="horizontal")
    paned.grid(row=0, column=0, sticky="nsew")

    list_panel = ttk.Frame(paned, style="Section.TFrame", padding=8)
    list_panel.columnconfigure(0, weight=1)
    list_panel.rowconfigure(2, weight=1)

    ttk.Label(list_panel, text="Available prompts", style="Subheading.TLabel").grid(row=0, column=0, sticky="w")

    search_var = tk.StringVar()

    search_entry = ttk.Entry(list_panel, textvariable=search_var)
    search_entry.grid(row=1, column=0, sticky="ew", pady=(4, 6))

    listbox = tk.Listbox(
        list_panel,
        exportselection=False,
        height=12,
        highlightthickness=0,
        relief="flat",
        activestyle="none",
    )
    listbox_scroll = ttk.Scrollbar(list_panel, orient="vertical", command=listbox.yview)
    listbox.grid(row=2, column=0, sticky="nsew")
    listbox_scroll.grid(row=2, column=1, sticky="ns")
    listbox.configure(
        bg=palette["surface"],
        fg=palette["foreground"],
        selectbackground=palette["primary"],
        selectforeground=palette["primary-foreground"],
        highlightbackground=palette["surface-2"],
        highlightcolor=palette["surface-2"],
        yscrollcommand=listbox_scroll.set,
    )

    detail_panel = ttk.Frame(paned, style="Section.TFrame", padding=12)
    detail_panel.columnconfigure(0, weight=1)
    detail_panel.rowconfigure(3, weight=1)

    ttk.Label(detail_panel, text="Prompt label", style="TLabel").grid(row=0, column=0, sticky="w")
    label_var = tk.StringVar()
    label_entry = ttk.Entry(detail_panel, textvariable=label_var)
    label_entry.grid(row=1, column=0, sticky="ew", pady=(0, 8))

    ttk.Label(detail_panel, text="Prompt template", style="TLabel").grid(row=2, column=0, sticky="w")
    template_frame = ttk.Frame(detail_panel, style="Section.TFrame")
    template_frame.grid(row=3, column=0, sticky="nsew")
    template_frame.columnconfigure(0, weight=1)
    template_frame.rowconfigure(0, weight=1)

    template_text = tk.Text(
        template_frame,
        wrap="word",
        relief="flat",
        borderwidth=1,
        highlightthickness=1,
    )
    template_text.grid(row=0, column=0, sticky="nsew")
    template_text.configure(
        bg=palette["surface"],
        fg=palette["foreground"],
        insertbackground=palette["foreground"],
        highlightbackground=palette["surface-2"],
        highlightcolor=palette["surface-2"],
    )

    template_scroll = ttk.Scrollbar(template_frame, orient="vertical", command=template_text.yview)
    template_scroll.grid(row=0, column=1, sticky="ns")
    template_text.configure(yscrollcommand=template_scroll.set)

    template_stats = tk.StringVar(value="0 characters")
    stats_label = ttk.Label(detail_panel, textvariable=template_stats, style="Small.TLabel")
    stats_label.grid(row=4, column=0, sticky="w", pady=(6, 0))

    button_bar = ttk.Frame(detail_panel, style="Section.TFrame")
    button_bar.grid(row=5, column=0, sticky="ew", pady=(12, 0))
    button_bar.columnconfigure(5, weight=1)

    paned.add(list_panel, weight=1)
    paned.add(detail_panel, weight=3)

    current_key = tk.StringVar(value=state["prompt_key"].get())
    visible_keys: list[str] = []

    def update_template_stats() -> None:
        text = template_text.get("1.0", "end-1c")
        template_stats.set(f"{len(text)} characters")

    def refresh_list(select_key: str | None = None) -> None:
        if select_key is None:
            select_key = current_key.get()
        listbox.delete(0, "end")
        visible_keys.clear()
        needle = search_var.get().strip().lower()
        for key, entry in working.items():
            label = entry.get("label", key)
            haystack = f"{label} {key}".lower()
            if needle and needle not in haystack:
                continue
            visible_keys.append(key)
            listbox.insert("end", label)

        if not visible_keys:
            current_key.set("")
            label_var.set("")
            template_text.delete("1.0", "end")
            update_template_stats()
            return

        if select_key not in visible_keys:
            select_key = visible_keys[0]
        index = visible_keys.index(select_key)
        current_key.set(select_key)
        listbox.select_set(index)
        listbox.see(index)
        load_selected()

    def load_selected(event=None) -> None:
        selection = listbox.curselection()
        if not selection or selection[0] >= len(visible_keys):
            return
        key = visible_keys[selection[0]]
        current_key.set(key)
        entry = working.get(key, {})
        label_var.set(entry.get("label", key))
        template_text.delete("1.0", "end")
        template_text.insert("1.0", entry.get("template", ""))
        update_template_stats()

    def add_prompt() -> None:
        name = simpledialog.askstring("New Prompt", "Enter a label for the new prompt:", parent=editor)
        if not name:
            return
        key = slugify(name)
        if not key:
            key = f"prompt{len(working)+1}"
        base_key = key
        suffix = 1
        while key in working:
            suffix += 1
            key = f"{base_key}-{suffix}"
        working[key] = {"label": name.strip(), "template": ""}
        refresh_list(select_key=key)
        label_entry.focus_set()

    def duplicate_prompt(event=None) -> None:
        key = current_key.get()
        if key not in working:
            return
        base_label = working[key].get("label", key)
        new_label = f"{base_label} Copy"
        candidate = slugify(new_label) or f"{key}-copy"
        suffix = 1
        while candidate in working:
            suffix += 1
            candidate = slugify(f"{new_label} {suffix}") or f"{key}-copy-{suffix}"
        working[candidate] = {
            "label": f"{base_label} Copy" if suffix == 1 else f"{base_label} Copy {suffix}",
            "template": working[key].get("template", ""),
        }
        refresh_list(select_key=candidate)

    def delete_prompt(event=None) -> None:
        key = current_key.get()
        if key == "default" or len(working) <= 1:
            messagebox.showinfo("Not allowed", "The default prompt cannot be deleted.", parent=editor)
            return
        if messagebox.askyesno("Delete Prompt", f"Delete prompt '{working[key].get('label', key)}'?", parent=editor):
            working.pop(key, None)
            refresh_list()

    def save_changes(event=None) -> None:
        key = current_key.get()
        if key not in working:
            messagebox.showerror("No selection", "Select a prompt to save.", parent=editor)
            return
        working[key]["label"] = label_var.get().strip() or key
        working[key]["template"] = template_text.get("1.0", "end").strip()
        save_prompts(working)
        refresh_prompt_choices(state)
        state["prompt_key"].set(key)
        set_status(state, f"Prompt '{working[key]['label']}' saved.")
        refresh_list(select_key=key)

    def save_and_close() -> None:
        save_changes()
        editor.destroy()

    ttk.Button(button_bar, text="Add", command=add_prompt, style="Accent.TButton").grid(row=0, column=0, padx=(0, 6))
    ttk.Button(button_bar, text="Duplicate", command=duplicate_prompt, style="TButton").grid(row=0, column=1, padx=(0, 6))
    ttk.Button(button_bar, text="Delete", command=delete_prompt, style="Secondary.TButton").grid(row=0, column=2, padx=(0, 6))
    ttk.Button(button_bar, text="Save", command=save_changes, style="TButton").grid(row=0, column=3, padx=(0, 6))
    ttk.Button(button_bar, text="Save & Close", command=save_and_close, style="Accent.TButton").grid(row=0, column=4, padx=(0, 6))
    ttk.Button(button_bar, text="Close", command=editor.destroy, style="TButton").grid(row=0, column=5)

    def on_search_change(*_args) -> None:
        refresh_list()

    search_entry.bind("<KeyRelease>", on_search_change)
    listbox.bind("<<ListboxSelect>>", load_selected)
    listbox.bind("<Double-Button-1>", lambda *_: template_text.focus_set())

    template_text.bind("<KeyRelease>", lambda *_: update_template_stats())

    refresh_list(select_key=current_key.get())
    apply_theme_to_window(editor, current_theme)
    editor.bind("<Control-s>", save_changes)
    editor.bind("<Control-d>", duplicate_prompt)
    listbox.bind("<Delete>", delete_prompt)
    search_entry.focus_set()


def build_ui(root, user_config):
    """Build the main UI and stitch components together."""
    chroma_frame = ttk.Frame(root, padding=(16, 0, 16, 16))
    chroma_frame.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    chrome_bar = ttk.Frame(chroma_frame, style="Chrome.TFrame")
    chrome_bar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    chrome_bar.columnconfigure((0, 1), weight=1)

    title_container = ttk.Frame(chrome_bar, style="Chrome.TFrame")
    title_container.grid(row=0, column=0, sticky="w")
    ttk.Label(title_container, text="Altomatic", style="ChromeTitle.TLabel").pack(side="left")

    menu_container = ttk.Frame(chrome_bar, style="Chrome.TFrame")
    menu_container.grid(row=0, column=1, sticky="e")
    menu_container.columnconfigure((0, 1), weight=0)

    menubar = tk.Menu(root, tearoff=False)
    root.config(menu="")

    def _popup_menu(items, event):
        menu = tk.Menu(menu_container, tearoff=False)
        for label, command in items:
            menu.add_command(label=label, command=command)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _on_file(event):
        _popup_menu([("Exit", root.destroy)], event)

    def _on_help(event):
        _popup_menu([("About", lambda: _show_about(state))], event)

    file_button = ttk.Label(menu_container, text="File", style="ChromeMenu.TLabel")
    file_button.grid(row=0, column=0, padx=(0, 8))
    file_button.bind("<Button-1>", _on_file)

    help_button = ttk.Label(menu_container, text="Help", style="ChromeMenu.TLabel")
    help_button.grid(row=0, column=1)
    help_button.bind("<Button-1>", _on_help)

    main_frame = ttk.Frame(chroma_frame, padding=16)
    main_frame.grid(row=1, column=0, sticky="nsew")
    chroma_frame.columnconfigure(0, weight=1)
    chroma_frame.rowconfigure(1, weight=1)

    # Configure main_frame for a 2-column layout
    main_frame.columnconfigure(0, weight=1, minsize=450)
    main_frame.columnconfigure(1, weight=1, minsize=400)
    main_frame.rowconfigure(0, weight=1)  # Main content row
    main_frame.rowconfigure(1, weight=0)  # Footer row

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

    active_model = (
        user_config.get("llm_model")
        or provider_model_map.get(provider)
        or get_default_model(provider)
    )
    if active_model not in get_models_for_provider(provider):
        active_model = get_default_model(provider)
    provider_model_map[provider] = active_model

    # Central state dictionary, passed around to UI functions
    state = {
        "root": root,
        "menubar": menubar,
        # Config-backed state
        "input_type": tk.StringVar(value="Folder"),
        "input_path": tk.StringVar(value=""),
        "include_subdirectories": tk.BooleanVar(value=user_config.get("include_subdirectories", False)),
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
        "ui_theme": tk.StringVar(value=user_config.get("ui_theme", "Default Light")),
        "openai_model": tk.StringVar(value=provider_model_map["openai"]),
        "openrouter_model": tk.StringVar(value=provider_model_map["openrouter"]),
        "llm_provider": tk.StringVar(value=provider),
        "llm_model": tk.StringVar(value=active_model),
        "prompt_key": tk.StringVar(value=active_prompt),
        "context_text": tk.StringVar(value=user_config.get("context_text", "")),
        # Ephemeral state
        "status_var": tk.StringVar(value="Ready."),
        "image_count": tk.StringVar(value=""),
        "total_tokens": tk.IntVar(value=0),
        "logs": [],
        "prompts": prompts_data,
        "prompt_names": prompt_names,
        "temp_drop_folder": None,
        "provider_model_map": provider_model_map,
        # Summary state
        "summary_model": tk.StringVar(),
        "summary_prompt": tk.StringVar(),
        "summary_output": tk.StringVar(),
        "_proxy_last_settings": None,
    }

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

    # --- Create main layout containers ---
    left_frame = ttk.Frame(main_frame)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
    left_frame.rowconfigure(2, weight=1)
    left_frame.columnconfigure(0, weight=1)

    # Build the UI components into the new layout
    _build_input_frame(left_frame, state)
    _build_header(left_frame, state)
    notebook = _build_notebook(left_frame, state)
    _build_log(main_frame, state)
    _build_footer(main_frame, state)

    # Wire up tabs
    tab_workflow = ttk.Frame(notebook, padding=16)
    tab_prompts = ttk.Frame(notebook, padding=16)
    tab_advanced = ttk.Frame(notebook, padding=16)
    notebook.add(tab_workflow, text="Workflow")
    notebook.add(tab_prompts, text="Prompts & Model")
    notebook.add(tab_advanced, text="Advanced")
    _build_tab_workflow(tab_workflow, state)
    _build_tab_prompts_model(tab_prompts, state)
    _build_tab_advanced(tab_advanced, state)

    # Final state setup and initial calls
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
    state["filename_language"].trace_add("write", lambda *_: update_summary(state))
    state["alttext_language"].trace_add("write", lambda *_: update_summary(state))

    # Trigger initial state correctly
    on_output_folder_change()
    update_model_pricing(state)
    update_prompt_preview(state)
    update_summary(state)
    _apply_proxy_preferences(state, force=True)
    _update_provider_status_labels(state)

    return state


def _build_input_frame(parent, state) -> None:
    """Build the persistent input frame."""
    input_card = ttk.Frame(parent, style="Card.TFrame", padding=12)
    input_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
    input_card.columnconfigure(1, weight=1)

    ttk.Label(input_card, text="Input type:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    option = ttk.OptionMenu(input_card, state["input_type"], state["input_type"].get(), "Folder", "File")
    option.grid(row=0, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(input_card, text="Input path:", style="TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    entry = ttk.Entry(input_card, textvariable=state["input_path"], width=50)
    entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
    state["input_entry"] = entry
    ttk.Button(input_card, text="Browse", command=lambda: _select_input(state), style="TButton").grid(
        row=1, column=2, padx=5, pady=5
    )

    ttk.Checkbutton(input_card, text="Include subdirectories", variable=state["include_subdirectories"]).grid(
        row=2, column=1, sticky="w", padx=5, pady=5
    )

    ttk.Label(input_card, textvariable=state["image_count"], style="Small.TLabel").grid(
        row=3, column=1, columnspan=2, sticky="w", padx=5
    )

def _build_header(parent, state) -> None:
    """Build the top summary header."""
    header = ttk.Frame(parent, style="Card.TFrame", padding=12)
    header.grid(row=1, column=0, sticky="ew")
    header.columnconfigure((0, 1, 2), weight=1)
    ttk.Label(header, textvariable=state["summary_model"], style="Card.TLabel").grid(row=0, column=0)
    ttk.Label(header, textvariable=state["summary_prompt"], style="Card.TLabel").grid(row=0, column=1)
    ttk.Label(header, textvariable=state["summary_output"], style="Card.TLabel").grid(row=0, column=2)


def _build_notebook(parent, state) -> ttk.Notebook:
    """Build the main notebook for settings."""
    notebook = ttk.Notebook(parent)
    notebook.grid(row=2, column=0, sticky="nsew", pady=(16, 0))
    return notebook


def _build_log(parent, state) -> None:
    """Build the embedded activity log."""
    log_frame = ttk.Labelframe(parent, text="Activity Log", style="Section.TLabelframe")
    log_frame.grid(row=0, column=1, sticky="nsew")
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(1, weight=1)

    btn_frame = ttk.Frame(log_frame, style="Section.TFrame")
    btn_frame.grid(row=0, column=0, sticky="ew", padx=10)
    ttk.Button(
        btn_frame, text="Copy", command=lambda: _copy_monitor(state), style="Secondary.TButton"
    ).pack(side="left", pady=5)
    ttk.Button(
        btn_frame, text="Clear", command=lambda: _clear_monitor(state), style="Secondary.TButton"
    ).pack(side="left", padx=5)

    log_text = tk.Text(log_frame, wrap="word", height=8, state="disabled", relief="solid", borderwidth=1)
    log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    state["log_text"] = log_text

    scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
    scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 10))
    log_text.configure(yscrollcommand=scrollbar.set)

    # Configure color tags immediately
    current_theme = state["ui_theme"].get()
    palette = PALETTE.get(current_theme, PALETTE.get("Default Light", {}))
    log_text.tag_config("info", foreground=palette.get("info"))
    log_text.tag_config("warn", foreground=palette.get("warning"))
    log_text.tag_config("error", foreground=palette.get("danger"))
    log_text.tag_config("success", foreground=palette.get("success"))
    log_text.tag_config("debug", foreground=palette.get("muted"))
    log_text.tag_config("token", foreground=palette.get("primary"))


def _build_footer(parent, state) -> None:
    """Build the bottom footer/action bar."""
    footer = ttk.Frame(parent)
    footer.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(16, 0))
    footer.columnconfigure(1, weight=1)

    state["status_label"] = ttk.Label(footer, textvariable=state["status_var"], style="Status.TLabel")
    state["status_label"].grid(row=0, column=0, sticky="w")

    state["progress_bar"] = ttk.Progressbar(footer, mode="determinate")
    state["progress_bar"].grid(row=0, column=1, sticky="ew", padx=16)

    state["process_button"] = ttk.Button(footer, text="Describe Images", style="Accent.TButton")
    state["process_button"].grid(row=0, column=2, sticky="e", padx=(16, 8))

    state["lbl_token_usage"] = ttk.Label(footer, text="Tokens: 0", style="Status.TLabel")
    state["lbl_token_usage"].grid(row=0, column=3, sticky="e")


def _build_menus(menubar, root, state) -> None:
    file_menu = tk.Menu(menubar, tearoff=False)
    file_menu.add_command(label="Exit", command=root.destroy)
    menubar.add_cascade(label="File", menu=file_menu)

    help_menu = tk.Menu(menubar, tearoff=False)
    help_menu.add_command(label="About", command=lambda: _show_about(state))
    menubar.add_cascade(label="Help", menu=help_menu)


def _build_tab_workflow(frame, state) -> None:
    """Build the main 'Workflow' tab for I/O."""
    frame.columnconfigure(0, weight=1)

    workflow_tabs = ttk.Notebook(frame)
    workflow_tabs.grid(row=0, column=0, sticky="nsew")

    input_tab = ttk.Frame(workflow_tabs, padding=12)
    processing_tab = ttk.Frame(workflow_tabs, padding=12)
    output_tab = ttk.Frame(workflow_tabs, padding=12)

    for tab in (input_tab, processing_tab, output_tab):
        tab.columnconfigure(0, weight=1)

    workflow_tabs.add(input_tab, text="Context")
    workflow_tabs.add(processing_tab, text="Processing Options")
    workflow_tabs.add(output_tab, text="Output")

    input_card = ttk.Frame(input_tab, style="Section.TFrame", padding=12)
    input_card.grid(row=0, column=0, sticky="nsew")
    input_card.columnconfigure(1, weight=1)

    ttk.Label(input_card, text="Context notes:", style="TLabel").grid(
        row=0, column=0, sticky="nw", padx=5, pady=(8, 0)
    )
    context_frame = ttk.Frame(input_card, style="Section.TFrame")
    context_frame.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=(8, 5))
    context_frame.columnconfigure(0, weight=1)
    context_entry = tk.Text(context_frame, height=6, wrap="word", relief="solid", borderwidth=1)
    context_entry.grid(row=0, column=0, sticky="nsew")
    context_scrollbar = ttk.Scrollbar(context_frame, orient="vertical", command=context_entry.yview)
    context_scrollbar.grid(row=0, column=1, sticky="ns")
    context_entry.configure(yscrollcommand=context_scrollbar.set)

    char_count_var = tk.StringVar(value="0 characters")
    state["context_char_count"] = char_count_var
    ttk.Label(input_card, textvariable=char_count_var, style="Small.TLabel").grid(row=1, column=1, sticky="w", padx=5)
    ttk.Button(input_card, text="Clear", command=lambda: _clear_context(state), style="Secondary.TButton").grid(
        row=1, column=2, sticky="e", padx=5
    )

    def update_char_count(event=None):
        content = context_entry.get("1.0", "end-1c")
        char_count_var.set(f"{len(content)} characters")
        state["context_text"].set(content)

    context_entry.bind("<KeyRelease>", update_char_count)
    state["context_widget"] = context_entry

    if initial_text := state["context_text"].get():
        context_entry.insert("1.0", initial_text)
        update_char_count()

    options_card = ttk.Frame(processing_tab, style="Section.TFrame", padding=12)
    options_card.grid(row=0, column=0, sticky="nsew")
    options_card.columnconfigure(1, weight=1)

    language_row = ttk.Frame(options_card, style="Section.TFrame")
    language_row.grid(row=0, column=0, columnspan=4, sticky="ew")
    language_row.columnconfigure((1, 3), weight=1)
    ttk.Label(language_row, text="Filename language:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    ttk.OptionMenu(
        language_row,
        state["filename_language"],
        state["filename_language"].get(),
        "English",
        "Persian",
    ).grid(row=0, column=1, sticky="w", padx=5, pady=5)
    ttk.Label(language_row, text="Alt-text language:", style="TLabel").grid(row=0, column=2, sticky="w", padx=5, pady=5)
    ttk.OptionMenu(
        language_row,
        state["alttext_language"],
        state["alttext_language"].get(),
        "English",
        "Persian",
    ).grid(row=0, column=3, sticky="w", padx=5, pady=5)

    ttk.Label(options_card, text="Name detail level:", style="TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    ttk.OptionMenu(
        options_card,
        state["name_detail_level"],
        state["name_detail_level"].get(),
        "Detailed",
        "Normal",
        "Minimal",
    ).grid(row=1, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(options_card, text="Vision detail:", style="TLabel").grid(row=1, column=2, sticky="w", padx=5, pady=5)
    ttk.OptionMenu(
        options_card,
        state["vision_detail"],
        state["vision_detail"].get(),
        "auto",
        "high",
        "low",
    ).grid(row=1, column=3, sticky="w", padx=5, pady=5)

    ocr_section = ttk.Frame(options_card, style="Section.TFrame")
    ocr_section.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 0))
    ocr_section.columnconfigure(1, weight=1)
    ttk.Checkbutton(ocr_section, text="Enable OCR before compression", variable=state["ocr_enabled"]).grid(
        row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5
    )
    ttk.Label(ocr_section, text="Tesseract path:", style="TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    ttk.Entry(ocr_section, textvariable=state["tesseract_path"], width=36).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
    ttk.Button(ocr_section, text="Browse", command=lambda: _browse_tesseract(state), style="TButton").grid(
        row=1, column=2, padx=5, pady=5
    )
    ttk.Label(ocr_section, text="OCR language:", style="TLabel").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    ttk.Entry(ocr_section, textvariable=state["ocr_language"], width=10).grid(row=2, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(options_card, text="Current selection:", style="Small.TLabel").grid(row=3, column=0, sticky="w", padx=5, pady=(10, 0))
    options_card.columnconfigure(0, weight=1)
    summary_line = ttk.Label(options_card, textvariable=state["summary_prompt"], style="SmallMuted.TLabel")
    summary_line.grid(row=3, column=1, columnspan=3, sticky="w", padx=5, pady=(10, 0))

    output_card = ttk.Frame(output_tab, style="Section.TFrame", padding=12)
    output_card.grid(row=0, column=0, sticky="nsew")
    output_card.columnconfigure(1, weight=1)

    ttk.Label(output_card, text="Save to:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    ttk.OptionMenu(
        output_card,
        state["output_folder_option"],
        state["output_folder_option"].get(),
        "Same as input",
        "Pictures",
        "Desktop",
        "Custom",
    ).grid(row=0, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(output_card, text="Custom folder:", style="TLabel").grid(
        row=1, column=0, sticky="w", padx=5, pady=5
    )
    custom_output_entry = ttk.Entry(output_card, textvariable=state["custom_output_path"], width=50)
    custom_output_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
    state["custom_output_entry"] = custom_output_entry
    ttk.Button(output_card, text="Browse", command=lambda: _select_output_folder(state), style="TButton").grid(
        row=1, column=2, padx=5, pady=5
    )

    ttk.Checkbutton(
        output_card,
        text="Show interactive results table after processing",
        variable=state["show_results_table"],
    ).grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 0))

    ttk.Label(
        output_card,
        text="Alt-text report and renamed images will be stored in a session folder.",
        style="Small.TLabel",
        wraplength=420,
        justify="left",
    ).grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 0))


def _build_tab_prompts_model(frame, state) -> None:
    """Build the 'Prompts & Model' tab."""
    frame.columnconfigure(0, weight=1)
    notebook = ttk.Notebook(frame)
    notebook.grid(row=0, column=0, sticky="nsew")

    provider_tab = ttk.Frame(notebook, padding=16)
    prompts_tab = ttk.Frame(notebook, padding=16)

    for tab in (provider_tab, prompts_tab):
        tab.columnconfigure(0, weight=1)

    notebook.add(provider_tab, text="LLM Provider")
    notebook.add(prompts_tab, text="Prompts")

    # --- Provider & API Card ---
    provider_card = ttk.Frame(provider_tab, style="Section.TFrame", padding=12)
    provider_card.grid(row=0, column=0, sticky="ew")
    provider_card.columnconfigure(1, weight=1)

    ttk.Label(provider_card, text="Provider:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=5)

    provider_labels = {get_provider_label(pid): pid for pid in AVAILABLE_PROVIDERS}
    provider_label_var = tk.StringVar(value=get_provider_label(state["llm_provider"].get()))
    state["provider_label_var"] = provider_label_var

    ttk.OptionMenu(
        provider_card,
        provider_label_var,
        provider_label_var.get(),
        *provider_labels.keys(),
        command=lambda label: state["llm_provider"].set(provider_labels[label]),
    ).grid(row=0, column=1, sticky="w", padx=5, pady=5)

    api_columns = ttk.Frame(provider_card, style="Section.TFrame")
    api_columns.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 0))
    api_columns.columnconfigure(0, weight=1)
    api_columns.columnconfigure(1, weight=1)

    openai_frame = ttk.Frame(api_columns, style="Section.TFrame", padding=10)
    openai_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    openai_frame.columnconfigure(1, weight=1)

    ttk.Label(openai_frame, text="OpenAI API Key", style="Subheading.TLabel").grid(
        row=0, column=0, columnspan=2, sticky="w"
    )
    openai_entry = ttk.Entry(openai_frame, textvariable=state["openai_api_key"], show="*", width=36)
    openai_entry.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(6, 2))
    state["openai_api_entry"] = openai_entry
    show_openai = tk.BooleanVar()

    def _toggle_openai_key() -> None:
        openai_entry.config(show="" if show_openai.get() else "*")

    ttk.Checkbutton(openai_frame, text="Show", variable=show_openai, command=_toggle_openai_key).grid(
        row=1, column=1, sticky="w", pady=(6, 2)
    )

    def _paste_openai_key() -> None:
        if pyperclip is None:
            set_status(state, "Clipboard support not available (install pyperclip).")
            return
        try:
            if content := pyperclip.paste():
                state["openai_api_key"].set(content)
                set_status(state, "API Key pasted from clipboard.")
            else:
                set_status(state, "Clipboard is empty.")
        except (pyperclip.PyperclipException, tk.TclError):
            set_status(state, "Could not access clipboard.")

    ttk.Button(openai_frame, text="Paste", command=_paste_openai_key, style="Secondary.TButton").grid(
        row=2, column=0, sticky="w"
    )
    openai_status = ttk.Label(
        openai_frame,
        textvariable=tk.StringVar(value="Ready" if state["openai_api_key"].get() else "Not set"),
        style="Small.TLabel",
    )
    openai_status.grid(row=2, column=1, sticky="e")
    state["openai_status_label"] = openai_status

    openrouter_frame = ttk.Frame(api_columns, style="Section.TFrame", padding=10)
    openrouter_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
    openrouter_frame.columnconfigure(1, weight=1)

    ttk.Label(openrouter_frame, text="OpenRouter API Key", style="Subheading.TLabel").grid(
        row=0, column=0, columnspan=2, sticky="w"
    )
    openrouter_entry = ttk.Entry(
        openrouter_frame, textvariable=state["openrouter_api_key"], show="*", width=36
    )
    openrouter_entry.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(6, 2))
    state["openrouter_api_entry"] = openrouter_entry
    show_openrouter = tk.BooleanVar()

    def _toggle_openrouter_key() -> None:
        openrouter_entry.config(show="" if show_openrouter.get() else "*")

    ttk.Checkbutton(
        openrouter_frame, text="Show", variable=show_openrouter, command=_toggle_openrouter_key
    ).grid(row=1, column=1, sticky="w", pady=(6, 2))

    def _paste_openrouter_key() -> None:
        if pyperclip is None:
            set_status(state, "Clipboard support not available (install pyperclip).")
            return
        try:
            if content := pyperclip.paste():
                state["openrouter_api_key"].set(content)
                set_status(state, "API Key pasted from clipboard.")
            else:
                set_status(state, "Clipboard is empty.")
        except (pyperclip.PyperclipException, tk.TclError):
            set_status(state, "Could not access clipboard.")

    ttk.Button(
        openrouter_frame, text="Paste", command=_paste_openrouter_key, style="Secondary.TButton"
    ).grid(row=2, column=0, sticky="w")
    openrouter_status = ttk.Label(
        openrouter_frame,
        textvariable=tk.StringVar(value="Ready" if state["openrouter_api_key"].get() else "Not set"),
        style="Small.TLabel",
    )
    openrouter_status.grid(row=2, column=1, sticky="e")
    state["openrouter_status_label"] = openrouter_status

    ttk.Label(openrouter_frame, text="Free multimodal models refresh automatically.", style="Small.TLabel").grid(
        row=3, column=0, columnspan=2, sticky="w", pady=(6, 0)
    )

    state["openai_section"] = openai_frame
    state["openrouter_section"] = openrouter_frame

    # --- Model & Pricing Card ---
    model_card = ttk.Frame(provider_tab, style="Section.TFrame", padding=12)
    model_card.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
    model_card.columnconfigure(1, weight=1)

    ttk.Label(model_card, text="Model:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=5)

    model_label_var = tk.StringVar()
    state["model_label_var"] = model_label_var

    model_menu = ttk.OptionMenu(model_card, model_label_var, "")
    model_menu.grid(row=0, column=1, sticky="w", padx=5, pady=5)
    state["model_option_widget"] = model_menu
    state["model_option_menu"] = model_menu["menu"]

    def _refresh_openrouter_models_ui() -> None:
        try:
            refresh_openrouter_models()
            models = get_models_for_provider("openrouter")
            current = state["openrouter_model"].get()
            if current not in models:
                fallback = get_default_model("openrouter")
                state["openrouter_model"].set(fallback)
                if state["llm_provider"].get() == "openrouter":
                    state["llm_model"].set(fallback)
            state["provider_model_map"]["openrouter"] = state["openrouter_model"].get()
            _refresh_model_choices()
            update_model_pricing(state)
            update_summary(state)
            set_status(state, "OpenRouter models refreshed.")
        except Exception as exc:  # pragma: no cover - network error path
            set_status(state, f"Could not refresh models: {exc}")

    refresh_button = ttk.Button(
        model_card,
        text="Refresh free models",
        command=_refresh_openrouter_models_ui,
        style="Secondary.TButton",
    )
    refresh_button.grid(row=0, column=2, sticky="e", padx=(5, 0), pady=5)
    state["refresh_openrouter_button"] = refresh_button

    state["lbl_model_pricing"] = ttk.Label(
        model_card, text="", justify="left", style="Small.TLabel"
    )
    state["lbl_model_pricing"].grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=(0, 10))

    def _refresh_model_choices() -> None:
        provider_key = state["llm_provider"].get()
        models = get_models_for_provider(provider_key)
        menu = state["model_option_menu"]
        menu.delete(0, "end")

        if not models:
            model_label_var.set("No models available")
            return

        for model_id, info in models.items():
            label = info.get("label", model_id)
            menu.add_command(label=label, command=lambda value=model_id: state["llm_model"].set(value))

        current_model = state["llm_model"].get()
        if current_model not in models:
            fallback = state["provider_model_map"].get(provider_key) or get_default_model(provider_key)
            if fallback not in models:
                fallback = next(iter(models.keys()))
            state["llm_model"].set(fallback)
            current_model = fallback

        model_label_var.set(models[current_model].get("label", current_model))

    def _refresh_provider_sections() -> None:
        provider_key = state["llm_provider"].get()
        provider_label_var.set(get_provider_label(provider_key))
        if provider_key == "openrouter":
            openrouter_frame.grid()
            openai_frame.grid_remove()
            state["refresh_openrouter_button"].grid()
        else:
            openai_frame.grid()
            openrouter_frame.grid_remove()
            state["refresh_openrouter_button"].grid_remove()

    def _sync_model_label(*_) -> None:
        provider_key = state["llm_provider"].get()
        models = get_models_for_provider(provider_key)
        current_model = state["llm_model"].get()
        model_label_var.set(models.get(current_model, {}).get("label", current_model))

    state["llm_provider"].trace_add(
        "write", lambda *_: (_refresh_provider_sections(), _refresh_model_choices())
    )
    state["llm_model"].trace_add("write", _sync_model_label)

    _refresh_provider_sections()
    _refresh_model_choices()

    # --- Prompts Tab Content ---
    prompt_card = ttk.Frame(prompts_tab, style="Section.TFrame", padding=12)
    prompt_card.grid(row=0, column=0, sticky="nsew")
    prompt_card.columnconfigure(0, weight=1)
    prompt_card.rowconfigure(1, weight=1)

    toolbar = ttk.Frame(prompt_card, style="Section.TFrame")
    toolbar.grid(row=0, column=0, sticky="ew")
    toolbar.columnconfigure(1, weight=1)

    ttk.Label(toolbar, text="Prompt preset:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=5)

    prompt_labels = {v["label"]: k for k, v in state["prompts"].items()}
    prompt_label_var = tk.StringVar(value=state["prompts"][state["prompt_key"].get()]["label"])

    def on_prompt_select(label):
        key = prompt_labels[label]
        state["prompt_key"].set(key)
        prompt_label_var.set(label)

    prompt_menu = ttk.OptionMenu(
        toolbar,
        prompt_label_var,
        prompt_label_var.get(),
        *prompt_labels.keys(),
        command=on_prompt_select,
    )
    prompt_menu.grid(row=0, column=1, sticky="w", padx=5, pady=5)
    state["prompt_option_widget"] = prompt_menu
    state["prompt_option_menu"] = prompt_menu["menu"]

    ttk.Button(
        toolbar,
        text="Edit Prompts...",
        command=lambda: open_prompt_editor(state),
        style="Secondary.TButton",
    ).grid(row=0, column=2, sticky="e", padx=5)

    preview_frame = ttk.Frame(prompt_card, style="Section.TFrame")
    preview_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
    preview_frame.columnconfigure(0, weight=1)

    prompt_preview = tk.Text(
        preview_frame,
        height=10,
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

    footer = ttk.Frame(prompt_card, style="Section.TFrame")
    footer.grid(row=2, column=0, sticky="ew", pady=(12, 0))
    footer.columnconfigure(0, weight=1)
    ttk.Label(
        footer,
        text="Need to tweak prompts? Use the editor to duplicate or rename presets.",
        style="Small.TLabel",
    ).grid(row=0, column=0, sticky="w")

    refresh_prompt_choices(state)


def _build_tab_advanced(frame, state) -> None:
    """Build the 'Advanced' settings tab."""
    frame.columnconfigure(0, weight=1)
    section_notebook = ttk.Notebook(frame)
    section_notebook.grid(row=0, column=0, sticky="nsew")

    appearance_tab = ttk.Frame(section_notebook, padding=16)
    automation_tab = ttk.Frame(section_notebook, padding=16)
    network_tab = ttk.Frame(section_notebook, padding=16)
    maintenance_tab = ttk.Frame(section_notebook, padding=16)

    for tab in (appearance_tab, automation_tab, network_tab, maintenance_tab):
        tab.columnconfigure(0, weight=1)

    section_notebook.add(appearance_tab, text="Appearance")
    section_notebook.add(automation_tab, text="Automation")
    section_notebook.add(network_tab, text="Network")
    section_notebook.add(maintenance_tab, text="Maintenance")

    _build_appearance_section(appearance_tab, state)
    _build_automation_section(automation_tab, state)
    _build_proxy_section(network_tab, state)
    _build_maintenance_section(maintenance_tab, state)


def _clear_context(state, *, silent: bool = False) -> None:
    if "context_widget" in state:
        state["context_widget"].delete("1.0", "end")
    state["context_text"].set("")
    if "context_char_count" in state:
        state["context_char_count"].set("0 characters")
    if not silent:
        set_status(state, "Context cleared.")


def _select_input(state) -> None:
    if state["input_type"].get() == "Folder":
        path = filedialog.askdirectory()
    else:
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.heic *.heif")])
    if path:
        cleanup_temp_drop_folder(state)
        state["input_path"].set(path)
        if state["input_type"].get() == "Folder":
            recursive = state["include_subdirectories"].get()
            count = get_image_count_in_folder(path, recursive)
        else:
            count = 1

        state["image_count"].set(f"{count} image(s) selected.")
        set_status(state, f"Ready to process {count} image(s).")
        _clear_monitor(state)
        update_summary(state)

        _clear_context(state, silent=True)


def _select_output_folder(state) -> None:
    path = filedialog.askdirectory()
    if path:
        state["custom_output_path"].set(path)


def _browse_tesseract(state) -> None:
    path = filedialog.askopenfilename(filetypes=[("Tesseract Executable", "tesseract.exe")])
    if path:
        state["tesseract_path"].set(path)


def _save_settings(state) -> None:
    geometry = state["root"].winfo_geometry()

    if "context_widget" in state:
        state["context_text"].set(state["context_widget"].get("1.0", "end").strip())

    save_config(state, geometry)

    apply_theme(state["root"], state["ui_theme"].get())

    messagebox.showinfo("Saved", "✅ Settings saved successfully.")


def _reset_token_usage(state) -> None:
    state["total_tokens"].set(0)
    update_token_label(state)
    append_monitor_colored(state, "Token usage reset to 0", "warn")


def _reset_global_stats(state) -> None:
    if "global_images_count" in state:
        state["global_images_count"].set(0)
        append_monitor_colored(state, "Global images analyzed count reset to 0", "warn")
    else:
        append_monitor_colored(state, "No global_images_count found to reset", "warn")


def _build_appearance_section(parent, state) -> None:
    card = ttk.Frame(parent, style="Section.TFrame", padding=12)
    card.grid(row=0, column=0, sticky="nsew")
    card.columnconfigure(1, weight=1)

    ttk.Label(card, text="UI Theme:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    ttk.OptionMenu(
        card,
        state["ui_theme"],
        state["ui_theme"].get(),
        "Arctic Light",
        "Midnight",
        "Forest",
        "Sunset",
        "Lavender",
        "Charcoal",
        "Ocean Blue",
        "Deep Space",
        "Warm Sand",
        "Cherry Blossom",
        "Emerald Night",
        "Monochrome",
        "Nord",
    ).grid(row=0, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(
        card,
        text="Choose a theme to customize the overall look and feel.",
        style="Small.TLabel",
        wraplength=420,
        justify="left",
    ).grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=(8, 0))


def _build_automation_section(parent, state) -> None:
    card = ttk.Frame(parent, style="Section.TFrame", padding=12)
    card.grid(row=0, column=0, sticky="nsew")
    card.columnconfigure(1, weight=1)

    ttk.Checkbutton(card, text="Enable OCR", variable=state["ocr_enabled"]).grid(
        row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5
    )

    ttk.Label(card, text="Tesseract path:", style="TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    ttk.Entry(card, textvariable=state["tesseract_path"], width=40).grid(
        row=1, column=1, sticky="ew", padx=5, pady=5
    )
    ttk.Button(card, text="Browse", command=lambda: _browse_tesseract(state), style="TButton").grid(
        row=1, column=2, padx=5, pady=5
    )

    ttk.Label(card, text="OCR language:", style="TLabel").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    ttk.Entry(card, textvariable=state["ocr_language"], width=10).grid(
        row=2, column=1, sticky="w", padx=5, pady=5
    )

    info = (
        "When enabled, detected text is shared with the model before compression."
    )
    ttk.Label(card, text=info, style="Small.TLabel", wraplength=420, justify="left").grid(
        row=3, column=0, columnspan=3, sticky="w", padx=5, pady=(4, 0)
    )


def _build_proxy_section(parent, state) -> None:
    card = ttk.Frame(parent, style="Section.TFrame", padding=12)
    card.grid(row=0, column=0, sticky="nsew")
    card.columnconfigure(0, weight=1)

    header = ttk.Frame(card, style="Section.TFrame")
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(0, weight=1)

    ttk.Checkbutton(
        header,
        text="Use proxy for network requests",
        variable=state["proxy_enabled"],
    ).grid(row=0, column=0, sticky="w", padx=5, pady=(0, 8))

    ttk.Button(
        header,
        text="Refresh detection",
        command=lambda: _refresh_detected_proxy(state),
        style="Secondary.TButton",
    ).grid(row=0, column=1, sticky="e", padx=5, pady=(0, 8))

    body = ttk.Frame(card, style="Section.TFrame")
    body.grid(row=1, column=0, sticky="nsew")
    body.columnconfigure(0, weight=1)

    ttk.Label(body, text="Detected system proxy:", style="TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(
        body,
        textvariable=state["proxy_detected_label"],
        style="Small.TLabel",
        justify="left",
    ).grid(row=1, column=0, sticky="w", padx=(12, 0), pady=(0, 6))

    ttk.Label(body, text="Effective proxy in use:", style="TLabel").grid(row=2, column=0, sticky="w")
    ttk.Label(
        body,
        textvariable=state["proxy_effective_label"],
        style="Small.TLabel",
        justify="left",
    ).grid(row=3, column=0, sticky="w", padx=(12, 0), pady=(0, 10))

    ttk.Label(body, text="Custom override (optional):", style="TLabel").grid(row=4, column=0, sticky="w")
    override_entry = ttk.Entry(body, textvariable=state["proxy_override"], width=50)
    override_entry.grid(row=5, column=0, sticky="ew", pady=5)
    state["proxy_override_entry"] = override_entry

    ttk.Label(
        body,
        text="Leave blank to rely on detected values. Applies to both HTTP and HTTPS.",
        style="Small.TLabel",
        wraplength=420,
        justify="left",
    ).grid(row=6, column=0, sticky="w")


def _build_maintenance_section(parent, state) -> None:
    card = ttk.Frame(parent, style="Section.TFrame", padding=12)
    card.grid(row=0, column=0, sticky="nsew")
    card.columnconfigure(0, weight=1)

    primary_row = ttk.Frame(card, style="Section.TFrame")
    primary_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    primary_row.columnconfigure(2, weight=1)

    ttk.Button(primary_row, text="Save Settings", command=lambda: _save_settings(state), style="TButton").grid(
        row=0, column=0, padx=(0, 8)
    )
    ttk.Button(primary_row, text="Open Config Folder", command=open_config_folder, style="TButton").grid(
        row=0, column=1, padx=(0, 8)
    )

    secondary_row = ttk.Frame(card, style="Section.TFrame")
    secondary_row.grid(row=1, column=0, sticky="ew")
    secondary_row.columnconfigure(3, weight=1)

    ttk.Button(
        secondary_row,
        text="Reset Defaults",
        command=lambda: state["reset_config_callback"](),
        style="Secondary.TButton",
    ).grid(row=0, column=0, padx=(0, 8), pady=5)
    ttk.Button(
        secondary_row,
        text="Reset Token Usage",
        command=lambda: _reset_token_usage(state),
        style="Secondary.TButton",
    ).grid(row=0, column=1, padx=(0, 8), pady=5)
    ttk.Button(
        secondary_row,
        text="Reset Analyzed Stats",
        command=lambda: _reset_global_stats(state),
        style="Secondary.TButton",
    ).grid(row=0, column=2, padx=(0, 8), pady=5)

def _update_proxy_controls(state) -> None:
    entry = state.get("proxy_override_entry")
    if entry is None:
        return
    entry_state = "normal" if state.get("proxy_enabled") and state["proxy_enabled"].get() else "disabled"
    entry.config(state=entry_state)


def _update_proxy_effective_label(state) -> None:
    if "proxy_effective_label" not in state:
        return
    enabled_var = state.get("proxy_enabled")
    override_var = state.get("proxy_override")
    enabled = bool(enabled_var.get()) if enabled_var is not None else True
    override = override_var.get().strip() if override_var is not None else ""
    proxies = get_requests_proxies(enabled=enabled, override=override or None)
    state["proxy_effective_label"].set(_format_proxy_mapping(proxies))


def _apply_proxy_preferences(state, *, force: bool = False) -> None:
    if "proxy_enabled" not in state or "proxy_override" not in state:
        return

    enabled = bool(state["proxy_enabled"].get())
    override_value = state["proxy_override"].get().strip()
    last_settings = state.get("_proxy_last_settings") or (None, None)
    current_settings = (enabled, override_value)

    if force or current_settings != last_settings:
        set_proxy_preferences(enabled, override_value or None)
        state["_proxy_last_settings"] = current_settings

    _update_proxy_controls(state)
    _update_proxy_effective_label(state)


def _refresh_detected_proxy(state) -> None:
    detected = reload_system_proxies()
    if "proxy_detected_label" in state:
        state["proxy_detected_label"].set(_format_proxy_mapping(detected))
    configure_global_proxy(force=True)
    _update_proxy_effective_label(state)


def _update_provider_status_labels(state) -> None:
    openai_label = state.get("openai_status_label")
    if openai_label is not None:
        is_set = bool(state.get("openai_api_key").get()) if "openai_api_key" in state else False
        openai_label.configure(text="Ready" if is_set else "Not set")

    openrouter_label = state.get("openrouter_status_label")
    if openrouter_label is not None:
        is_set = bool(state.get("openrouter_api_key").get()) if "openrouter_api_key" in state else False
        openrouter_label.configure(text="Ready" if is_set else "Not set")


def append_monitor_colored(state, message: str, level: str = "info") -> None:
    """Append a colored message to the log."""
    formatted = f"[{level.upper()}] {message}"
    state["logs"].append((formatted, level))
    _write_monitor_line_colored(state, (formatted, level))


def _clear_monitor(state) -> None:
    """Clear the activity log."""
    state["logs"].clear()
    if "log_text" in state:
        widget = state["log_text"]
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.config(state="disabled")


def _copy_monitor(state) -> None:
    """Copy the activity log content to the clipboard."""
    if "log_text" in state:
        text = state["log_text"].get("1.0", "end")
        if pyperclip is None:
            set_status(state, "Clipboard support not available (install pyperclip).")
            return
        pyperclip.copy(text)
        set_status(state, "Log copied to clipboard.")


def _write_monitor_line_colored(state, log_item) -> None:
    """Write a single line to the activity log with the correct color tag."""
    if "log_text" not in state:
        return

    text_widget = state["log_text"]
    text, level = log_item

    text_widget.config(state="normal")
    text_widget.insert("end", text + "\\n", level)
    text_widget.see("end")
    text_widget.config(state="disabled")


def _show_about(state) -> None:
    settings = SettingsService()
    use_pyside6 = settings.get("feature_flags", {}).get("use_pyside6_about_window", False)

    if use_pyside6:
        # Ensure a QApplication instance exists
        if not QApplication.instance():
            QApplication(sys.argv)

        # Create and show the PySide6 About window
        about_vm = AboutViewModel()
        about_view = AboutView(about_vm)

        # Load and apply the stylesheet
        with open('src/app/resources/styles/generated.qss', 'r') as f:
            about_view.setStyleSheet(f.read())

        about_view.show()
    else:
        import webbrowser
        root = state.get("root")
        top = tk.Toplevel(root)
        top.title("About Altomatic")
        top.geometry("520x320")
        top.resizable(False, False)
        current_theme = state["ui_theme"].get()
        palette = PALETTE.get(current_theme, PALETTE["Arctic Light"])
        top.configure(bg=palette["background"])
        _apply_window_icon(top)
        apply_theme_to_window(top, current_theme)

        wrapper = ttk.Frame(top, padding=20, style="Section.TFrame")
        wrapper.pack(fill="both", expand=True)
        wrapper.columnconfigure(0, weight=1)

        ttk.Label(wrapper, text="Altomatic", font=("Segoe UI Semibold", 16)).grid(row=0, column=0, sticky="w")
        ttk.Label(
            wrapper,
            text="Created by Mehdi",
            style="Small.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 12))

        description = (
            "Altomatic helps you batch-generate file names and alt text for images using multimodal LLMs.\\n"
            "Choose your provider, drop images, and let the app handle OCR, compression, and AI prompts."
        )
        ttk.Label(wrapper, text=description, wraplength=460, justify="left").grid(row=2, column=0, sticky="w")

        link = ttk.Label(wrapper, text="Visit GitHub Repository", style="Accent.TLabel", cursor="hand2")
        link.grid(row=3, column=0, sticky="w", pady=(16, 0))
        link.bind("<Button-1>", lambda _event: webbrowser.open_new("https://github.com/MehdiDevX"))

        ttk.Button(wrapper, text="Close", command=top.destroy, style="Accent.TButton").grid(
            row=4, column=0, sticky="e", pady=(20, 0)
        )
