"""UI construction helpers with improved organization and visual hierarchy."""

from __future__ import annotations

import os
import shutil
import tkinter as tk
from importlib import resources
from tkinter import filedialog, messagebox, simpledialog, ttk

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


class AnimatedLabel(ttk.Label):
    """Label with animated scrolling for overflow text."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.full_text = ""
        self.running = False
        self.bind("<Configure>", self.check_width)

    def apply_theme_styling(self, palette: dict) -> None:
        """Apply theme styling to the label."""
        try:
            # Use standard ttk.Label styling - let the theme system handle it
            self.configure(style="Small.TLabel")
        except Exception:
            # Final fallback - use default style
            try:
                self.configure(style="TLabel")
            except Exception:
                pass

    def set_text(self, text):
        self.full_text = text
        self.running = False  # Reset animation state
        self.check_width()

    def check_width(self, event=None):
        if not self.full_text:
            return
        self.config(text=self.full_text)
        self.update_idletasks()
        if self.winfo_width() < self.winfo_reqwidth() and not self.running:
            self.running = True
            self.animate()
        elif self.winfo_width() >= self.winfo_reqwidth() and self.running:
            self.running = False
            self.config(text=self.full_text)  # Show full text when not scrolling

    def animate(self):
        if not self.running:
            self.config(text=self.full_text)
            return
        text = self.cget("text")
        # Move first character to the end, but avoid creating multiple consecutive separators
        first_char = text[0]
        rest = text[1:]

        # If moving the first character would create double separators, use space instead
        if (first_char in '-•' and rest.startswith(first_char)):
            new_text = rest + " "
        elif first_char in '-•' and len(rest) > 0 and rest[0] in '-•':
            # Handle case where next character is also a separator
            new_text = rest + " "
        else:
            new_text = rest + first_char

        self.config(text=new_text)
        self.after(200, self.animate)


def _scaled_geometry(widget: tk.Misc, base_width: int, base_height: int) -> str:
    """Calculate responsive window geometry based on screen size."""
    widget.update_idletasks()
    screen_w = widget.winfo_screenwidth()
    screen_h = widget.winfo_screenheight()

    min_w = int(screen_w * 0.5)
    max_w = int(screen_w * 0.85)
    min_h = int(screen_h * 0.5)
    max_h = int(screen_h * 0.85)

    width = min(max(base_width, min_w), max_w)
    height = min(max(base_height, min_h), max_h)

    width = max(700, min(width, screen_w - 40))
    height = max(500, min(height, screen_h - 80))

    return f"{width}x{height}"


def _apply_window_icon(window: tk.Misc) -> None:
    """Apply application icon to window."""
    try:
        with resources.as_file(
            resources.files("altomatic.resources") / "altomatic_icon.ico"
        ) as icon_path:
            window.iconbitmap(default=str(icon_path))
    except Exception:
        pass


def _create_section_header(parent, text: str, style="TLabel") -> ttk.Label:
    """Create a consistent section header."""
    return ttk.Label(parent, text=text, style=style, font=("Segoe UI Semibold", 11))


def _create_info_label(parent, text: str, wraplength=500) -> ttk.Label:
    """Create a consistent info/help label."""
    return ttk.Label(
        parent, 
        text=text, 
        style="Small.TLabel",
        wraplength=wraplength,
        justify="left"
    )


# === State Update Functions ===

def update_token_label(state) -> None:
    """Update the token usage display."""
    if "lbl_token_usage" in state:
        state["lbl_token_usage"].config(text=f"Tokens: {state['total_tokens'].get():,}")


def update_model_pricing(state) -> None:
    """Update the model pricing information display."""
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
    
    pricing_text = f"{provider_label} • {model_label}\n{format_pricing(provider, model_id)}"
    if vendor:
        pricing_text += f"\nVendor: {vendor}"
    
    state["lbl_model_pricing"].config(text=pricing_text)


def _format_proxy_mapping(mapping: dict[str, str]) -> str:
    """Format proxy mapping dictionary for display."""
    if not mapping:
        return "None"
    lines = [f"{scheme}: {value}" for scheme, value in sorted(mapping.items())]
    return "\n".join(lines)


def update_summary(state) -> None:
    """Update the summary bar with current selections."""
    if "summary_model" not in state:
        return

    # Update model summary
    provider_var = state.get("llm_provider")
    provider = provider_var.get() if provider_var is not None else DEFAULT_PROVIDER
    model_var = state.get("llm_model")
    model_id = model_var.get() if model_var is not None else DEFAULT_MODEL
    models = get_models_for_provider(provider)
    model_label = models.get(model_id, {}).get("label", model_id)
    state["summary_model"].set_text(f"Model: {get_provider_label(provider)} • {model_label}")

    # Update prompt summary
    prompts = state.get("prompts") or load_prompts()
    prompt_key = state["prompt_key"].get()
    prompt_entry = prompts.get(prompt_key) or prompts.get("default") or next(iter(prompts.values()), {})
    prompt_text = f"Prompt: {prompt_entry.get('label', prompt_key)}"
    state["summary_prompt"].set_text(prompt_text)
    summary_prompt_var = state.get("summary_prompt_var")
    if summary_prompt_var is not None:
        summary_prompt_var.set(prompt_text)

    # Update output summary
    destination = state["output_folder_option"].get()
    if destination == "Custom":
        path = state["custom_output_path"].get().strip() or "(not set)"
        output_text = f"Output: Custom → {path}"
    else:
        output_text = f"Output: {destination}"

    state["summary_output"].set_text(output_text)
    summary_output_var = state.get("summary_output_var")
    if summary_output_var is not None:
        summary_output_var.set(output_text)

    # Trigger scroll check after updating summaries
    if "_update_summary_scrolling" in state and "summary_container" in state:
        state["summary_container"].after(50, state["_update_summary_scrolling"])


def set_status(state, message: str) -> None:
    """Update the status bar message."""
    if "status_var" in state:
        state["status_var"].set(message)


def update_prompt_preview(state) -> None:
    """Update the prompt preview text widget."""
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
    widget.insert("1.0", f"{label}\n\n{template}".strip())
    widget.config(state="disabled")


def refresh_prompt_choices(state) -> None:
    """Refresh the prompt dropdown menu with current prompts."""
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
    """Clean up temporary drop folder if it exists."""
    folder = state.get("temp_drop_folder")
    if folder and os.path.isdir(folder):
        try:
            shutil.rmtree(folder)
        except OSError:
            pass
    state["temp_drop_folder"] = None


# === Prompt Editor Dialog ===

def open_prompt_editor(state) -> None:
    """Open the prompt editor dialog window."""
    root = state.get("root")
    editor = tk.Toplevel(root)
    editor.title("Prompt Editor")
    editor.geometry(_scaled_geometry(editor, 1000, 700))
    editor.minsize(800, 600)
    editor.grab_set()
    
    current_theme = state["ui_theme"].get()
    palette = PALETTE.get(current_theme) or PALETTE.get("Arctic Light")
    editor.configure(bg=palette["background"])
    _apply_window_icon(editor)

    prompts = load_prompts()
    working = {key: dict(value) for key, value in prompts.items()}

    # Main container
    container = ttk.Frame(editor, padding=16, style="TFrame")
    container.pack(fill="both", expand=True)
    container.columnconfigure(0, weight=1)
    container.rowconfigure(0, weight=1)

    # Paned window for split view
    paned = ttk.Panedwindow(container, orient="horizontal")
    paned.grid(row=0, column=0, sticky="nsew", pady=(0, 12))

    # === Left Panel: Prompt List ===
    list_panel = ttk.Frame(paned, style="Card.TFrame", padding=12)
    list_panel.columnconfigure(0, weight=1)
    list_panel.rowconfigure(2, weight=1)

    _create_section_header(list_panel, "Available Prompts").grid(row=0, column=0, sticky="w", pady=(0, 8))

    search_var = tk.StringVar()
    search_entry = ttk.Entry(list_panel, textvariable=search_var)
    search_entry.grid(row=1, column=0, sticky="ew", pady=(0, 8))

    listbox_frame = ttk.Frame(list_panel, style="Section.TFrame")
    listbox_frame.grid(row=2, column=0, sticky="nsew")
    listbox_frame.columnconfigure(0, weight=1)
    listbox_frame.rowconfigure(0, weight=1)

    listbox = tk.Listbox(
        listbox_frame,
        exportselection=False,
        height=15,
        highlightthickness=0,
        relief="flat",
        activestyle="none",
    )
    listbox_scroll = ttk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
    listbox.grid(row=0, column=0, sticky="nsew")
    listbox_scroll.grid(row=0, column=1, sticky="ns")
    listbox.configure(
        bg=palette["surface"],
        fg=palette["foreground"],
        selectbackground=palette["primary"],
        selectforeground=palette["primary-foreground"],
        highlightbackground=palette["surface-2"],
        highlightcolor=palette["surface-2"],
        yscrollcommand=listbox_scroll.set,
    )

    # === Right Panel: Prompt Details ===
    detail_panel = ttk.Frame(paned, style="Card.TFrame", padding=16)
    detail_panel.columnconfigure(0, weight=1)
    detail_panel.rowconfigure(3, weight=1)

    _create_section_header(detail_panel, "Prompt Details").grid(row=0, column=0, sticky="w", pady=(0, 12))

    # Label section
    label_section = ttk.Frame(detail_panel, style="Section.TFrame")
    label_section.grid(row=1, column=0, sticky="ew", pady=(0, 12))
    label_section.columnconfigure(0, weight=1)
    
    ttk.Label(label_section, text="Display Name", style="TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
    label_var = tk.StringVar()
    label_entry = ttk.Entry(label_section, textvariable=label_var)
    label_entry.grid(row=1, column=0, sticky="ew")

    # Template section
    ttk.Label(detail_panel, text="Prompt Template", style="TLabel").grid(row=2, column=0, sticky="w", pady=(0, 4))
    
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
        highlightcolor=palette["primary"],
    )

    template_scroll = ttk.Scrollbar(template_frame, orient="vertical", command=template_text.yview)
    template_scroll.grid(row=0, column=1, sticky="ns")
    template_text.configure(yscrollcommand=template_scroll.set)

    # Stats and buttons
    stats_frame = ttk.Frame(detail_panel, style="Section.TFrame")
    stats_frame.grid(row=4, column=0, sticky="ew", pady=(8, 0))
    stats_frame.columnconfigure(0, weight=1)

    template_stats = tk.StringVar(value="0 characters")
    ttk.Label(stats_frame, textvariable=template_stats, style="Small.TLabel").grid(row=0, column=0, sticky="w")

    button_bar = ttk.Frame(detail_panel, style="Section.TFrame")
    button_bar.grid(row=5, column=0, sticky="ew", pady=(12, 0))
    button_bar.columnconfigure(6, weight=1)

    paned.add(list_panel, weight=1)
    paned.add(detail_panel, weight=2)

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
        name = simpledialog.askstring("New Prompt", "Enter a name for the new prompt:", parent=editor)
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
        new_label = f"{base_label} (Copy)"
        candidate = slugify(new_label) or f"{key}-copy"
        suffix = 1
        while candidate in working:
            suffix += 1
            candidate = slugify(f"{new_label} {suffix}") or f"{key}-copy-{suffix}"
        working[candidate] = {
            "label": f"{base_label} (Copy)" if suffix == 1 else f"{base_label} (Copy {suffix})",
            "template": working[key].get("template", ""),
        }
        refresh_list(select_key=candidate)

    def delete_prompt(event=None) -> None:
        key = current_key.get()
        if key == "default" or len(working) <= 1:
            messagebox.showinfo("Cannot Delete", "The default prompt cannot be deleted, and you must keep at least one prompt.", parent=editor)
            return
        if messagebox.askyesno("Delete Prompt", f"Delete prompt '{working[key].get('label', key)}'?", parent=editor):
            working.pop(key, None)
            refresh_list()

    def save_changes(event=None) -> None:
        key = current_key.get()
        if key not in working:
            messagebox.showerror("No Selection", "Please select a prompt to save.", parent=editor)
            return
        working[key]["label"] = label_var.get().strip() or key
        working[key]["template"] = template_text.get("1.0", "end").strip()
        save_prompts(working)
        refresh_prompt_choices(state)
        state["prompt_key"].set(key)
        set_status(state, f"Saved '{working[key]['label']}'")
        refresh_list(select_key=key)

    def save_and_close() -> None:
        save_changes()
        editor.destroy()

    # Button bar
    ttk.Button(button_bar, text="New", command=add_prompt, style="Accent.TButton").grid(row=0, column=0, padx=(0, 6))
    ttk.Button(button_bar, text="Duplicate", command=duplicate_prompt, style="TButton").grid(row=0, column=1, padx=(0, 6))
    ttk.Button(button_bar, text="Delete", command=delete_prompt, style="Secondary.TButton").grid(row=0, column=2, padx=(0, 6))
    ttk.Label(button_bar, text="", style="TLabel").grid(row=0, column=3, padx=(12, 0))  # Spacer
    ttk.Button(button_bar, text="Save", command=save_changes, style="TButton").grid(row=0, column=4, padx=(0, 6))
    ttk.Button(button_bar, text="Save & Close", command=save_and_close, style="Accent.TButton").grid(row=0, column=5, padx=(0, 6))
    ttk.Button(button_bar, text="Cancel", command=editor.destroy, style="TButton").grid(row=0, column=6, sticky="e")

    # Event bindings
    search_entry.bind("<KeyRelease>", lambda *_: refresh_list())
    listbox.bind("<<ListboxSelect>>", load_selected)
    listbox.bind("<Double-Button-1>", lambda *_: template_text.focus_set())
    template_text.bind("<KeyRelease>", lambda *_: update_template_stats())
    editor.bind("<Control-s>", save_changes)
    editor.bind("<Control-d>", duplicate_prompt)
    listbox.bind("<Delete>", delete_prompt)

    refresh_list(select_key=current_key.get())
    apply_theme_to_window(editor, current_theme)
    search_entry.focus_set()


# === Main UI Builder ===

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
        _popup_menu([("About", lambda: _show_about(state))], event)

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

    active_model = (
        user_config.get("llm_model")
        or provider_model_map.get(provider)
        or get_default_model(provider)
    )
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
        "summary_model": AnimatedLabel(),
        "summary_prompt": AnimatedLabel(),
        "summary_output": AnimatedLabel(),
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
    tab_workflow = ttk.Frame(notebook, padding=20)
    tab_prompts = ttk.Frame(notebook, padding=20)
    tab_advanced = ttk.Frame(notebook, padding=20)
    tab_log = ttk.Frame(notebook, padding=20)
    
    notebook.add(tab_workflow, text="Workflow")
    notebook.add(tab_prompts, text="Prompts & Model")
    notebook.add(tab_advanced, text="Advanced")
    notebook.add(tab_log, text="Activity Log")
    
    _build_tab_workflow(tab_workflow, state)
    _build_tab_prompts_model(tab_prompts, state)
    _build_tab_advanced(tab_advanced, state)
    _build_log(tab_log, state)

    # Build menus
    _build_menus(menubar, root, state)

    # Event handlers
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


# === UI Component Builders ===

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
    _create_info_label(
        header_frame,
        "Drop files or folders here, or use the browse button to select images."
    ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    # Input path selection
    input_frame = ttk.Frame(input_card, style="Section.TFrame")
    input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
    input_frame.columnconfigure(0, weight=1)

    entry = ttk.Entry(input_frame, textvariable=state["input_path"], width=50)
    entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    state["input_entry"] = entry
    
    ttk.Button(
        input_frame, 
        text="Browse...", 
        command=lambda: _select_input(state),
        style="TButton"
    ).grid(row=0, column=1)

    # Options row
    options_frame = ttk.Frame(input_card, style="Section.TFrame")
    options_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
    options_frame.columnconfigure(1, weight=1)

    ttk.Checkbutton(
        options_frame,
        text="Include subdirectories",
        variable=state["recursive_search"]
    ).grid(row=0, column=0, sticky="w")

    ttk.Label(
        options_frame,
        textvariable=state["image_count"],
        style="Small.TLabel"
    ).grid(row=0, column=1, sticky="e")

    # Summary bar with scrolling support
    summary_frame = ttk.Frame(input_card, style="Section.TFrame")
    summary_frame.grid(row=3, column=0, sticky="ew")
    summary_frame.columnconfigure((0, 1, 2), weight=1)

    # Create a container frame that can scroll as a unit
    summary_container = ttk.Frame(summary_frame, style="TFrame")
    summary_container.grid(row=0, column=0, sticky="ew")
    summary_container.columnconfigure((0, 1, 2), weight=1)

    for column, key in enumerate(("summary_model", "summary_prompt", "summary_output")):
        existing = state.get(key)
        if existing is not None:
            try:
                existing.destroy()
            except tk.TclError:
                pass
        widget = AnimatedLabel(summary_container, style="Small.TLabel")
        widget.grid(row=0, column=column, sticky="w", padx=(0, 12))
        state[key] = widget

    # Note: AnimatedLabel widgets use standard ttk.Label styling

    # Make the entire summary scroll as one unit if text is too long
    def _update_summary_scrolling():
        total_width = sum(state[key].winfo_reqwidth() for key in ("summary_model", "summary_prompt", "summary_output") if key in state)
        container_width = summary_container.winfo_width()

        if total_width > container_width and container_width > 0:
            # Enable scrolling animation for overflow text
            for key in ("summary_model", "summary_prompt", "summary_output"):
                if key in state:
                    state[key].check_width()
        else:
            # Disable scrolling if everything fits
            for key in ("summary_model", "summary_prompt", "summary_output"):
                if key in state:
                    state[key].running = False
                    state[key].config(text=state[key].full_text)

    summary_container.bind("<Configure>", lambda e: _update_summary_scrolling())

    # Store the function reference for use in update_summary
    state["_update_summary_scrolling"] = _update_summary_scrolling

    # Store reference to summary container for scrolling
    state["summary_container"] = summary_container

    # Now update summary after container is properly initialized
    update_summary(state)

    # Update scrolling after initial summary setup
    def _initial_scroll_update():
        total_width = sum(state[key].winfo_reqwidth() for key in ("summary_model", "summary_prompt", "summary_output") if key in state)
        container_width = summary_container.winfo_width()
        if total_width > container_width and container_width > 0:
            for key in ("summary_model", "summary_prompt", "summary_output"):
                if key in state:
                    state[key].check_width()

    summary_container.after(100, _initial_scroll_update)  # Delay to allow widgets to render

    summary_prompt_var = tk.StringVar(value="")
    summary_output_var = tk.StringVar(value="")
    state["summary_prompt_var"] = summary_prompt_var
    state["summary_output_var"] = summary_output_var


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

    state["status_label"] = ttk.Label(footer, textvariable=state["status_var"], style="Status.TLabel")
    state["status_label"].grid(row=0, column=0, sticky="w")

    state["progress_bar"] = ttk.Progressbar(footer, mode="determinate")
    state["progress_bar"].grid(row=0, column=1, sticky="ew", padx=16)

    state["process_button"] = ttk.Button(footer, text="Describe Images", style="Accent.TButton")
    state["process_button"].grid(row=0, column=2, sticky="e", padx=(0, 16))

    state["lbl_token_usage"] = ttk.Label(footer, text="Tokens: 0", style="Status.TLabel")
    state["lbl_token_usage"].grid(row=0, column=3, sticky="e")


def _build_menus(menubar, root, state) -> None:
    """Build the menu bar."""
    file_menu = tk.Menu(menubar, tearoff=False)
    file_menu.add_command(label="Exit", command=root.destroy)
    menubar.add_cascade(label="File", menu=file_menu)

    help_menu = tk.Menu(menubar, tearoff=False)
    help_menu.add_command(label="About", command=lambda: _show_about(state))
    menubar.add_cascade(label="Help", menu=help_menu)


def _build_tab_workflow(frame, state) -> None:
    """Build the workflow tab with context, processing options, and output."""
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    # Sub-notebook for workflow sections
    workflow_notebook = ttk.Notebook(frame)
    workflow_notebook.grid(row=0, column=0, sticky="nsew")

    context_tab = ttk.Frame(workflow_notebook, padding=16)
    processing_tab = ttk.Frame(workflow_notebook, padding=16)
    output_tab = ttk.Frame(workflow_notebook, padding=16)

    for tab in (context_tab, processing_tab, output_tab):
        tab.columnconfigure(0, weight=1)

    workflow_notebook.add(context_tab, text="Context")
    workflow_notebook.add(processing_tab, text="Processing")
    workflow_notebook.add(output_tab, text="Output")

    # === Context Tab ===
    context_card = ttk.Frame(context_tab, style="Card.TFrame", padding=16)
    context_card.grid(row=0, column=0, sticky="nsew")
    context_card.columnconfigure(0, weight=1)
    context_card.rowconfigure(1, weight=1)

    _create_section_header(context_card, "Context Notes").grid(row=0, column=0, sticky="w", pady=(0, 8))
    
    _create_info_label(
        context_card,
        "Add optional context about these images to help the AI generate more accurate descriptions."
    ).grid(row=0, column=1, sticky="w", pady=(0, 8))

    text_frame = ttk.Frame(context_card, style="Section.TFrame")
    text_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 8))
    text_frame.columnconfigure(0, weight=1)
    text_frame.rowconfigure(0, weight=1)

    context_entry = tk.Text(text_frame, height=8, wrap="word", relief="solid", borderwidth=1)
    context_entry.grid(row=0, column=0, sticky="nsew")
    
    context_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=context_entry.yview)
    context_scrollbar.grid(row=0, column=1, sticky="ns")
    context_entry.configure(yscrollcommand=context_scrollbar.set)

    stats_frame = ttk.Frame(context_card, style="Section.TFrame")
    stats_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
    stats_frame.columnconfigure(0, weight=1)

    char_count_var = tk.StringVar(value="0 characters")
    state["context_char_count"] = char_count_var
    
    ttk.Label(stats_frame, textvariable=char_count_var, style="Small.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Button(stats_frame, text="Clear", command=lambda: _clear_context(state), style="Secondary.TButton").grid(
        row=0, column=1, sticky="e"
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

    # === Processing Tab ===
    processing_card = ttk.Frame(processing_tab, style="Card.TFrame", padding=16)
    processing_card.grid(row=0, column=0, sticky="nsew")
    processing_card.columnconfigure((0, 1, 2, 3), weight=1)

    _create_section_header(processing_card, "Processing Options").grid(
        row=0, column=0, columnspan=4, sticky="w", pady=(0, 12)
    )

    # Language options
    ttk.Label(processing_card, text="Filename language:", style="TLabel").grid(
        row=1, column=0, sticky="w", padx=(0, 8), pady=8
    )
    ttk.OptionMenu(
        processing_card,
        state["filename_language"],
        state["filename_language"].get(),
        "English",
        "Persian",
    ).grid(row=1, column=1, sticky="ew", padx=(0, 16), pady=8)

    ttk.Label(processing_card, text="Alt-text language:", style="TLabel").grid(
        row=1, column=2, sticky="w", padx=(0, 8), pady=8
    )
    ttk.OptionMenu(
        processing_card,
        state["alttext_language"],
        state["alttext_language"].get(),
        "English",
        "Persian",
    ).grid(row=1, column=3, sticky="ew", pady=8)

    # Detail options
    ttk.Label(processing_card, text="Name detail level:", style="TLabel").grid(
        row=2, column=0, sticky="w", padx=(0, 8), pady=8
    )
    ttk.OptionMenu(
        processing_card,
        state["name_detail_level"],
        state["name_detail_level"].get(),
        "Detailed",
        "Normal",
        "Minimal",
    ).grid(row=2, column=1, sticky="ew", padx=(0, 16), pady=8)

    ttk.Label(processing_card, text="Vision detail:", style="TLabel").grid(
        row=2, column=2, sticky="w", padx=(0, 8), pady=8
    )
    ttk.OptionMenu(
        processing_card,
        state["vision_detail"],
        state["vision_detail"].get(),
        "auto",
        "high",
        "low",
    ).grid(row=2, column=3, sticky="ew", pady=8)

    # OCR section
    ttk.Separator(processing_card, orient="horizontal").grid(
        row=3, column=0, columnspan=4, sticky="ew", pady=16
    )

    _create_section_header(processing_card, "OCR Settings").grid(
        row=4, column=0, columnspan=4, sticky="w", pady=(0, 8)
    )

    ttk.Checkbutton(
        processing_card,
        text="Enable OCR before compression",
        variable=state["ocr_enabled"]
    ).grid(row=5, column=0, columnspan=4, sticky="w", pady=(0, 8))

    ttk.Label(processing_card, text="Tesseract path:", style="TLabel").grid(
        row=6, column=0, sticky="w", padx=(0, 8), pady=8
    )
    ttk.Entry(processing_card, textvariable=state["tesseract_path"]).grid(
        row=6, column=1, columnspan=2, sticky="ew", padx=(0, 8), pady=8
    )
    ttk.Button(
        processing_card,
        text="Browse",
        command=lambda: _browse_tesseract(state),
        style="TButton"
    ).grid(row=6, column=3, sticky="ew", pady=8)

    ttk.Label(processing_card, text="OCR language:", style="TLabel").grid(
        row=7, column=0, sticky="w", padx=(0, 8), pady=8
    )
    ttk.Entry(processing_card, textvariable=state["ocr_language"], width=10).grid(
        row=7, column=1, sticky="w", pady=8
    )

    _create_info_label(
        processing_card,
        "OCR extracts text from images before compression, improving AI descriptions for text-heavy images."
    ).grid(row=8, column=0, columnspan=4, sticky="w", pady=(8, 0))

    # === Output Tab ===
    output_card = ttk.Frame(output_tab, style="Card.TFrame", padding=16)
    output_card.grid(row=0, column=0, sticky="nsew")
    output_card.columnconfigure(1, weight=1)

    _create_section_header(output_card, "Output Settings").grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 12)
    )

    ttk.Label(output_card, text="Save to:", style="TLabel").grid(
        row=1, column=0, sticky="w", padx=(0, 8), pady=8
    )
    ttk.OptionMenu(
        output_card,
        state["output_folder_option"],
        state["output_folder_option"].get(),
        "Same as input",
        "Pictures",
        "Desktop",
        "Custom",
    ).grid(row=1, column=1, sticky="w", pady=8)

    ttk.Label(output_card, text="Custom folder:", style="TLabel").grid(
        row=2, column=0, sticky="w", padx=(0, 8), pady=8
    )
    custom_output_entry = ttk.Entry(output_card, textvariable=state["custom_output_path"])
    custom_output_entry.grid(row=2, column=1, sticky="ew", padx=(0, 8), pady=8)
    state["custom_output_entry"] = custom_output_entry
    
    ttk.Button(
        output_card,
        text="Browse",
        command=lambda: _select_output_folder(state),
        style="TButton"
    ).grid(row=2, column=2, pady=8)

    ttk.Separator(output_card, orient="horizontal").grid(
        row=3, column=0, columnspan=3, sticky="ew", pady=16
    )

    ttk.Checkbutton(
        output_card,
        text="Show interactive results table after processing",
        variable=state["show_results_table"],
    ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(0, 8))

    _create_info_label(
        output_card,
        "Results are saved in a timestamped session folder containing alt-text reports and renamed images.",
        wraplength=600
    ).grid(row=5, column=0, columnspan=3, sticky="w")


def _build_tab_prompts_model(frame, state) -> None:
    """Build the prompts and model selection tab with redesigned LLM provider section."""
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    # Sub-notebook
    prompts_notebook = ttk.Notebook(frame)
    prompts_notebook.grid(row=0, column=0, sticky="nsew")

    provider_tab = ttk.Frame(prompts_notebook, padding=16)
    prompts_tab = ttk.Frame(prompts_notebook, padding=16)

    for tab in (provider_tab, prompts_tab):
        tab.columnconfigure(0, weight=1)

    prompts_notebook.add(provider_tab, text="LLM Provider")
    prompts_notebook.add(prompts_tab, text="Prompts")

    # === Redesigned Provider Tab ===
    _build_llm_provider_section(provider_tab, state)

    # === Prompts Tab ===
    prompt_card = ttk.Frame(prompts_tab, style="Card.TFrame", padding=16)
    prompt_card.grid(row=0, column=0, sticky="nsew")
    prompt_card.columnconfigure(0, weight=1)
    prompt_card.rowconfigure(2, weight=1)

    _create_section_header(prompt_card, "Prompt Management").grid(
        row=0, column=0, sticky="w", pady=(0, 12)
    )

    # Prompt selection
    selection_frame = ttk.Frame(prompt_card, style="Section.TFrame")
    selection_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
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

    _create_section_header(provider_card, "AI Provider").grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
    )

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
    model_card = ttk.Frame(main_container, style="Card.TFrame", padding=8)
    model_card.grid(row=1, column=0, sticky="ew", pady=(0, 4))
    model_card.columnconfigure(2, weight=1)

    _create_section_header(model_card, "Model Selection").grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
    )

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
            _refresh_model_choices()
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
    api_card = ttk.Frame(main_container, style="Card.TFrame", padding=8)
    api_card.grid(row=2, column=0, sticky="ew", pady=(0, 4))
    api_card.columnconfigure(0, weight=1)

    _create_section_header(api_card, "API Configuration").grid(
        row=0, column=0, sticky="w", pady=(0, 4)
    )

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
    _initialize_provider_ui(state)


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
                    is_valid, message = _validate_api_key("openai", content)
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
                    is_valid, message = _validate_api_key("openrouter", content)
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


def _validate_api_key(provider: str, api_key: str) -> tuple[bool, str]:
    """Validate API key format and provide feedback."""
    if not api_key or not api_key.strip():
        return False, "API key is required"

    api_key = api_key.strip()

    if provider == "openai":
        # OpenAI keys start with 'sk-' and are 51 characters long
        if not api_key.startswith("sk-"):
            return False, "OpenAI API keys should start with 'sk-'"
        if len(api_key) < 40:
            return False, "OpenAI API key appears to be too short"
        if len(api_key) > 60:
            return False, "OpenAI API key appears to be too long"
        return True, "Valid OpenAI API key format"

    elif provider == "openrouter":
        # OpenRouter keys start with 'sk-or-'
        if not api_key.startswith("sk-or-"):
            return False, "OpenRouter API keys should start with 'sk-or-'"
        if len(api_key) < 40:
            return False, "OpenRouter API key appears to be too short"
        return True, "Valid OpenRouter API key format"

    return False, "Unknown provider"


def _update_api_key_validation_display(provider: str, api_key: str, status_label: ttk.Label) -> None:
    """Update the visual validation display for API keys."""
    is_valid, message = _validate_api_key(provider, api_key)

    if not api_key:
        status_label.config(text="Not configured", foreground="#64748b")
    elif is_valid:
        status_label.config(text=f"✓ {message}", foreground="#059669")
    else:
        status_label.config(text=f"⚠ {message}", foreground="#d97706")


def _initialize_provider_ui(state) -> None:
    """Initialize the provider UI state and event handlers."""
    def _refresh_model_choices() -> None:
        provider_key = state["llm_provider"].get()
        models = get_models_for_provider(provider_key)
        menu = state["model_option_menu"]
        menu.delete(0, "end")

        if not models:
            state["model_label_var"].set("No models available")
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

        state["model_label_var"].set(models[current_model].get("label", current_model))

    def _refresh_provider_sections() -> None:
        provider_key = state["llm_provider"].get()
        state["provider_label_var"].set(get_provider_label(provider_key))

        # Show/hide API sections based on selected provider
        if provider_key == "openai":
            state["openai_section"].grid(row=1, column=0, sticky="ew")
            state["openrouter_section"].grid_remove()
        elif provider_key == "openrouter":
            state["openai_section"].grid_remove()
            state["openrouter_section"].grid(row=2, column=0, sticky="ew")
        else:
            # Fallback - hide both if unknown provider
            state["openai_section"].grid_remove()
            state["openrouter_section"].grid_remove()

        # Update provider status
        has_api_key = False
        if provider_key == "openai":
            has_api_key = bool(state["openai_api_key"].get())
        elif provider_key == "openrouter":
            has_api_key = bool(state["openrouter_api_key"].get())

        status_text = "● Ready" if has_api_key else "● Not configured"
        state["provider_status_var"].set(status_text)

        # Show/hide refresh button based on provider
        refresh_button = state.get("refresh_openrouter_button")
        if refresh_button:
            if provider_key == "openrouter":
                refresh_button.grid(row=0, column=2, sticky="e", padx=(16, 0))
            else:
                refresh_button.grid_remove()

    def _sync_model_label(*_) -> None:
        provider_key = state["llm_provider"].get()
        models = get_models_for_provider(provider_key)
        current_model = state["llm_model"].get()
        model_info = models.get(current_model, {})
        state["model_label_var"].set(model_info.get("label", current_model))

        # Update capabilities display
        capabilities = model_info.get("capabilities", ["text"])
        capabilities_list = []
        if "vision" in capabilities:
            capabilities_list.append("Vision")
        if "text" in capabilities:
            capabilities_list.append("Text")
        if "audio" in capabilities:
            capabilities_list.append("Audio")

        capabilities_text = ", ".join(capabilities_list) if capabilities_list else "Text"
        state["model_capabilities_label"].config(text=f"Capabilities: {capabilities_text}")

        # Update pricing display with enhanced information
        _update_model_pricing_display(state, provider_key, current_model, model_info)

    def _update_model_pricing_display(state, provider_key: str, model_id: str, model_info: dict) -> None:
        """Update the model pricing display with enhanced information."""
        try:
            pricing_label = state.get("lbl_model_pricing")
            if not pricing_label:
                return

            if not model_info:
                pricing_label.config(text="Model information unavailable")
                return

            provider_label = get_provider_label(provider_key)
            model_label = model_info.get("label", model_id)

            # Enhanced pricing information
            pricing_info = []

            # Basic pricing
            pricing_text = format_pricing(provider_key, model_id)
            if pricing_text and pricing_text != "Pricing unavailable":
                pricing_info.append(pricing_text)

            # Provider and model info (cleaner formatting)
            info_line = f"{provider_label} • {model_label}".replace("  ", " ").strip()
            pricing_info.append(info_line)

            # Vendor information if available
            vendor = model_info.get("vendor")
            if vendor:
                pricing_info.append(f"Vendor: {vendor}")

            # Context window if available
            context_window = model_info.get("context_window")
            if context_window:
                pricing_info.append(f"Context: {context_window:,}","tokens")

            # Special features
            features = []
            if model_info.get("supports_function_calling"):
                features.append("Function Calling")
            if model_info.get("supports_json_mode"):
                features.append("JSON Mode")
            if model_info.get("is_free") or (provider_key == "openrouter" and "free" in model_id.lower()):
                features.append("Free")

            if features:
                pricing_info.append(f"Features: {', '.join(features)}")

            # Join all information
            full_text = "\n".join(pricing_info)
            pricing_label.config(text=full_text)

        except Exception as e:
            pricing_label.config(text=f"Error loading model info: {str(e)}")

    def _update_api_status_labels() -> None:
        # Update OpenAI status with validation
        openai_key = state["openai_api_key"].get()
        _update_api_key_validation_display("openai", openai_key, state["openai_status_label"])

        # Update OpenRouter status with validation
        openrouter_key = state["openrouter_api_key"].get()
        _update_api_key_validation_display("openrouter", openrouter_key, state["openrouter_status_label"])

        # Update provider status indicator
        _refresh_provider_sections()

    # Set up event handlers
    state["llm_provider"].trace_add(
        "write", lambda *_: (_refresh_provider_sections(), _refresh_model_choices())
    )
    state["llm_model"].trace_add("write", _sync_model_label)
    state["openai_api_key"].trace_add("write", lambda *_: _update_api_status_labels())
    state["openrouter_api_key"].trace_add("write", lambda *_: _update_api_status_labels())

    # Add real-time validation for API keys
    def _add_realtime_validation():
        """Add real-time validation feedback for API key entries."""

        def validate_openai_realtime(*_):
            key = state["openai_api_key"].get()
            if key and len(key) > 10:  # Only validate if key is long enough
                is_valid, message = _validate_api_key("openai", key)
                if is_valid:
                    state["openai_api_entry"].config(style="TEntry")  # Normal style
                else:
                    state["openai_api_entry"].config(style="Warning.TEntry")  # Warning style
            else:
                state["openai_api_entry"].config(style="TEntry")  # Normal style

        def validate_openrouter_realtime(*_):
            key = state["openrouter_api_key"].get()
            if key and len(key) > 10:  # Only validate if key is long enough
                is_valid, message = _validate_api_key("openrouter", key)
                if is_valid:
                    state["openrouter_api_entry"].config(style="TEntry")  # Normal style
                else:
                    state["openrouter_api_entry"].config(style="Warning.TEntry")  # Warning style
            else:
                state["openrouter_api_entry"].config(style="TEntry")  # Normal style

        # Add validation traces
        state["openai_api_key"].trace_add("write", validate_openai_realtime)
        state["openrouter_api_key"].trace_add("write", validate_openrouter_realtime)

    # Initialize the UI
    _refresh_model_choices()
    _refresh_provider_sections()  # This must come after model choices are set up
    _update_api_status_labels()
    _add_realtime_validation()


def _build_tab_advanced(frame, state) -> None:
    """Build the advanced settings tab."""
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    
    advanced_notebook = ttk.Notebook(frame)
    advanced_notebook.grid(row=0, column=0, sticky="nsew")

    appearance_tab = ttk.Frame(advanced_notebook, padding=16)
    network_tab = ttk.Frame(advanced_notebook, padding=16)
    maintenance_tab = ttk.Frame(advanced_notebook, padding=16)

    for tab in (appearance_tab, network_tab, maintenance_tab):
        tab.columnconfigure(0, weight=1)

    advanced_notebook.add(appearance_tab, text="Appearance")
    advanced_notebook.add(network_tab, text="Network")
    advanced_notebook.add(maintenance_tab, text="Maintenance")

    _build_appearance_section(appearance_tab, state)
    _build_proxy_section(network_tab, state)
    _build_maintenance_section(maintenance_tab, state)


def _build_log(parent, state) -> None:
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


def _build_appearance_section(parent, state) -> None:
    """Build the appearance settings section."""
    card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    card.grid(row=0, column=0, sticky="nsew")
    card.columnconfigure(1, weight=1)

    _create_section_header(card, "Theme Selection").grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
    )

    ttk.Label(card, text="UI Theme:", style="TLabel").grid(
        row=1, column=0, sticky="w", padx=(0, 8), pady=8
    )
    
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
        "Monokai",
        "Solarized Light",
        "Dracula",
    ).grid(row=1, column=1, sticky="w", pady=8)

    _create_info_label(
        card,
        "Choose a color scheme that suits your preference. Changes apply immediately."
    ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 0))


def _build_proxy_section(parent, state) -> None:
    """Build the network proxy settings section."""
    card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    card.grid(row=0, column=0, sticky="nsew")
    card.columnconfigure(0, weight=1)

    # Header
    header = ttk.Frame(card, style="Section.TFrame")
    header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
    header.columnconfigure(0, weight=1)

    _create_section_header(header, "Proxy Configuration").grid(
        row=0, column=0, sticky="w", pady=(0, 8)
    )

    control_frame = ttk.Frame(header, style="Section.TFrame")
    control_frame.grid(row=1, column=0, sticky="ew")
    control_frame.columnconfigure(0, weight=1)

    ttk.Checkbutton(
        control_frame,
        text="Use proxy for network requests",
        variable=state["proxy_enabled"],
    ).grid(row=0, column=0, sticky="w")

    ttk.Button(
        control_frame,
        text="Refresh Detection",
        command=lambda: _refresh_detected_proxy(state),
        style="Secondary.TButton",
    ).grid(row=0, column=1, sticky="e")

    # Proxy info
    info_frame = ttk.Frame(card, style="Section.TFrame")
    info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))
    info_frame.columnconfigure(0, weight=1)

    ttk.Label(info_frame, text="Detected system proxy:", style="TLabel").grid(
        row=0, column=0, sticky="w", pady=(0, 4)
    )
    ttk.Label(
        info_frame,
        textvariable=state["proxy_detected_label"],
        style="Small.TLabel",
        justify="left",
    ).grid(row=1, column=0, sticky="w", padx=(12, 0), pady=(0, 12))

    ttk.Label(info_frame, text="Effective proxy in use:", style="TLabel").grid(
        row=2, column=0, sticky="w", pady=(0, 4)
    )
    ttk.Label(
        info_frame,
        textvariable=state["proxy_effective_label"],
        style="Small.TLabel",
        justify="left",
    ).grid(row=3, column=0, sticky="w", padx=(12, 0))

    # Override
    override_frame = ttk.Frame(card, style="Section.TFrame")
    override_frame.grid(row=2, column=0, sticky="ew")
    override_frame.columnconfigure(0, weight=1)

    ttk.Label(override_frame, text="Custom override (optional):", style="TLabel").grid(
        row=0, column=0, sticky="w", pady=(0, 8)
    )
    
    override_entry = ttk.Entry(override_frame, textvariable=state["proxy_override"])
    override_entry.grid(row=1, column=0, sticky="ew")
    state["proxy_override_entry"] = override_entry

    _create_info_label(
        override_frame,
        "Leave blank to use detected system proxy. Format: http://proxy.example.com:8080"
    ).grid(row=2, column=0, sticky="w", pady=(8, 0))


def _build_maintenance_section(parent, state) -> None:
    """Build the maintenance settings section."""
    card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    card.grid(row=0, column=0, sticky="nsew")
    card.columnconfigure(0, weight=1)

    _create_section_header(card, "Settings & Maintenance").grid(
        row=0, column=0, sticky="w", pady=(0, 16)
    )

    # Primary actions
    primary_frame = ttk.Frame(card, style="Section.TFrame")
    primary_frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))

    ttk.Button(
        primary_frame,
        text="Save Settings",
        command=lambda: _save_settings(state),
        style="Accent.TButton"
    ).pack(side="left", padx=(0, 8))
    
    ttk.Button(
        primary_frame,
        text="Open Config Folder",
        command=open_config_folder,
        style="TButton"
    ).pack(side="left")

    ttk.Separator(card, orient="horizontal").grid(
        row=2, column=0, sticky="ew", pady=(0, 16)
    )

    # Secondary actions
    _create_section_header(card, "Reset Options", style="Small.TLabel").grid(
        row=3, column=0, sticky="w", pady=(0, 8)
    )

    secondary_frame = ttk.Frame(card, style="Section.TFrame")
    secondary_frame.grid(row=4, column=0, sticky="ew")

    ttk.Button(
        secondary_frame,
        text="Reset to Defaults",
        command=lambda: state["reset_config_callback"](),
        style="Secondary.TButton"
    ).pack(side="left", padx=(0, 8))
    
    ttk.Button(
        secondary_frame,
        text="Reset Token Usage",
        command=lambda: _reset_token_usage(state),
        style="Secondary.TButton"
    ).pack(side="left", padx=(0, 8))
    
    ttk.Button(
        secondary_frame,
        text="Reset Statistics",
        command=lambda: _reset_global_stats(state),
        style="Secondary.TButton"
    ).pack(side="left")

    _create_info_label(
        card,
        "Settings are automatically saved when closing the application. Use 'Save Settings' to save immediately."
    ).grid(row=5, column=0, sticky="w", pady=(16, 0))


# === Helper Functions ===

def _update_proxy_controls(state) -> None:
    """Enable or disable proxy override entry based on proxy enabled state."""
    entry = state.get("proxy_override_entry")
    if entry is None:
        return
    entry_state = "normal" if state.get("proxy_enabled") and state["proxy_enabled"].get() else "disabled"
    entry.config(state=entry_state)


def _update_proxy_effective_label(state) -> None:
    """Update the effective proxy label with current settings."""
    if "proxy_effective_label" not in state:
        return
    enabled_var = state.get("proxy_enabled")
    override_var = state.get("proxy_override")
    enabled = bool(enabled_var.get()) if enabled_var is not None else True
    override = override_var.get().strip() if override_var is not None else ""
    proxies = get_requests_proxies(enabled=enabled, override=override or None)
    state["proxy_effective_label"].set(_format_proxy_mapping(proxies))


def _apply_proxy_preferences(state, *, force: bool = False) -> None:
    """Apply proxy preferences and update UI."""
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
    """Refresh the detected system proxy settings."""
    detected = reload_system_proxies()
    if "proxy_detected_label" in state:
        state["proxy_detected_label"].set(_format_proxy_mapping(detected))
    configure_global_proxy(force=True)
    _update_proxy_effective_label(state)


def _update_provider_status_labels(state) -> None:
    """Update the API key status labels."""
    openai_label = state.get("openai_status_label")
    if openai_label is not None:
        is_set = bool(state.get("openai_api_key").get()) if "openai_api_key" in state else False
        openai_label.configure(text="✓ Ready" if is_set else "⚠ Not set")

    openrouter_label = state.get("openrouter_status_label")
    if openrouter_label is not None:
        is_set = bool(state.get("openrouter_api_key").get()) if "openrouter_api_key" in state else False
        openrouter_label.configure(text="✓ Ready" if is_set else "⚠ Not set")


def append_monitor_colored(state, message: str, level: str = "info") -> None:
    """Append a colored message to the activity log."""
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
    """Copy the activity log to clipboard."""
    if "log_text" in state:
        text = state["log_text"].get("1.0", "end")
        if pyperclip is None:
            set_status(state, "Clipboard support not available")
            return
        pyperclip.copy(text)
        set_status(state, "Log copied to clipboard")


def _write_monitor_line_colored(state, log_item) -> None:
    """Write a colored line to the activity log."""
    if "log_text" not in state:
        return

    text_widget = state["log_text"]
    text, level = log_item

    text_widget.config(state="normal")
    text_widget.insert("end", text + "\n", level)
    text_widget.see("end")
    text_widget.config(state="disabled")


def _clear_context(state, *, silent: bool = False) -> None:
    """Clear the context text area."""
    if "context_widget" in state:
        state["context_widget"].delete("1.0", "end")
    state["context_text"].set("")
    if "context_char_count" in state:
        state["context_char_count"].set("0 characters")
    if not silent:
        set_status(state, "Context cleared")


def _select_input(state) -> None:
    """Open file dialog to select input folder."""
    temp_root = tk.Tk()
    temp_root.withdraw()
    path = filedialog.askopenfilename(
        title="Select an image file or any file in the target folder",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.heic *.heif"), ("All files", "*.*")],
    )
    temp_root.destroy()

    if not path:
        return

    if os.path.isdir(path):
        input_path = path
    else:
        input_path = os.path.dirname(path)

    cleanup_temp_drop_folder(state)
    state["input_path"].set(input_path)
    recursive = state["recursive_search"].get()
    count = get_image_count_in_folder(input_path, recursive)
    state["image_count"].set(f"{count} image(s)")
    set_status(state, f"Ready to process {count} image(s)")
    _clear_monitor(state)
    update_summary(state)
    _clear_context(state, silent=True)


def _select_output_folder(state) -> None:
    """Open folder dialog to select custom output folder."""
    path = filedialog.askdirectory()
    if path:
        state["custom_output_path"].set(path)


def _browse_tesseract(state) -> None:
    """Open file dialog to select Tesseract executable."""
    path = filedialog.askopenfilename(filetypes=[("Tesseract Executable", "tesseract.exe")])
    if path:
        state["tesseract_path"].set(path)


def _save_settings(state) -> None:
    """Save current settings to config file."""
    geometry = state["root"].winfo_geometry()

    if "context_widget" in state:
        state["context_text"].set(state["context_widget"].get("1.0", "end").strip())

    save_config(state, geometry)
    apply_theme(state["root"], state["ui_theme"].get())
    messagebox.showinfo("Settings Saved", "✓ Your settings have been saved successfully.")


def _reset_token_usage(state) -> None:
    """Reset the token usage counter."""
    state["total_tokens"].set(0)
    update_token_label(state)
    append_monitor_colored(state, "Token usage reset to 0", "warn")


def _reset_global_stats(state) -> None:
    """Reset global statistics."""
    if "global_images_count" in state:
        state["global_images_count"].set(0)
        append_monitor_colored(state, "Global statistics reset", "warn")
    else:
        append_monitor_colored(state, "No statistics to reset", "warn")


def _show_about(state) -> None:
    """Show the About dialog."""
    import webbrowser

    root = state.get("root")
    about_dialog = tk.Toplevel(root)
    about_dialog.title("About Altomatic")
    about_dialog.geometry("550x350")
    about_dialog.resizable(False, False)
    
    current_theme = state["ui_theme"].get()
    palette = PALETTE.get(current_theme, PALETTE["Arctic Light"])
    about_dialog.configure(bg=palette["background"])
    _apply_window_icon(about_dialog)
    apply_theme_to_window(about_dialog, current_theme)

    container = ttk.Frame(about_dialog, padding=24, style="Card.TFrame")
    container.pack(fill="both", expand=True)
    container.columnconfigure(0, weight=1)

    # Title
    ttk.Label(
        container,
        text="Altomatic",
        font=("Segoe UI Semibold", 18)
    ).grid(row=0, column=0, sticky="w", pady=(0, 4))

    # Subtitle
    ttk.Label(
        container,
        text="AI-Powered Image Description Tool",
        style="Small.TLabel"
    ).grid(row=1, column=0, sticky="w", pady=(0, 20))

    # Description
    description = (
        "Altomatic helps you batch-generate descriptive filenames and alt text "
        "for images using advanced multimodal language models.\n\n"
        "Features include:\n"
        "• Support for multiple AI providers (OpenAI, OpenRouter)\n"
        "• Customizable prompts and templates\n"
        "• OCR integration for text extraction\n"
        "• Batch processing with progress tracking\n"
        "• Multiple theme options"
    )
    ttk.Label(
        container,
        text=description,
        wraplength=500,
        justify="left"
    ).grid(row=2, column=0, sticky="w", pady=(0, 20))

    # Links
    link_frame = ttk.Frame(container, style="Section.TFrame")
    link_frame.grid(row=3, column=0, sticky="w", pady=(0, 20))

    github_link = ttk.Label(
        link_frame,
        text="View on GitHub →",
        style="Accent.TLabel",
        cursor="hand2"
    )
    github_link.pack(side="left")
    github_link.bind(
        "<Button-1>",
        lambda _: webbrowser.open_new("https://github.com/NaxonM/Altomatic/")
    )

    # Credits
    ttk.Label(
        container,
        text="Created by Mehdi",
        style="Small.TLabel"
    ).grid(row=4, column=0, sticky="w")

    # Close button
    ttk.Button(
        container,
        text="Close",
        command=about_dialog.destroy,
        style="Accent.TButton"
    ).grid(row=5, column=0, sticky="e", pady=(20, 0))