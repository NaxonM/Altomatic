import tkinter as tk
from tkinter import ttk
import webbrowser
from ..themes import PALETTE, apply_theme_to_window
from ..ui_toolkit import _apply_window_icon

def show_about(state) -> None:
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
