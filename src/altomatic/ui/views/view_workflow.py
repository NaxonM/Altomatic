from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..ui_toolkit import (
    ScrollableFrame,
    _browse_tesseract,
    _clear_context,
    _select_output_folder,
    CollapsiblePane,
    PlaceholderEntry,
    create_tooltip,
    update_summary,
)
from .._shared import _create_section_header


def build_tab_workflow(frame, state) -> None:
    """Build the workflow tab with scrollable, responsive layout."""
    # Configure main frame
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    # Create scrollable container
    scrollable = ScrollableFrame(frame)
    scrollable.grid(row=0, column=0, sticky="nsew")

    # Use the scrollable_frame as the container for all content
    container = scrollable.scrollable_frame
    container.columnconfigure(0, weight=1)

    # === Context Section ===
    context_card = ttk.Frame(container, style="Card.TFrame", padding=16)
    context_card.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
    context_card.columnconfigure(0, weight=1)

    _create_section_header(context_card, "✏️ Context Notes").grid(row=0, column=0, sticky="w", pady=(0, 8))

    # Text frame with proper weight distribution
    text_frame = ttk.Frame(context_card, style="Section.TFrame")
    text_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
    text_frame.columnconfigure(0, weight=1)
    text_frame.rowconfigure(0, weight=0)  # Fixed height for text widget

    context_entry = tk.Text(text_frame, height=4, wrap="word", relief="solid", borderwidth=1, undo=True, maxundo=-1)
    context_entry.grid(row=0, column=0, sticky="nsew")

    placeholder = "Add optional context about these images..."
    context_entry.insert("1.0", placeholder)
    context_entry.config(foreground="grey")

    # Optimized placeholder handlers
    def _clear_placeholder(e):
        if context_entry.get("1.0", "end-1c") == placeholder:
            context_entry.delete("1.0", "end")
            context_entry.config(foreground="black")

    def _add_placeholder(e):
        content = context_entry.get("1.0", "end-1c")
        if not content or content.isspace():
            context_entry.delete("1.0", "end")
            context_entry.insert("1.0", placeholder)
            context_entry.config(foreground="grey")

    context_entry.bind("<FocusIn>", _clear_placeholder)
    context_entry.bind("<FocusOut>", _add_placeholder)

    # Scrollbar
    context_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=context_entry.yview)
    context_scrollbar.grid(row=0, column=1, sticky="ns")
    context_entry.configure(yscrollcommand=context_scrollbar.set)

    # Stats frame
    stats_frame = ttk.Frame(context_card, style="Section.TFrame")
    stats_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
    stats_frame.columnconfigure(0, weight=1)

    char_count_var = tk.StringVar(value="0 characters")
    state["context_char_count"] = char_count_var

    ttk.Label(stats_frame, textvariable=char_count_var, style="Small.TLabel").grid(row=0, column=0, sticky="w")

    ttk.Button(stats_frame, text="Clear", command=lambda: _clear_context(state), style="Secondary.TButton").grid(
        row=0, column=1, sticky="e"
    )

    # Debounced character count update
    _update_timer = None

    def update_char_count(event=None):
        nonlocal _update_timer

        if _update_timer:
            context_entry.after_cancel(_update_timer)

        def do_update():
            content = context_entry.get("1.0", "end-1c")
            if content != placeholder or context_entry.cget("foreground") != "grey":
                actual_content = "" if content == placeholder else content
                char_count_var.set(f"{len(actual_content)} characters")
                state["context_text"].set(actual_content)

        _update_timer = context_entry.after(150, do_update)

    context_entry.bind("<KeyRelease>", update_char_count)
    state["context_widget"] = context_entry

    # Initialize with saved context
    if initial_text := state["context_text"].get():
        context_entry.delete("1.0", "end")
        context_entry.insert("1.0", initial_text)
        context_entry.config(foreground="black")
        update_char_count()

    # Create accordion group
    accordion_group = []

    # === Processing Section ===
    processing_pane = CollapsiblePane(
        container, text="🤖 Processing Options", accordion_group=accordion_group, scroll_canvas=scrollable.canvas
    )
    processing_pane.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    accordion_group.append(processing_pane)
    processing_card = processing_pane.frame
    state["processing_pane"] = processing_pane

    # Responsive grid
    processing_card.columnconfigure(0, weight=0, minsize=120)
    processing_card.columnconfigure(1, weight=1, minsize=100)
    processing_card.columnconfigure(2, weight=0, minsize=120)
    processing_card.columnconfigure(3, weight=1, minsize=100)

    # Language options
    ttk.Label(processing_card, text="Filename language:", style="TLabel").grid(
        row=0, column=0, sticky="w", padx=(0, 8), pady=8
    )

    ttk.OptionMenu(
        processing_card,
        state["filename_language"],
        state["filename_language"].get(),
        "English",
        "Persian",
    ).grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=8)

    ttk.Label(processing_card, text="Alt-text language:", style="TLabel").grid(
        row=0, column=2, sticky="w", padx=(0, 8), pady=8
    )

    ttk.OptionMenu(
        processing_card,
        state["alttext_language"],
        state["alttext_language"].get(),
        "English",
        "Persian",
    ).grid(row=0, column=3, sticky="ew", pady=8)

    if not state.get("_alttext_trace_registered"):
        def _alttext_updated(*_args) -> None:
            update_summary(state)

        state["alttext_language"].trace_add("write", lambda *_: _alttext_updated())
        state["_alttext_trace_registered"] = True

    # Detail options
    ttk.Label(processing_card, text="Name detail level:", style="TLabel").grid(
        row=1, column=0, sticky="w", padx=(0, 8), pady=8
    )

    ttk.OptionMenu(
        processing_card,
        state["name_detail_level"],
        state["name_detail_level"].get(),
        "Detailed",
        "Normal",
        "Minimal",
    ).grid(row=1, column=1, sticky="ew", padx=(0, 16), pady=8)

    ttk.Label(processing_card, text="Vision detail:", style="TLabel").grid(
        row=1, column=2, sticky="w", padx=(0, 8), pady=8
    )

    ttk.OptionMenu(
        processing_card,
        state["vision_detail"],
        state["vision_detail"].get(),
        "auto",
        "high",
        "low",
    ).grid(row=1, column=3, sticky="ew", pady=8)

    # === OCR Section ===
    ocr_pane = CollapsiblePane(
        container, text="📸 OCR Settings", accordion_group=accordion_group, scroll_canvas=scrollable.canvas
    )
    ocr_pane.grid(row=2, column=0, sticky="ew", pady=(0, 8))
    accordion_group.append(ocr_pane)
    ocr_card = ocr_pane.frame

    # Responsive grid
    ocr_card.columnconfigure(0, weight=0, minsize=120)
    ocr_card.columnconfigure(1, weight=1)
    ocr_card.columnconfigure(2, weight=1)
    ocr_card.columnconfigure(3, weight=0, minsize=80)

    # OCR checkbox
    ocr_checkbox = ttk.Checkbutton(ocr_card, text="Enable OCR before compression", variable=state["ocr_enabled"])
    ocr_checkbox.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
    create_tooltip(
        ocr_checkbox,
        "OCR extracts text from images before compression, improving AI descriptions for text-heavy images.",
    )

    # Tesseract path
    ttk.Label(ocr_card, text="Tesseract path:", style="TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=8)

    tesseract_entry = PlaceholderEntry(
        ocr_card, textvariable=state["tesseract_path"], placeholder="Path to Tesseract executable"
    )
    tesseract_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 8), pady=8)
    create_tooltip(tesseract_entry, "The path to the Tesseract executable. Required for OCR.")

    ttk.Button(ocr_card, text="Browse", command=lambda: _browse_tesseract(state), style="TButton").grid(
        row=1, column=3, sticky="ew", pady=8
    )

    # OCR language
    ttk.Label(ocr_card, text="OCR language:", style="TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=8)

    ocr_lang_entry = ttk.Entry(ocr_card, textvariable=state["ocr_language"], width=10)
    ocr_lang_entry.grid(row=2, column=1, sticky="w", pady=8)
    create_tooltip(ocr_lang_entry, "The language for OCR (e.g., 'eng' for English).")

    # === Output Section ===
    output_pane = CollapsiblePane(
        container, text="💾 Output Settings", accordion_group=accordion_group, scroll_canvas=scrollable.canvas
    )
    output_pane.grid(row=3, column=0, sticky="ew", pady=(0, 8))
    accordion_group.append(output_pane)
    state["output_pane"] = output_pane
    output_card = output_pane.frame

    # Responsive grid
    output_card.columnconfigure(0, weight=0, minsize=120)
    output_card.columnconfigure(1, weight=1)
    output_card.columnconfigure(2, weight=0, minsize=80)

    # Save location
    ttk.Label(output_card, text="Save to:", style="TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=8)

    ttk.OptionMenu(
        output_card,
        state["output_folder_option"],
        state["output_folder_option"].get(),
        "Same as input",
        "Pictures",
        "Desktop",
        "Custom",
    ).grid(row=0, column=1, columnspan=2, sticky="w", pady=8)

    # Custom folder
    custom_output_label = ttk.Label(output_card, text="Custom folder:", style="TLabel")
    custom_output_label.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=8)
    state["custom_output_label"] = custom_output_label

    custom_output_entry = ttk.Entry(output_card, textvariable=state["custom_output_path"])
    custom_output_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=8)
    state["custom_output_entry"] = custom_output_entry

    custom_output_browse_button = ttk.Button(
        output_card, text="Browse", command=lambda: _select_output_folder(state), style="TButton"
    )
    custom_output_browse_button.grid(row=1, column=2, sticky="ew", pady=8)
    state["custom_output_browse_button"] = custom_output_browse_button

    # Separator
    ttk.Separator(output_card, orient="horizontal").grid(row=2, column=0, columnspan=3, sticky="ew", pady=16)

    # Results table checkbox
    results_checkbox = ttk.Checkbutton(
        output_card,
        text="Show interactive results table after processing",
        variable=state["show_results_table"],
    )
    results_checkbox.grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 8))
    create_tooltip(
        results_checkbox, "Show a table with the results after processing. You can view, copy, and preview the results."
    )

    auto_open_checkbox = ttk.Checkbutton(
        output_card,
        text="Open results folder when processing completes",
        variable=state["auto_open_results"],
    )
    auto_open_checkbox.grid(row=4, column=0, columnspan=3, sticky="w")
    create_tooltip(
        auto_open_checkbox,
        "Automatically open the generated session folder in your file explorer after each run.",
    )

    # Add padding at bottom to ensure last accordion has space
    ttk.Frame(container, height=20).grid(row=5, column=0)
