from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..ui_toolkit import (
    _create_info_label,
    _create_section_header,
    _browse_tesseract,
    _clear_context,
    _select_output_folder,
)


def build_tab_workflow(frame, state) -> None:
    """Build the workflow tab with a flattened, vertical layout."""
    frame.columnconfigure(0, weight=1)

    # === Context Section ===
    _create_section_header(frame, "Context").grid(row=0, column=0, sticky="w", pady=(0, 8))
    context_card = ttk.Frame(frame, style="Card.TFrame", padding=16)
    context_card.grid(row=1, column=0, sticky="nsew", pady=(0, 16))
    context_card.columnconfigure(0, weight=1)
    context_card.rowconfigure(1, weight=1)

    _create_section_header(context_card, "Context Notes").grid(
        row=0, column=0, sticky="w", pady=(0, 8)
    )

    _create_info_label(
        context_card,
        "Add optional context about these images to help the AI generate more accurate descriptions.",
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

    ttk.Label(stats_frame, textvariable=char_count_var, style="Small.TLabel").grid(
        row=0, column=0, sticky="w"
    )
    ttk.Button(
        stats_frame, text="Clear", command=lambda: _clear_context(state), style="Secondary.TButton"
    ).grid(row=0, column=1, sticky="e")

    def update_char_count(event=None):
        content = context_entry.get("1.0", "end-1c")
        char_count_var.set(f"{len(content)} characters")
        state["context_text"].set(content)

    context_entry.bind("<KeyRelease>", update_char_count)
    state["context_widget"] = context_entry

    if initial_text := state["context_text"].get():
        context_entry.insert("1.0", initial_text)
        update_char_count()

    # === Processing Section ===
    _create_section_header(frame, "Processing").grid(row=2, column=0, sticky="w", pady=(0, 8))
    processing_card = ttk.Frame(frame, style="Card.TFrame", padding=16)
    processing_card.grid(row=3, column=0, sticky="nsew", pady=(0, 16))
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
        processing_card, text="Enable OCR before compression", variable=state["ocr_enabled"]
    ).grid(row=5, column=0, columnspan=4, sticky="w", pady=(0, 8))

    ttk.Label(processing_card, text="Tesseract path:", style="TLabel").grid(
        row=6, column=0, sticky="w", padx=(0, 8), pady=8
    )
    ttk.Entry(processing_card, textvariable=state["tesseract_path"]).grid(
        row=6, column=1, columnspan=2, sticky="ew", padx=(0, 8), pady=8
    )
    ttk.Button(
        processing_card, text="Browse", command=lambda: _browse_tesseract(state), style="TButton"
    ).grid(row=6, column=3, sticky="ew", pady=8)

    ttk.Label(processing_card, text="OCR language:", style="TLabel").grid(
        row=7, column=0, sticky="w", padx=(0, 8), pady=8
    )
    ttk.Entry(processing_card, textvariable=state["ocr_language"], width=10).grid(
        row=7, column=1, sticky="w", pady=8
    )

    _create_info_label(
        processing_card,
        "OCR extracts text from images before compression, improving AI descriptions for text-heavy images.",
    ).grid(row=8, column=0, columnspan=4, sticky="w", pady=(8, 0))

    # === Output Section ===
    _create_section_header(frame, "Output").grid(row=4, column=0, sticky="w", pady=(0, 8))
    output_card = ttk.Frame(frame, style="Card.TFrame", padding=16)
    output_card.grid(row=5, column=0, sticky="nsew", pady=(0, 16))
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
        output_card, text="Browse", command=lambda: _select_output_folder(state), style="TButton"
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
        wraplength=600,
    ).grid(row=5, column=0, columnspan=3, sticky="w")
