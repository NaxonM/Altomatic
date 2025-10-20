import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from ...prompts import load_prompts, save_prompts
from ...utils import slugify
from ..themes import PALETTE, apply_theme_to_window
from ..ui_toolkit import _scaled_geometry, _apply_window_icon, set_status, refresh_prompt_choices
from .._shared import _create_section_header


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
            messagebox.showinfo(
                "Cannot Delete",
                "The default prompt cannot be deleted, and you must keep at least one prompt.",
                parent=editor,
            )
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
    ttk.Button(button_bar, text="Duplicate", command=duplicate_prompt, style="TButton").grid(
        row=0, column=1, padx=(0, 6)
    )
    ttk.Button(button_bar, text="Delete", command=delete_prompt, style="Secondary.TButton").grid(
        row=0, column=2, padx=(0, 6)
    )
    ttk.Label(button_bar, text="", style="TLabel").grid(row=0, column=3, padx=(12, 0))  # Spacer
    ttk.Button(button_bar, text="Save", command=save_changes, style="TButton").grid(row=0, column=4, padx=(0, 6))
    ttk.Button(button_bar, text="Save & Close", command=save_and_close, style="Accent.TButton").grid(
        row=0, column=5, padx=(0, 6)
    )
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
