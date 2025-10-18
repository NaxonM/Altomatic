
def build_ui(root, user_config):
    """Build the main UI and stitch components together."""
    chroma_frame = ttk.Frame(root, padding=(16, 0, 16, 16))
    chroma_frame.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    main_frame = ttk.Frame(chroma_frame, padding=16)
    main_frame.grid(row=1, column=0, sticky="nsew")
    chroma_frame.columnconfigure(0, weight=1)
    chroma_frame.rowconfigure(1, weight=1)

    # --- Main Layout ---
    main_frame.rowconfigure(0, weight=0)  # Input section
    main_frame.rowconfigure(1, weight=1)  # Notebook
    main_frame.rowconfigure(2, weight=0)  # Footer
    main_frame.columnconfigure(0, weight=1)

    # Central state dictionary, passed around to UI functions
    state = {
        "root": root,
        # ... (rest of the state dictionary remains the same)
    }

    _build_input_frame(main_frame, state)
    notebook = _build_notebook(main_frame, state)
    _build_footer(main_frame, state)

    # ... (rest of the function remains the same)

    return state


def _build_input_frame(parent, state) -> None:
    """Build the persistent input frame."""
    input_card = ttk.Frame(parent, style="Card.TFrame", padding=12)
    input_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
    input_card.columnconfigure(0, weight=1)
    state["input_card"] = input_card  # Make it available for dnd binding

    # Row 0: Label
    ttk.Label(input_card, text="Drop files or a folder here, or use the browse button.", style="TLabel").grid(
        row=0, column=0, sticky="w", padx=5, pady=5
    )

    # Row 1: Input line (entry and browse button)
    input_line = ttk.Frame(input_card, style="Card.TFrame")
    input_line.grid(row=1, column=0, sticky="ew")
    input_line.columnconfigure(0, weight=1)
    entry = ttk.Entry(input_line, textvariable=state["input_path"], width=50)
    entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    state["input_entry"] = entry
    ttk.Button(input_line, text="Browse...", command=lambda: _select_input(state), style="TButton").grid(
        row=0, column=1
    )

    # Row 2: Options line (checkbox and image count)
    options_line = ttk.Frame(input_card, style="Card.TFrame")
    options_line.grid(row=2, column=0, sticky="ew", pady=(4, 0))
    options_line.columnconfigure(1, weight=1)
    ttk.Checkbutton(
        options_line, text="Include subdirectories", variable=state["recursive_search"]
    ).grid(row=0, column=0, sticky="w")
    ttk.Label(options_line, textvariable=state["image_count"], style="Small.TLabel").grid(
        row=0, column=1, sticky="e"
    )

    # Row 3: Session overview (the header)
    header = ttk.Frame(input_card, style="Card.TFrame", padding=(0, 12, 0, 0))
    header.grid(row=3, column=0, sticky="ew", pady=(12, 0))
    header.columnconfigure((0, 1, 2), weight=1)
    state["summary_model"].grid(row=0, column=0)
    state["summary_prompt"].grid(row=0, column=1)
    state["summary_output"].grid(row=0, column=2)
