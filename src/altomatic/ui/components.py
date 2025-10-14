"""UI construction helpers."""

from __future__ import annotations

import os
import shutil
import tkinter as tk
from importlib import resources
from tkinter import filedialog, messagebox, simpledialog, ttk

import pyperclip

from ..config import open_config_folder, save_config
from ..models import AVAILABLE_MODELS, DEFAULT_MODEL, format_pricing
from ..prompts import get_prompt_template, load_prompts, save_prompts
from ..utils import get_image_count_in_folder, slugify
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
    if "lbl_model_pricing" in state:
        model_id = state["openai_model"].get()
        details = AVAILABLE_MODELS.get(model_id)
        if details:
            state["lbl_model_pricing"].config(
                text=f"Model: {details['label']}\n{format_pricing(model_id)}"
            )
        else:
            state["lbl_model_pricing"].config(text="Model pricing unavailable")


def update_summary(state) -> None:
    if "summary_model" not in state:
        return

    model_id = state["openai_model"].get()
    model_label = AVAILABLE_MODELS.get(model_id, {}).get("label", model_id)
    state["summary_model"].set(f"Model: {model_label}")

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

    model_id = state["openai_model"].get()
    model_label = AVAILABLE_MODELS.get(model_id, {}).get("label", model_id)
    state["summary_model"].set(f"Model: {model_label}")

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
    widget.insert("1.0", f"{label}\n\n{template}".strip())
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
    editor.geometry(_scaled_geometry(editor, 800, 630))
    editor.grab_set()
    current_theme = state["ui_theme"].get()
    palette = PALETTE.get(current_theme, PALETTE["Default Light"])
    editor.configure(bg=palette["background"])
    _apply_window_icon(editor)

    prompts = load_prompts()
    working = {key: dict(value) for key, value in prompts.items()}

    frame = ttk.Frame(editor, padding=10, style="Section.TFrame")
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(1, weight=1)

    ttk.Label(frame, text="Available prompts:").grid(row=0, column=0, sticky="w")
    listbox = tk.Listbox(
        frame,
        exportselection=False,
        height=8,
        highlightthickness=0,
        relief="flat",
        activestyle="none",
    )
    listbox.grid(row=1, column=0, sticky="nsw")
    listbox.configure(
        bg=palette["surface"],
        fg=palette["foreground"],
        selectbackground=palette["primary"],
        selectforeground=palette["primary-foreground"],
        highlightbackground=palette["surface-2"],
        highlightcolor=palette["surface-2"],
    )

    label_var = tk.StringVar()
    template_text = tk.Text(
        frame,
        wrap="word",
        relief="flat",
        borderwidth=1,
        highlightthickness=1,
    )
    template_text.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
    template_text.configure(
        bg=palette["surface"],
        fg=palette["foreground"],
        insertbackground=palette["foreground"],
        highlightbackground=palette["surface-2"],
        highlightcolor=palette["surface-2"],
    )

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=template_text.yview)
    scrollbar.grid(row=1, column=2, sticky="ns")
    template_text.configure(yscrollcommand=scrollbar.set)

    button_frame = ttk.Frame(editor, padding=(10, 0), style="Section.TFrame")
    button_frame.pack(fill="x")

    current_key = tk.StringVar(value=state["prompt_key"].get())

    def refresh_list(select_key: str | None = None) -> None:
        listbox.delete(0, "end")
        for key, value in working.items():
            listbox.insert("end", value.get("label", key))
        keys = list(working.keys())
        if select_key and select_key in working:
            index = keys.index(select_key)
        elif current_key.get() in working:
            index = keys.index(current_key.get())
        else:
            index = 0 if keys else -1
        if index >= 0:
            listbox.select_set(index)
            listbox.event_generate("<<ListboxSelect>>")

    def load_selected(event=None) -> None:
        selection = listbox.curselection()
        if not selection:
            return
        key = list(working.keys())[selection[0]]
        current_key.set(key)
        entry = working[key]
        label_var.set(entry.get("label", key))
        template_text.delete("1.0", "end")
        template_text.insert("1.0", entry.get("template", ""))

    listbox.bind("<<ListboxSelect>>", load_selected)

    ttk.Label(button_frame, text="Prompt label:").grid(row=0, column=0, sticky="w")
    label_entry = ttk.Entry(button_frame, textvariable=label_var, width=40)
    label_entry.grid(row=0, column=1, sticky="w")

    def add_prompt() -> None:
        name = simpledialog.askstring("New Prompt", "Enter a label for the new prompt:", parent=editor)
        if not name:
            return
        key = slugify(name)
        if not key:
            key = f"prompt{len(working)+1}"
        if key in working:
            messagebox.showerror("Duplicate", "A prompt with that name already exists.", parent=editor)
            return
        working[key] = {"label": name.strip(), "template": ""}
        refresh_list(select_key=key)
        label_entry.focus_set()

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

    ttk.Button(button_frame, text="Add", command=add_prompt, style="Accent.TButton").grid(
        row=1, column=0, pady=10, sticky="w"
    )
    ttk.Button(button_frame, text="Delete", command=delete_prompt, style="Secondary.TButton").grid(
        row=1, column=1, pady=10, sticky="w", padx=5
    )
    ttk.Button(button_frame, text="Save", command=save_changes, style="TButton").grid(
        row=1, column=2, pady=10, sticky="w", padx=5
    )
    ttk.Button(button_frame, text="Save & Close", command=save_and_close, style="Accent.TButton").grid(
        row=1, column=3, pady=10, sticky="w", padx=5
    )
    ttk.Button(button_frame, text="Close", command=editor.destroy, style="TButton").grid(
        row=1, column=4, pady=10, sticky="w", padx=5
    )

    refresh_list(select_key=current_key.get())
    apply_theme_to_window(editor, current_theme)
    editor.bind("<Control-s>", save_changes)
    listbox.bind("<Delete>", delete_prompt)


def build_ui(root, user_config):
    """Build the main UI and stitch components together."""
    main_frame = ttk.Frame(root, padding=16)
    main_frame.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # Configure main_frame for a 2-column layout
    main_frame.columnconfigure(0, weight=1, minsize=450)
    main_frame.columnconfigure(1, weight=1, minsize=400)
    main_frame.rowconfigure(0, weight=1)  # Main content row
    main_frame.rowconfigure(1, weight=0)  # Footer row

    menubar = tk.Menu(root)
    root.config(menu=menubar)

    prompts_data = load_prompts()
    prompt_names = list(prompts_data.keys()) or ["default"]
    active_prompt = user_config.get("prompt_key", "default")
    if active_prompt not in prompts_data:
        active_prompt = prompt_names[0]

    # Gracefully handle missing or invalid model from config
    user_model = user_config.get("openai_model", DEFAULT_MODEL)
    if user_model.lower() not in AVAILABLE_MODELS:
        user_model = DEFAULT_MODEL

    # Central state dictionary, passed around to UI functions
    state = {
        "root": root,
        "menubar": menubar,
        # Config-backed state
        "input_type": tk.StringVar(value="Folder"),
        "input_path": tk.StringVar(value=""),
        "custom_output_path": tk.StringVar(value=user_config.get("custom_output_path", "")),
        "output_folder_option": tk.StringVar(value=user_config.get("output_folder_option", "Same as input")),
        "openai_api_key": tk.StringVar(value=user_config.get("openai_api_key", "")),
        "filename_language": tk.StringVar(value=user_config.get("filename_language", "English")),
        "alttext_language": tk.StringVar(value=user_config.get("alttext_language", "English")),
        "name_detail_level": tk.StringVar(value=user_config.get("name_detail_level", "Detailed")),
        "vision_detail": tk.StringVar(value=user_config.get("vision_detail", "auto")),
        "ocr_enabled": tk.BooleanVar(value=user_config.get("ocr_enabled", False)),
        "tesseract_path": tk.StringVar(value=user_config.get("tesseract_path", "")),
        "ocr_language": tk.StringVar(value=user_config.get("ocr_language", "eng")),
        "ui_theme": tk.StringVar(value=user_config.get("ui_theme", "Default Light")),
        "openai_model": tk.StringVar(value=user_model),
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
        # Summary state
        "summary_model": tk.StringVar(),
        "summary_prompt": tk.StringVar(),
        "summary_output": tk.StringVar(),
    }

    # --- Create main layout containers ---
    left_frame = ttk.Frame(main_frame)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
    left_frame.rowconfigure(1, weight=1)
    left_frame.columnconfigure(0, weight=1)

    # Build the UI components into the new layout
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

    state["openai_model"].trace_add("write", lambda *_: (update_model_pricing(state), update_summary(state)))
    state["prompt_key"].trace_add("write", lambda *_: (update_prompt_preview(state), update_summary(state)))
    state["output_folder_option"].trace_add("write", on_output_folder_change)
    state["custom_output_path"].trace_add("write", lambda *_: update_summary(state))
    state["ui_theme"].trace_add("write", lambda *_, **kwargs: apply_theme(root, state["ui_theme"].get()))

    # Trigger initial state correctly
    on_output_folder_change()
    update_model_pricing(state)
    update_prompt_preview(state)
    update_summary(state)

    return state


def _build_header(parent, state) -> None:
    """Build the top summary header."""
    header = ttk.Frame(parent, style="Card.TFrame", padding=12)
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure((0, 1, 2), weight=1)
    ttk.Label(header, textvariable=state["summary_model"], style="Card.TLabel").grid(row=0, column=0)
    ttk.Label(header, textvariable=state["summary_prompt"], style="Card.TLabel").grid(row=0, column=1)
    ttk.Label(header, textvariable=state["summary_output"], style="Card.TLabel").grid(row=0, column=2)


def _build_notebook(parent, state) -> ttk.Notebook:
    """Build the main notebook for settings."""
    notebook = ttk.Notebook(parent)
    notebook.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
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
    frame.columnconfigure(1, weight=1)

    # --- Input Section ---
    input_frame = ttk.Labelframe(frame, text="Input", style="Section.TLabelframe")
    input_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")
    input_frame.columnconfigure(1, weight=1)

    ttk.Label(input_frame, text="Input Type:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    option = ttk.OptionMenu(input_frame, state["input_type"], state["input_type"].get(), "Folder", "File")
    option.grid(row=0, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(input_frame, text="Input Path:", style="TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    entry = ttk.Entry(input_frame, textvariable=state["input_path"], width=50)
    entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
    state["input_entry"] = entry
    ttk.Button(input_frame, text="Browse", command=lambda: _select_input(state), style="TButton").grid(
        row=1, column=2, padx=5, pady=5
    )

    ttk.Label(input_frame, textvariable=state["image_count"], style="Small.TLabel").grid(
        row=2, column=1, columnspan=2, sticky="w", padx=5
    )

    ttk.Label(input_frame, text="Context:", style="TLabel").grid(
        row=3, column=0, sticky="nw", padx=5, pady=(5, 0)
    )
    context_frame = ttk.Frame(input_frame, style="Section.TFrame")
    context_frame.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=(5, 5))
    context_frame.columnconfigure(0, weight=1)
    context_entry = tk.Text(
        context_frame, height=4, width=50, wrap="word", relief="solid", borderwidth=1
    )
    context_entry.grid(row=0, column=0, sticky="nsew")
    context_scrollbar = ttk.Scrollbar(context_frame, orient="vertical", command=context_entry.yview)
    context_scrollbar.grid(row=0, column=1, sticky="ns")
    context_entry.configure(yscrollcommand=context_scrollbar.set)

    char_count_var = tk.StringVar(value="0 characters")
    state["context_char_count"] = char_count_var
    char_count_label = ttk.Label(input_frame, textvariable=char_count_var, style="Small.TLabel")
    char_count_label.grid(row=4, column=1, sticky="w", padx=5)

    ttk.Button(
        input_frame,
        text="Clear",
        command=lambda: _clear_context(state),
        style="Secondary.TButton",
    ).grid(row=4, column=2, sticky="e", padx=5)

    def update_char_count(event=None):
        content = context_entry.get("1.0", "end-1c")
        count = len(content)
        char_count_var.set(f"{count} characters")
        state["context_text"].set(content)

    context_entry.bind("<KeyRelease>", update_char_count)
    state["context_widget"] = context_entry

    # Load initial text if any and update counter
    initial_text = state["context_text"].get()
    if initial_text:
        context_entry.insert("1.0", initial_text)
        update_char_count()

    # --- Output Section ---
    output_frame = ttk.Labelframe(frame, text="Output", style="Section.TLabelframe", padding=16)
    output_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=16)
    output_frame.columnconfigure(1, weight=1)

    ttk.Label(output_frame, text="Save to:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    ttk.OptionMenu(
        output_frame,
        state["output_folder_option"],
        state["output_folder_option"].get(),
        "Same as input",
        "Pictures",
        "Desktop",
        "Custom",
    ).grid(row=0, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(output_frame, text="Custom Folder:", style="TLabel").grid(
        row=1, column=0, sticky="w", padx=5, pady=5
    )
    custom_output_entry = ttk.Entry(output_frame, textvariable=state["custom_output_path"], width=50)
    custom_output_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
    state["custom_output_entry"] = custom_output_entry
    ttk.Button(
        output_frame, text="Browse", command=lambda: _select_output_folder(state), style="TButton"
    ).grid(row=1, column=2, padx=5, pady=5)
    info_label = ttk.Label(
        output_frame,
        text="An alt-text report and renamed image files will be saved in a new session folder.",
        style="Small.TLabel",
        wraplength=400,
        justify="left",
    )
    info_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 5))


def _build_tab_prompts_model(frame, state) -> None:
    """Build the 'Prompts & Model' tab."""
    frame.columnconfigure(1, weight=1)

    # --- Credentials & Model ---
    model_frame = ttk.Labelframe(frame, text="API & Model", style="Section.TLabelframe", padding=16)
    model_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")
    model_frame.columnconfigure(1, weight=1)

    ttk.Label(model_frame, text="OpenAI API Key:", style="TLabel").grid(
        row=0, column=0, sticky="w", padx=5, pady=5
    )

    api_key_frame = ttk.Frame(model_frame, style="Section.TFrame")
    api_key_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
    api_key_frame.columnconfigure(0, weight=1)

    api_key_entry = ttk.Entry(api_key_frame, textvariable=state["openai_api_key"], show="*", width=50)
    api_key_entry.grid(row=0, column=0, sticky="ew")
    state["api_key_entry"] = api_key_entry
    show_api_key = tk.BooleanVar()

    def toggle_api_key():
        api_key_entry.config(show="" if show_api_key.get() else "*")

    ttk.Checkbutton(api_key_frame, text="Show", variable=show_api_key, command=toggle_api_key).grid(
        row=0, column=1, padx=(5, 0)
    )

    def paste_api_key():
        try:
            if content := pyperclip.paste():
                state["openai_api_key"].set(content)
                set_status(state, "API Key pasted from clipboard.")
            else:
                set_status(state, "Clipboard is empty.")
        except (pyperclip.PyperclipException, tk.TclError):
            set_status(state, "Could not access clipboard.")

    ttk.Button(api_key_frame, text="Paste", command=paste_api_key, style="TButton").grid(
        row=0, column=2, padx=5
    )

    ttk.Label(model_frame, text="OpenAI Model:", style="TLabel").grid(
        row=1, column=0, sticky="w", padx=5, pady=5
    )
    model_labels = {v["label"]: k for k, v in AVAILABLE_MODELS.items()}
    model_menu = ttk.OptionMenu(
        model_frame,
        state["openai_model"],
        AVAILABLE_MODELS[state["openai_model"].get()]["label"],
        *model_labels.keys(),
        command=lambda label: state["openai_model"].set(model_labels[label]),
    )
    model_menu.grid(row=1, column=1, sticky="w", padx=5, pady=5)
    state["lbl_model_pricing"] = ttk.Label(
        model_frame, text="", justify="left", style="Small.TLabel"
    )
    state["lbl_model_pricing"].grid(row=2, column=1, sticky="w", padx=5, pady=(0, 10))

    # --- Prompt Management ---
    prompt_frame = ttk.Labelframe(frame, text="Prompt", style="Section.TLabelframe", padding=16)
    prompt_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=16)
    prompt_frame.columnconfigure(1, weight=1)

    ttk.Label(prompt_frame, text="Prompt Preset:", style="TLabel").grid(
        row=0, column=0, sticky="w", padx=5, pady=5
    )

    prompt_labels = {v["label"]: k for k, v in state["prompts"].items()}

    # Need a separate variable for the label, since the state tracks the key
    prompt_label_var = tk.StringVar(value=state["prompts"][state["prompt_key"].get()]["label"])

    def on_prompt_select(label):
        key = prompt_labels[label]
        state["prompt_key"].set(key)
        prompt_label_var.set(label)

    prompt_menu = ttk.OptionMenu(
        prompt_frame,
        prompt_label_var,
        prompt_label_var.get(),
        *prompt_labels.keys(),
        command=on_prompt_select,
    )
    prompt_menu.grid(row=0, column=1, sticky="w", padx=5, pady=5)
    state["prompt_option_widget"] = prompt_menu
    state["prompt_option_menu"] = prompt_menu["menu"]
    ttk.Button(
        prompt_frame,
        text="Edit Prompts...",
        command=lambda: open_prompt_editor(state),
        style="Secondary.TButton",
    ).grid(row=0, column=2, sticky="w", padx=5)

    preview_frame = ttk.Frame(prompt_frame, style="Section.TFrame")
    preview_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=(5, 10))
    preview_frame.columnconfigure(0, weight=1)
    prompt_preview = tk.Text(
        preview_frame,
        height=8,
        width=50,
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
    refresh_prompt_choices(state)


def _build_tab_advanced(frame, state) -> None:
    """Build the 'Advanced' settings tab."""
    frame.columnconfigure(1, weight=1)

    # --- Appearance ---
    appearance_frame = ttk.Labelframe(
        frame, text="Appearance & Language", style="Section.TLabelframe", padding=16
    )
    appearance_frame.grid(row=0, column=0, sticky="nsew")
    appearance_frame.columnconfigure(1, weight=1)

    ttk.Label(appearance_frame, text="UI Theme:", style="TLabel").grid(
        row=0, column=0, sticky="w", padx=5, pady=5
    )
    ttk.OptionMenu(
        appearance_frame,
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
    ).grid(row=0, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(appearance_frame, text="Filename Language:", style="TLabel").grid(
        row=1, column=0, sticky="w", padx=5, pady=5
    )
    ttk.OptionMenu(
        appearance_frame,
        state["filename_language"],
        state["filename_language"].get(),
        "English",
        "Persian",
    ).grid(row=1, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(appearance_frame, text="Alt Text Language:", style="TLabel").grid(
        row=2, column=0, sticky="w", padx=5, pady=5
    )
    ttk.OptionMenu(
        appearance_frame,
        state["alttext_language"],
        state["alttext_language"].get(),
        "English",
        "Persian",
    ).grid(row=2, column=1, sticky="w", padx=5, pady=5)

    # --- OCR & Automation ---
    ocr_frame = ttk.Labelframe(frame, text="OCR & Automation", style="Section.TLabelframe", padding=16)
    ocr_frame.grid(row=1, column=0, sticky="nsew", pady=16)
    ocr_frame.columnconfigure(1, weight=1)

    ttk.Checkbutton(ocr_frame, text="Enable OCR", variable=state["ocr_enabled"]).grid(
        row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5
    )
    ttk.Label(ocr_frame, text="Tesseract Path:", style="TLabel").grid(
        row=1, column=0, sticky="w", padx=5, pady=5
    )
    ttk.Entry(ocr_frame, textvariable=state["tesseract_path"], width=40).grid(
        row=1, column=1, sticky="ew", padx=5, pady=5
    )
    ttk.Button(
        ocr_frame, text="Browse", command=lambda: _browse_tesseract(state), style="TButton"
    ).grid(row=1, column=2, padx=5, pady=5)
    ttk.Label(ocr_frame, text="OCR Language:", style="TLabel").grid(
        row=2, column=0, sticky="w", padx=5, pady=5
    )
    ttk.Entry(ocr_frame, textvariable=state["ocr_language"], width=10).grid(
        row=2, column=1, sticky="w", padx=5, pady=5
    )

    # --- Maintenance ---
    maintenance_frame = ttk.Labelframe(frame, text="Maintenance", style="Section.TLabelframe", padding=16)
    maintenance_frame.grid(row=2, column=0, sticky="nsew")
    maintenance_frame.columnconfigure(1, weight=1)

    ttk.Button(
        maintenance_frame, text="Save Settings", command=lambda: _save_settings(state), style="TButton"
    ).grid(row=0, column=0, padx=5, pady=5)
    ttk.Button(
        maintenance_frame, text="Open Config Folder", command=open_config_folder, style="TButton"
    ).grid(row=0, column=1, padx=5, pady=5)
    ttk.Button(
        maintenance_frame,
        text="Reset Defaults",
        command=lambda: state["reset_config_callback"](),
        style="Secondary.TButton",
    ).grid(row=1, column=0, padx=5, pady=5)
    ttk.Button(
        maintenance_frame,
        text="Reset Token Usage",
        command=lambda: _reset_token_usage(state),
        style="Secondary.TButton",
    ).grid(row=1, column=1, padx=5, pady=5)
    ttk.Button(
        maintenance_frame,
        text="Reset Analyzed Stats",
        command=lambda: _reset_global_stats(state),
        style="Secondary.TButton",
    ).grid(row=1, column=2, padx=5, pady=5)


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
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp")])
    if path:
        cleanup_temp_drop_folder(state)
        state["input_path"].set(path)
        if state["input_type"].get() == "Folder":
            count = get_image_count_in_folder(path)
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
        pyperclip.copy(text)
        set_status(state, "Log copied to clipboard.")


def _write_monitor_line_colored(state, log_item) -> None:
    """Write a single line to the activity log with the correct color tag."""
    if "log_text" not in state:
        return

    text_widget = state["log_text"]
    text, level = log_item

    text_widget.config(state="normal")
    text_widget.insert("end", text + "\n", level)
    text_widget.see("end")
    text_widget.config(state="disabled")


def _show_about(state) -> None:
    import webbrowser

    root = state.get("root")
    top = tk.Toplevel(root)
    top.title("About Altomatic")
    top.geometry(_scaled_geometry(top, 420, 240))
    top.resizable(False, False)
    current_theme = state["ui_theme"].get()
    palette = PALETTE.get(current_theme, PALETTE["Default Light"])
    top.configure(bg=palette["background"])
    _apply_window_icon(top)
    apply_theme_to_window(top, current_theme)

    ttk.Label(top, text="Altomatic", font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
    ttk.Label(
        top,
        text=(
            "Created by Mehdi\n\n"
            "An image captioning tool powered by GPT-4.1-nano.\n"
            "Name and describe your images with AI.\n\n"
        ),
    ).pack()

    def open_github():
        webbrowser.open_new("https://github.com/MehdiDevX")

    link = ttk.Label(top, text="Visit GitHub Repository", style="Accent.TLabel", cursor="hand2")
    link.pack()
    link.bind("<Button-1>", lambda _event: open_github())

    ttk.Button(top, text="Close", command=top.destroy).pack(pady=10)
