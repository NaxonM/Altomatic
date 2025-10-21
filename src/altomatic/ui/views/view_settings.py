from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models import AVAILABLE_PROVIDERS, get_models_for_provider, get_provider_label, refresh_openrouter_models, get_default_model, format_pricing
from ..ui_toolkit import (
    CollapsiblePane,
    _create_info_label,
    set_status,
    update_model_pricing,
    update_summary,
    validate_api_key,
    initialize_provider_ui,
    append_monitor_colored,
    pyperclip,
    refresh_prompt_choices,
)
from ..dialogs.prompt_editor import open_prompt_editor


class ScrollableFrame(ttk.Frame):
    """A scrollable frame container for dynamic content."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Create canvas and scrollbar with proper background
        style = ttk.Style()
        bg_color = style.lookup('TFrame', 'background')
        self.canvas = tk.Canvas(self, highlightthickness=0, bg=bg_color)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configure canvas scrolling with after_idle to prevent race conditions
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.after_idle(
                lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            )
        )

        # Create window in canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Configure canvas to resize with window
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Enable mousewheel scrolling
        self.scrollable_frame.bind("<Enter>", self._bind_mousewheel)
        self.scrollable_frame.bind("<Leave>", self._unbind_mousewheel)

    def _on_canvas_configure(self, event):
        """Adjust the scrollable frame width to match canvas width."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def _bind_mousewheel(self, event):
        """Bind mousewheel to canvas scrolling."""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        """Unbind mousewheel from canvas scrolling."""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

def build_tab_configuration(frame, state) -> None:
    """Build the consolidated configuration tab."""
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    # Create scrollable container
    scrollable = ScrollableFrame(frame)
    scrollable.grid(row=0, column=0, sticky="nsew")
    
    container = scrollable.scrollable_frame
    container.columnconfigure(0, weight=1)

    # Create accordion group for all collapsible panes
    accordion_group = []

    # AI Provider & Model
    pane1 = CollapsiblePane(container, text="🤖 AI Provider & Model", accordion_group=accordion_group, scroll_canvas=scrollable.canvas)
    pane1.grid(row=0, column=0, sticky="ew", pady=(0, 16))
    accordion_group.append(pane1)
    _build_llm_provider_section(pane1.frame, state)

    # Prompt Management
    pane2 = CollapsiblePane(container, text="✍️ Prompt Management", accordion_group=accordion_group, scroll_canvas=scrollable.canvas)
    pane2.grid(row=1, column=0, sticky="ew", pady=(0, 16))
    accordion_group.append(pane2)
    _build_prompt_management_section(pane2.frame, state)


def _build_prompt_management_section(parent, state) -> None:
    """Build the prompt management section."""
    parent.columnconfigure(0, weight=1)
    prompt_card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    prompt_card.grid(row=0, column=0, sticky="nsew")
    prompt_card.columnconfigure(0, weight=1)
    prompt_card.rowconfigure(2, weight=1)

    # Prompt selection
    selection_frame = ttk.Frame(prompt_card, style="Section.TFrame")
    selection_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
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

    # Main container with compact padding
    main_container = ttk.Frame(parent, style="Card.TFrame", padding=16)
    main_container.grid(row=0, column=0, sticky="nsew")
    main_container.columnconfigure(0, weight=1)

    # --- Provider Selection ---
    provider_select_frame = ttk.Frame(main_container, style="Section.TFrame")
    provider_select_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
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

    # --- Model Selection ---
    model_select_frame = ttk.Frame(main_container, style="Section.TFrame")
    model_select_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
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
            # Refresh model choices in the dropdown
            if "model_option_menu" in state:
                menu = state["model_option_menu"]
                menu.delete(0, "end")
                for model_id, info in models.items():
                    label = info.get("label", model_id)
                    menu.add_command(label=label, command=lambda value=model_id: state["llm_model"].set(value))

                current_model = state["llm_model"].get()
                if current_model in models:
                    state["model_label_var"].set(models[current_model].get("label", current_model))

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
    model_info_frame = ttk.Frame(main_container, style="Section.TFrame")
    model_info_frame.grid(row=2, column=0, sticky="ew", pady=(4, 12))
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

    # --- API Keys ---
    # OpenAI section (show/hide based on provider)
    openai_frame = ttk.Frame(main_container, style="Section.TFrame")
    openai_frame.grid(row=3, column=0, sticky="ew", pady=(0, 4))
    openai_frame.columnconfigure(1, weight=1)
    _build_compact_openai_config(openai_frame, state)
    state["openai_section"] = openai_frame

    # OpenRouter section (show/hide based on provider)
    openrouter_frame = ttk.Frame(main_container, style="Section.TFrame")
    openrouter_frame.grid(row=4, column=0, sticky="ew", pady=(0, 4))
    openrouter_frame.columnconfigure(1, weight=1)
    _build_compact_openrouter_config(openrouter_frame, state)
    state["openrouter_section"] = openrouter_frame

    # Initialize the UI
    initialize_provider_ui(state)


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
                    is_valid, message = validate_api_key("openai", content)
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
                    is_valid, message = validate_api_key("openrouter", content)
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
