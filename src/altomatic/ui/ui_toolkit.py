import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import shutil
from importlib import resources
import webbrowser

try:
    import pyperclip
except ModuleNotFoundError:
    pyperclip = None

from ..config import open_config_folder, save_config
from ..models import (
    AVAILABLE_PROVIDERS,
    AppState,
    DEFAULT_MODEL,
    default_models,
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
    """A label with animated scrolling for overflow text."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.full_text = ""
        self._after_id = None
        self.bind("<Configure>", self._check_width)
        self.bind("<Destroy>", self._on_destroy)

    def set_text(self, text: str):
        """Set the label's text and start or stop animation as needed."""
        self.full_text = text
        self._stop_animation()
        self.config(text=self.full_text)
        self.after_idle(self._check_width)

    def _check_width(self, event=None):
        """Check if the text is overflowing and manage animation."""
        if not self.winfo_exists():
            return

        self.update_idletasks()
        is_overflowing = self.winfo_width() < self.winfo_reqwidth()

        if is_overflowing and self._after_id is None:
            self._start_animation()
        elif not is_overflowing and self._after_id is not None:
            self._stop_animation()
            self.config(text=self.full_text)

    def _start_animation(self):
        """Start the scrolling animation."""
        self.config(text=self.full_text)
        self._animate()

    def _animate(self):
        """Perform one step of the animation."""
        text = self.cget("text")
        if text:
            text = text[1:] + text[0]
            self.config(text=text)
        self._after_id = self.after(200, self._animate)

    def _stop_animation(self):
        """Stop the scrolling animation."""
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

    def _on_destroy(self, event=None):
        """Ensure animation is stopped when widget is destroyed."""
        self._stop_animation()


class ScrollableFrame(ttk.Frame):
    """A scrollable frame container for dynamic content."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Create canvas and scrollbar with proper background
        style = ttk.Style()
        bg_color = style.lookup("TFrame", "background")
        self.canvas = tk.Canvas(self, highlightthickness=0, bg=bg_color)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Defer window creation until the first configure event
        self.canvas_frame = None

        # Configure canvas scrolling with after_idle to prevent race conditions
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.after_idle(lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all"))),
        )

        # Bind configure event to handle window creation and resizing
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Enable mousewheel scrolling
        self.bind("<Enter>", self._bind_mousewheel)
        self.bind("<Leave>", self._unbind_mousewheel)

    def _on_canvas_configure(self, event):
        """Create the canvas window on first configure and adjust width."""
        if self.winfo_exists():
            # Create the window only once
            if self.canvas_frame is None:
                self.canvas_frame = self.canvas.create_window(
                    (0, 0), window=self.scrollable_frame, anchor="nw"
                )

            # Always update the width to be responsive
            self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _bind_mousewheel(self, event):
        """Bind mousewheel to canvas scrolling."""
        # Bind to the canvas itself, not globally.
        # This prevents interference with other scrollable widgets.
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        """Unbind mousewheel from canvas scrolling."""
        self.canvas.unbind("<MouseWheel>")
        self.canvas.unbind("<Button-4>")
        self.canvas.unbind("<Button-5>")

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")


class CollapsiblePane(ttk.Frame):
    """A collapsible pane widget with optional accordion behavior and auto-scroll."""
    
    def __init__(self, parent, text, accordion_group=None, scroll_canvas=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.columnconfigure(0, weight=1)
        
        self.scroll_canvas = scroll_canvas
        self.is_collapsed = True
        self.text = text
        self.accordion_group = accordion_group
        
        # Header
        self.header_frame = ttk.Frame(self, style="Card.TFrame")
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.columnconfigure(0, weight=1)
        
        self.header_label = ttk.Label(self.header_frame, text=self.text, style="Header.TLabel")
        self.header_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.toggle_button = ttk.Button(
            self.header_frame, 
            text="▶", 
            command=self.toggle, 
            width=4
        )
        self.toggle_button.grid(row=0, column=1, sticky="e", padx=5)
        
        # Content frame
        self.frame = ttk.Frame(self, style="Card.TFrame", padding=(16, 0, 16, 16))
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        
        # Bind click events
        self.bind("<Button-1>", self.toggle)
        self.header_label.bind("<Button-1>", self.toggle)
    
    def toggle(self, event=None):
        """Toggle the pane open/closed with auto-scroll support."""
        if self.is_collapsed:
            # If accordion group is set, collapse all other panes first
            if self.accordion_group:
                for pane in self.accordion_group:
                    if pane != self and not pane.is_collapsed:
                        pane.collapse()
            
            # Expand this pane
            self.frame.grid(row=1, column=0, sticky="nsew")
            self.toggle_button.configure(text="▼")
            self.is_collapsed = False
            
            # Update scroll region and auto-scroll to make content visible
            if self.scroll_canvas:
                self._auto_scroll_to_visible()
        else:
            self.collapse()
    
    def _auto_scroll_to_visible(self):
        """Automatically scroll the canvas to make the expanded pane fully visible."""
        if not self.scroll_canvas:
            return
        
        # Update the canvas to get accurate measurements
        self.scroll_canvas.update_idletasks()
        self.update_idletasks()
        
        # Update scroll region first
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
        
        # Get the bounding box of this pane within the canvas
        try:
            # Get the position of this widget relative to the scrollable frame
            pane_y = self.winfo_y()
            pane_height = self.winfo_height()
            pane_bottom = pane_y + pane_height
            
            # Get canvas viewport dimensions
            canvas_height = self.scroll_canvas.winfo_height()
            
            # Get current scroll position
            scroll_region = self.scroll_canvas.cget("scrollregion").split()
            if len(scroll_region) == 4:
                total_height = float(scroll_region[3])
            else:
                return
            
            # Get current view position (top and bottom fractions)
            current_view = self.scroll_canvas.yview()
            view_top = current_view[0] * total_height
            view_bottom = current_view[1] * total_height
            
            # Calculate if we need to scroll
            if pane_bottom > view_bottom:
                # Pane bottom is below visible area - scroll down
                target_position = (pane_bottom - canvas_height) / total_height
                target_position = max(0.0, min(1.0, target_position))
                self.scroll_canvas.yview_moveto(target_position)
            elif pane_y < view_top:
                # Pane top is above visible area - scroll up
                target_position = pane_y / total_height
                target_position = max(0.0, min(1.0, target_position))
                self.scroll_canvas.yview_moveto(target_position)
                
        except tk.TclError as e:
            # This can happen if the widget is destroyed while scrolling.
            # We can safely ignore it.
            print(f"Ignoring TclError during auto-scroll: {e}")
    
    def collapse(self):
        """Collapse this pane."""
        self.frame.grid_forget()
        self.toggle_button.configure(text="▶")
        self.is_collapsed = True
        
        # Update scroll region when collapsing
        if self.scroll_canvas:
            self.scroll_canvas.update_idletasks()
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
    
    def expand(self):
        """Expand this pane (collapsing others if in accordion group)."""
        if self.is_collapsed:
            self.toggle()


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


def _create_section_header(parent, text: str, style="Header.TLabel") -> ttk.Label:
    """Create a consistent section header."""
    return ttk.Label(parent, text=text, style=style)


def _create_info_label(parent, text: str, wraplength=500) -> ttk.Label:
    """Create a consistent info/help label."""
    return ttk.Label(
        parent,
        text=text,
        style="Small.TLabel",
        wraplength=wraplength,
        justify="left"
    )

def update_token_label(state: AppState) -> None:
    """Update the token usage display."""
    if state.lbl_token_usage:
        state.lbl_token_usage.config(text=f"Tokens: {state.total_tokens.get():,}")


def update_model_pricing(state: AppState) -> None:
    """Update the model pricing information display."""
    if not state.lbl_model_pricing:
        return

    provider = state.llm_provider.get() or DEFAULT_PROVIDER
    model_id = state.llm_model.get() or DEFAULT_MODEL

    models = get_models_for_provider(provider)
    details = models.get(model_id)

    if not details:
        state.lbl_model_pricing.config(text="Model pricing unavailable")
        return

    provider_label = get_provider_label(provider)
    model_label = details.get("label", model_id)
    vendor = details.get("vendor")

    pricing_text = f"{provider_label} • {model_label}\n{format_pricing(provider, model_id)}"
    if vendor:
        pricing_text += f"\nVendor: {vendor}"

    state.lbl_model_pricing.config(text=pricing_text)


def _format_proxy_mapping(mapping: dict[str, str]) -> str:
    """Format proxy mapping dictionary for display."""
    if not mapping:
        return "None"
    lines = [f"{scheme}: {value}" for scheme, value in sorted(mapping.items())]
    return "\n".join(lines)


def update_summary(state: AppState) -> None:
    """Update the summary bar with current selections."""
    if not state.summary_model:
        return

    # Update model summary
    provider = state.llm_provider.get() or DEFAULT_PROVIDER
    model_id = state.llm_model.get() or DEFAULT_MODEL
    models = get_models_for_provider(provider)
    model_label = models.get(model_id, {}).get("label", model_id)
    state.summary_model.set_text(f"Model: {get_provider_label(provider)} • {model_label}")

    # Update prompt summary
    prompts = state.prompts or load_prompts()
    prompt_key = state.prompt_key.get()
    prompt_entry = prompts.get(prompt_key) or prompts.get("default") or next(iter(prompts.values()), {})
    prompt_text = f"Prompt: {prompt_entry.get('label', prompt_key)}"
    state.summary_prompt.set_text(prompt_text)

    # Update output summary
    destination = state.output_folder_option.get()
    if destination == "Custom":
        path = state.custom_output_path.get().strip() or "(not set)"
        output_text = f"Output: Custom → {path}"
    else:
        output_text = f"Output: {destination}"

    state.summary_output.set_text(output_text)

    # Trigger scroll check after updating summaries
    if state._update_summary_scrolling and state.summary_container:
        state.summary_container.after(50, state._update_summary_scrolling)


def set_status(state: AppState, message: str) -> None:
    """Update the status bar message."""
    if state.status_var:
        state.status_var.set(message)


def update_prompt_preview(state: AppState) -> None:
    """Update the prompt preview text widget."""
    if not state.prompt_preview:
        return
    prompts = state.prompts or load_prompts()
    key = state.prompt_key.get()
    entry = prompts.get(key)
    if entry is None:
        prompts = load_prompts()
        entry = prompts.get(key) or prompts.get("default") or next(iter(prompts.values()))
        state.prompts = prompts
        state.prompt_names = list(prompts.keys())
    label = entry.get("label", key)
    template = entry.get("template", "")
    widget = state.prompt_preview
    widget.config(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", f"{label}\n\n{template}".strip())
    widget.config(state="disabled")


def refresh_prompt_choices(state: AppState) -> None:
    """Refresh the prompt dropdown menu with current prompts."""
    prompts = load_prompts()
    state.prompts = prompts
    state.prompt_names = list(prompts.keys())
    menu = state.prompt_option_menu
    if menu:
        menu.delete(0, "end")
        for key, entry in prompts.items():
            label = entry.get("label", key)
            menu.add_command(label=label, command=lambda value=key: state.prompt_key.set(value))
    current = state.prompt_key.get()
    if current not in prompts and prompts:
        state.prompt_key.set(next(iter(prompts.keys())))
    else:
        state.prompt_key.set(state.prompt_key.get())
    update_prompt_preview(state)


def cleanup_temp_drop_folder(state: AppState) -> None:
    """Clean up temporary drop folder if it exists."""
    folder = state.temp_drop_folder
    if folder and os.path.isdir(folder):
        try:
            shutil.rmtree(folder)
        except OSError:
            pass
    state.temp_drop_folder = None

def _update_proxy_controls(state: AppState) -> None:
    """Enable or disable proxy override entry based on proxy enabled state."""
    entry = state.proxy_override_entry
    if entry is None:
        return
    entry_state = "normal" if state.proxy_enabled and state.proxy_enabled.get() else "disabled"
    entry.config(state=entry_state)


def _update_proxy_effective_label(state: AppState) -> None:
    """Update the effective proxy label with current settings."""
    if not state.proxy_effective_label:
        return
    enabled = bool(state.proxy_enabled.get())
    override = state.proxy_override.get().strip()
    proxies = get_requests_proxies(enabled=enabled, override=override or None)
    state.proxy_effective_label.set(_format_proxy_mapping(proxies))


def _apply_proxy_preferences(state: AppState, *, force: bool = False) -> None:
    """Apply proxy preferences and update UI."""
    enabled = bool(state.proxy_enabled.get())
    override_value = state.proxy_override.get().strip()
    last_settings = state._proxy_last_settings or (None, None)
    current_settings = (enabled, override_value)

    if force or current_settings != last_settings:
        set_proxy_preferences(enabled, override_value or None)
        state._proxy_last_settings = current_settings

    _update_proxy_controls(state)
    _update_proxy_effective_label(state)


def _refresh_detected_proxy(state: AppState) -> None:
    """Refresh the detected system proxy settings."""
    detected = reload_system_proxies()
    if state.proxy_detected_label:
        state.proxy_detected_label.set(_format_proxy_mapping(detected))
    configure_global_proxy(force=True)
    _update_proxy_effective_label(state)


def _update_provider_status_labels(state: AppState) -> None:
    """Update the API key status labels."""
    openai_label = state.openai_status_label
    if openai_label is not None:
        is_set = bool(state.openai_api_key.get())
        openai_label.configure(text="✓ Ready" if is_set else "⚠ Not set")

    openrouter_label = state.openrouter_status_label
    if openrouter_label is not None:
        is_set = bool(state.openrouter_api_key.get())
        openrouter_label.configure(text="✓ Ready" if is_set else "⚠ Not set")


def append_monitor_colored(state: AppState, message: str, level: str = "info") -> None:
    """Append a colored message to the activity log."""
    formatted = f"[{level.upper()}] {message}"
    state.logs.append((formatted, level))
    _write_monitor_line_colored(state, (formatted, level))


def _clear_monitor(state: AppState) -> None:
    """Clear the activity log."""
    state.logs.clear()
    if state.log_text:
        widget = state.log_text
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.config(state="disabled")


def _copy_monitor(state: AppState) -> None:
    """Copy the activity log to clipboard."""
    if state.log_text:
        text = state.log_text.get("1.0", "end")
        if pyperclip is None:
            set_status(state, "Clipboard support not available")
            return
        pyperclip.copy(text)
        set_status(state, "Log copied to clipboard")


def _write_monitor_line_colored(state: AppState, log_item) -> None:
    """Write a colored line to the activity log."""
    if not state.log_text:
        return

    text_widget = state.log_text
    text, level = log_item

    text_widget.config(state="normal")
    text_widget.insert("end", text + "\n", level)
    text_widget.see("end")
    text_widget.config(state="disabled")


def _clear_context(state: AppState, *, silent: bool = False) -> None:
    """Clear the context text area."""
    if state.context_widget:
        state.context_widget.delete("1.0", "end")
    state.context_text.set("")
    if state.context_char_count:
        state.context_char_count.set("0 characters")
    if not silent:
        set_status(state, "Context cleared")


def _select_input(state: AppState) -> None:
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
    state.input_path.set(input_path)
    recursive = state.recursive_search.get()
    count = get_image_count_in_folder(input_path, recursive)
    state.image_count.set(f"{count} image(s)")
    set_status(state, f"Ready to process {count} image(s)")
    _clear_monitor(state)
    update_summary(state)
    _clear_context(state, silent=True)


def _select_output_folder(state: AppState) -> None:
    """Open folder dialog to select custom output folder."""
    path = filedialog.askdirectory()
    if path:
        state.custom_output_path.set(path)


def _browse_tesseract(state: AppState) -> None:
    """Open file dialog to select Tesseract executable."""
    path = filedialog.askopenfilename(filetypes=[("Tesseract Executable", "tesseract.exe")])
    if path:
        state.tesseract_path.set(path)


def _save_settings(state: AppState) -> None:
    """Save current settings to config file."""
    geometry = state.root.winfo_geometry()

    if state.context_widget:
        state.context_text.set(state.context_widget.get("1.0", "end").strip())

    save_config(state, geometry)
    apply_theme(state.root, state.ui_theme.get())
    messagebox.showinfo("Settings Saved", "✓ Your settings have been saved successfully.")


def _reset_token_usage(state: AppState) -> None:
    """Reset the token usage counter."""
    state.total_tokens.set(0)
    update_token_label(state)
    append_monitor_colored(state, "Token usage reset to 0", "warn")


def _reset_global_stats(state: AppState) -> None:
    """Reset global statistics."""
    if state.global_images_count:
        state.global_images_count.set(0)
        append_monitor_colored(state, "Global statistics reset", "warn")
    else:
        append_monitor_colored(state, "No statistics to reset", "warn")


def append_monitor_colored(state, message: str, level: str = "info") -> None:
    """Append a colored message to the activity log."""
    formatted = f"[{level.upper()}] {message}"
    state["logs"].append((formatted, level))
    _write_monitor_line_colored(state, (formatted, level))


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

def _sync_model_label(state, *_) -> None:
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


def validate_api_key(provider: str, api_key: str) -> tuple[bool, str]:
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


def update_api_key_validation_display(provider: str, api_key: str, status_label: ttk.Label) -> None:
    """Update the visual validation display for API keys."""
    is_valid, message = validate_api_key(provider, api_key)

    if not api_key:
        status_label.config(text="Not configured", foreground="#64748b")
    elif is_valid:
        status_label.config(text=f"✓ {message}", foreground="#059669")
    else:
        status_label.config(text=f"⚠ {message}", foreground="#d97706")

def _refresh_model_choices(state) -> None:
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

def _refresh_provider_sections(state) -> None:
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

    # Show/hide refresh button
    refresh_button = state.get("refresh_openrouter_button")
    if refresh_button:
        if provider_key == "openrouter":
            refresh_button.grid(row=0, column=2, sticky="e", padx=(16, 0))
        else:
            refresh_button.grid_remove()

def _update_api_status_labels(state) -> None:
    openai_key = state["openai_api_key"].get()
    update_api_key_validation_display("openai", openai_key, state["openai_status_label"])
    openrouter_key = state["openrouter_api_key"].get()
    update_api_key_validation_display("openrouter", openrouter_key, state["openrouter_status_label"])
    _refresh_provider_sections(state)

def initialize_provider_ui(state) -> None:
    """Initialize the provider UI state and event handlers."""
    state["llm_provider"].trace_add("write", lambda *_: (_refresh_provider_sections(state), _refresh_model_choices(state)))
    state["llm_model"].trace_add("write", lambda *_: _sync_model_label(state))
    state["openai_api_key"].trace_add("write", lambda *_: _update_api_status_labels(state))
    state["openrouter_api_key"].trace_add("write", lambda *_: _update_api_status_labels(state))

    # Initial UI state
    _refresh_provider_sections(state)
    _refresh_model_choices(state)


class PlaceholderEntry(ttk.Entry):
    """An entry widget that displays placeholder text."""

    def __init__(self, master=None, placeholder="PLACEHOLDER", **kwargs):
        super().__init__(master, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = PALETTE["grey_light"]
        self.default_fg_color = self["foreground"]
        self._is_placeholder = False

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._check_placeholder)

        self.after_idle(self._check_placeholder)

    def _check_placeholder(self, event=None):
        """Check if the placeholder should be added or removed."""
        if self.get() == "" and not self.focus_get() == self:
            self._add_placeholder()
        elif self.get() == self.placeholder:
            self._clear_placeholder()

    def _add_placeholder(self):
        """Add the placeholder text."""
        if self.get() == "":
            self._is_placeholder = True
            self.insert(0, self.placeholder)
            self["foreground"] = self.placeholder_color

    def _clear_placeholder(self, event=None):
        """Clear the placeholder text."""
        if self._is_placeholder:
            self.delete(0, "end")
            self["foreground"] = self.default_fg_color
            self._is_placeholder = False

    def get(self) -> str:
        """Return the entry's content, or an empty string if it's a placeholder."""
        if self._is_placeholder:
            return ""
        return super().get()

    def insert(self, index, string):
        """Insert text, clearing placeholder if necessary."""
        self._clear_placeholder()
        super().insert(index, string)

    def delete(self, first, last=None):
        """Delete text, checking for placeholder afterwards."""
        super().delete(first, last)
        self.after_idle(self._check_placeholder)


class Tooltip:
    """A tooltip that appears when hovering over a widget."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self._after_id = None
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<Destroy>", self._on_destroy)

    def _on_enter(self, event=None):
        """Schedule the tooltip to appear after a delay."""
        self._cancel_scheduled()
        self._after_id = self.widget.after(700, self._show_tooltip)

    def _on_leave(self, event=None):
        """Cancel scheduled tooltip or hide it if visible."""
        self._cancel_scheduled()
        self._hide_tooltip()

    def _on_destroy(self, event=None):
        """Ensure tooltip is destroyed when the parent widget is."""
        self._cancel_scheduled()
        self._hide_tooltip()

    def _cancel_scheduled(self):
        """Cancel any pending after() callbacks."""
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show_tooltip(self):
        """Create and display the tooltip window."""
        if not self.widget.winfo_exists():
            return

        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        theme_bg = ttk.Style().lookup("TFrame", "background")
        theme_fg = ttk.Style().lookup("TLabel", "foreground")

        label = ttk.Label(
            self.tooltip_window,
            text=self.text,
            justify="left",
            background=theme_bg,
            foreground=theme_fg,
            relief="solid",
            borderwidth=1,
            wraplength=200,
        )
        label.pack(ipadx=4, ipady=4)

    def _hide_tooltip(self):
        """Destroy the tooltip window if it exists."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def create_tooltip(widget, text):
    """Create a tooltip for a widget."""
    return Tooltip(widget, text)
