"""Interactive results window for Altomatic."""

import tkinter as tk
from tkinter import ttk
import pyperclip
from PIL import Image, ImageTk

from .ui_toolkit import _apply_window_icon, _scaled_geometry
from .themes import PALETTE, apply_theme_to_window


def create_results_window(state, results):
    """Create and display the interactive results window."""
    root = state.get("root")
    editor = tk.Toplevel(root)
    editor.title("Processing Results")
    editor.geometry(_scaled_geometry(editor, 1024, 600))
    editor.minsize(720, 400)
    editor.grab_set()

    current_theme = state["ui_theme"].get()
    palette = PALETTE.get(current_theme, PALETTE["Arctic Light"])
    editor.configure(bg=palette["background"])
    _apply_window_icon(editor)

    container = ttk.Frame(editor, padding=12)
    container.pack(fill="both", expand=True)
    container.columnconfigure(0, weight=1)
    container.rowconfigure(0, weight=1)

    tree = ttk.Treeview(
        container,
        columns=("Original", "New", "Alt Text"),
        show="headings",
        selectmode="browse",
    )
    tree.grid(row=0, column=0, sticky="nsew")

    tree.heading("Original", text="Original Filename")
    tree.heading("New", text="New Filename")
    tree.heading("Alt Text", text="Generated Alt Text")

    tree.column("Original", width=200, anchor="w")
    tree.column("New", width=200, anchor="w")
    tree.column("Alt Text", width=400, anchor="w")

    for i, result in enumerate(results):
        tree.insert("", "end", iid=i, values=(result["original_filename"], result["new_filename"], result["alt_text"]))

    scrollbar = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)

    context_menu = tk.Menu(editor, tearoff=0)

    def show_context_menu(event):
        item_id = tree.identify_row(event.y)
        if item_id:
            tree.selection_set(item_id)
            context_menu.tk_popup(event.x_root, event.y_root)

    def copy_new_filename():
        selected_item = tree.selection()[0]
        pyperclip.copy(tree.item(selected_item)["values"][1])

    def copy_alt_text():
        selected_item = tree.selection()[0]
        pyperclip.copy(tree.item(selected_item)["values"][2])

    def preview_image():
        selected_item = tree.selection()[0]
        item_index = int(selected_item)
        image_path = results[item_index]["original_path"]

        preview = tk.Toplevel(editor)
        preview.title("Image Preview")

        img = Image.open(image_path)
        img.thumbnail((800, 600))
        photo = ImageTk.PhotoImage(img)

        label = ttk.Label(preview, image=photo)
        label.image = photo
        label.pack()

    context_menu.add_command(label="Copy New Filename", command=copy_new_filename)
    context_menu.add_command(label="Copy Alt Text", command=copy_alt_text)
    context_menu.add_separator()
    context_menu.add_command(label="Preview Image", command=preview_image)

    tree.bind("<Button-3>", show_context_menu)

    button_bar = ttk.Frame(container, padding=(0, 12, 0, 0))
    button_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

    ttk.Button(button_bar, text="Close", command=editor.destroy).pack(side="right")

    apply_theme_to_window(editor, current_theme)
