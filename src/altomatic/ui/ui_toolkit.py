import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from importlib import resources

try:
    import pyperclip
except ModuleNotFoundError:
    pyperclip = None

from ..config import save_config
from ..models import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    format_pricing,
    get_default_model,
    get_models_for_provider,
    get_provider_label,
)
from ..prompts import load_prompts
from ..utils import (
    configure_global_proxy,
    get_image_count_in_folder,
    get_requests_proxies,
    reload_system_proxies,
    set_proxy_preferences,
)
from ..services.provider_health import check_openai_key, check_openrouter_key
from ..services.providers.exceptions import APIError, AuthenticationError, NetworkError
from .themes import apply_theme


RECENT_INPUT_LIMIT = 5
MAX_LOG_ENTRIES = 1000


class AnimatedLabel(ttk.Label):
    """Label with animated scrolling for overflow text."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.full_text = ""
        self.running = False
        self.bind("<Configure>", self.check_width)

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
        first_char = text[0]
        rest = text[1:]
        new_text = rest + first_char
        self.config(text=new_text)
        self.after(200, self.animate)


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

        self.toggle_button = ttk.Button(self.header_frame, text="▶", command=self.toggle, width=4)
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

        except Exception:
            pass

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
        with resources.as_file(resources.files("altomatic.resources") / "altomatic_icon.ico") as icon_path:
            window.iconbitmap(default=str(icon_path))
    except Exception:
        pass


def _create_section_header(parent, text: str, style="Header.TLabel") -> ttk.Label:
    """Create a consistent section header."""
    return ttk.Label(parent, text=text, style=style)


def _create_info_label(parent, text: str, wraplength=500) -> ttk.Label:
    """Create a consistent info/help label."""
    return ttk.Label(parent, text=text, style="Small.TLabel", wraplength=wraplength, justify="left")


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


def _build_prompt_display_map(prompts: dict[str, dict]) -> dict[str, str]:
    """Return display labels that remain unique even when prompt labels repeat."""
    labels = [entry.get("label") or key for key, entry in prompts.items()]
    counts = Counter(labels)
    display_map: dict[str, str] = {}
    for key, entry in prompts.items():
        label = entry.get("label") or key
        display_map[key] = f"{label} — {key}" if counts[label] > 1 else label
    return display_map


def update_summary(state) -> None:
    """Update the summary chips with current selections."""
    chip_model_var = state.get("summary_chip_model_var")
    chip_prompt_var = state.get("summary_chip_prompt_var")
    chip_output_var = state.get("summary_chip_output_var")
    chip_alttext_var = state.get("summary_chip_alttext_var")
    if not all([chip_model_var, chip_prompt_var, chip_output_var, chip_alttext_var]):
        return

    provider_var = state.get("llm_provider")
    provider = provider_var.get() if provider_var is not None else DEFAULT_PROVIDER
    model_var = state.get("llm_model")
    model_id = model_var.get() if model_var is not None else DEFAULT_MODEL
    models = get_models_for_provider(provider)
    model_label = models.get(model_id, {}).get("label", model_id)
    model_text = f"Model: {get_provider_label(provider)} • {model_label}"

    prompts = state.get("prompts") or load_prompts()
    prompt_key = state["prompt_key"].get()
    prompt_entry = prompts.get(prompt_key) or prompts.get("default") or next(iter(prompts.values()), {})
    prompt_text = f"Prompt: {prompt_entry.get('label', prompt_key)}"

    destination = state["output_folder_option"].get()
    if destination == "Custom":
        path = state["custom_output_path"].get().strip() or "(not set)"
        output_text = f"Output: Custom → {path}"
    else:
        output_text = f"Output: {destination}"

    summary_chip_model_var = state["summary_chip_model_var"]
    summary_chip_prompt_var = state["summary_chip_prompt_var"]
    summary_chip_output_var = state["summary_chip_output_var"]
    summary_chip_alttext_var = state["summary_chip_alttext_var"]

    summary_chip_model_var.set(model_text.replace("Model: ", ""))
    summary_chip_prompt_var.set(prompt_text.replace("Prompt: ", ""))
    summary_chip_output_var.set(output_text.replace("Output: ", ""))
    alttext_value = state.get("alttext_language").get() if state.get("alttext_language") else "English"
    alttext_text = f"Alt text: {alttext_value}"
    summary_chip_alttext_var.set(alttext_text.replace("Alt text: ", ""))

    # Update tooltips with richer detail
    model_tooltip = state.get("summary_chip_model_tooltip")
    if model_tooltip is not None:
        pricing = format_pricing(provider, model_id)
        tooltip_lines = [model_label]
        tooltip_lines.append(f"Provider: {get_provider_label(provider)}")
        tooltip_lines.append(f"Model ID: {model_id}")
        if pricing and pricing != "Pricing unavailable":
            tooltip_lines.append(pricing)
        tooltip_lines.append("Click to adjust provider & model")
        model_tooltip.text = "\n".join(tooltip_lines)

    prompt_tooltip = state.get("summary_chip_prompt_tooltip")
    if prompt_tooltip is not None:
        template_preview = prompt_entry.get("template", "").strip()
        first_line = template_preview.splitlines()[0] if template_preview else "(no template preview)"
        info = [
            f"Preset: {prompt_entry.get('label', prompt_key)}",
            f"Key: {prompt_key}",
            first_line[:120],
            "Click to edit prompts",
        ]
        prompt_tooltip.text = "\n".join([line for line in info if line])

    output_tooltip = state.get("summary_chip_output_tooltip")
    if output_tooltip is not None:
        output_details = [destination]
        if destination == "Custom":
            output_details.append(path)
        output_details.append("Click to adjust output settings")
        output_tooltip.text = "\n".join(output_details)

    alttext_tooltip = state.get("summary_chip_alttext_tooltip")
    if alttext_tooltip is not None:
        alttext_tooltip.text = f"Alt-text language: {alttext_value}\nClick to edit processing options"


def refresh_recent_input_menu(state) -> None:
    """Rebuild the recent input folder menu based on current history."""
    button = state.get("recent_input_button")
    menu = state.get("recent_input_menu")
    if not button or not menu:
        return

    menu.delete(0, "end")
    recent_paths = state.get("recent_input_paths") or []
    if len(recent_paths) > RECENT_INPUT_LIMIT:
        del recent_paths[RECENT_INPUT_LIMIT:]

    if not recent_paths:
        menu.add_command(label="No recent folders", state="disabled")
        try:
            button.state(["disabled"])
        except tk.TclError:
            pass
        return

    try:
        button.state(["!disabled"])
    except tk.TclError:
        pass

    for path in recent_paths:
        menu.add_command(
            label=path,
            command=lambda value=path: set_input_folder(state, value, add_recent=True),
        )


def add_recent_input_path(state, path: str) -> None:
    """Record a recently used input folder and update UI affordances."""
    if not path or not os.path.isdir(path):
        return

    normalized = os.path.normpath(path)
    recent = state.setdefault("recent_input_paths", [])
    if normalized in recent:
        recent.remove(normalized)
    recent.insert(0, normalized)

    if len(recent) > RECENT_INPUT_LIMIT:
        del recent[RECENT_INPUT_LIMIT:]

    refresh_recent_input_menu(state)


def open_folder_location(state, path: str) -> None:
    """Open a folder in the system file explorer with gentle user feedback."""
    if not path:
        set_status(state, "No folder to open")
        return

    folder = os.path.normpath(path)

    if not os.path.isdir(folder):
        set_status(state, "Folder path is unavailable")
        return

    try:
        if sys.platform.startswith("win"):
            os.startfile(folder)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
        set_status(state, f"Opened folder: {folder}")
    except Exception as exc:
        set_status(state, f"Could not open folder: {exc}")


def set_input_folder(
    state,
    folder_path: str,
    *,
    add_recent: bool = True,
    cleanup_temp: bool = True,
    status_prefix: str | None = None,
) -> int | None:
    """Apply a folder selection to the UI and optionally record it in history."""
    if not folder_path or not os.path.isdir(folder_path):
        set_status(state, "Folder path is unavailable")
        refresh_recent_input_menu(state)
        return None

    folder = os.path.normpath(folder_path)

    if cleanup_temp:
        cleanup_temp_drop_folder(state)

    state["input_type"].set("Folder")
    state["input_path"].set(folder)

    recursive = state["recursive_search"].get()
    image_count = get_image_count_in_folder(folder, recursive)
    state["image_count"].set(f"{image_count} image(s)")

    message = status_prefix or f"Ready to process {image_count} image(s)"
    set_status(state, message)
    _clear_monitor(state)
    update_summary(state)
    _clear_context(state, silent=True)

    if add_recent:
        add_recent_input_path(state, folder_path)
    else:
        refresh_recent_input_menu(state)

    return image_count


def format_global_stats(count: int) -> str:
    """Return a formatted global statistics string."""
    return f"Images processed: {count:,}"


def update_global_stats_label(state) -> None:
    """Update the global statistics label text if present."""
    if "global_images_label" not in state or "global_images_count" not in state:
        return
    count = int(state["global_images_count"].get())
    state["global_images_label"].set(format_global_stats(count))


def set_status(
    state,
    message: str,
    *,
    duration_ms: int | None = None,
    restore_message: str | None = None,
    persist: bool | None = None,
) -> None:
    """Update the status bar message, optionally resetting after a delay."""
    status_var = state.get("status_var")
    if status_var is None:
        return

    try:
        status_var.set(message)
    except Exception:
        return

    if duration_ms is not None and duration_ms <= 0:
        duration_ms = None

    if persist is None:
        persist = duration_ms is None

    if persist:
        state["status_idle_default"] = message

    root = state.get("root")
    if root is None:
        state["_status_after_id"] = None
        return

    after_id = state.get("_status_after_id")
    if after_id is not None:
        try:
            root.after_cancel(after_id)
        except Exception:
            pass
        finally:
            state["_status_after_id"] = None

    if duration_ms is None:
        return

    fallback = restore_message if restore_message is not None else state.get("status_idle_default", "Ready")

    def _reset_status() -> None:
        state["_status_after_id"] = None
        current = status_var.get()
        if current == message:
            try:
                status_var.set(fallback)
            except Exception:
                pass

    state["_status_after_id"] = root.after(duration_ms, _reset_status)


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
    display_map = _build_prompt_display_map(prompts)
    state["prompt_display_map"] = display_map

    def _select_prompt(key: str) -> None:
        state["prompt_key"].set(key)
        label_var = state.get("prompt_label_var")
        if label_var is not None:
            label_var.set(display_map.get(key, key))
        update_summary(state)

    menu = state.get("prompt_option_menu")
    if menu:
        menu.delete(0, "end")
        for key, display in display_map.items():
            menu.add_command(label=display, command=lambda value=key: _select_prompt(value))

    current = state["prompt_key"].get()
    if current not in prompts and prompts:
        current = next(iter(prompts.keys()))
        state["prompt_key"].set(current)

    label_var = state.get("prompt_label_var")
    if label_var is not None:
        label_var.set(display_map.get(current, current))

    update_prompt_preview(state)
    update_summary(state)


def cleanup_temp_drop_folder(state) -> None:
    """Clean up temporary drop folder if it exists."""
    folder = state.get("temp_drop_folder")
    if folder and os.path.isdir(folder):
        try:
            shutil.rmtree(folder)
        except OSError:
            pass
    state["temp_drop_folder"] = None


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
    _trim_log_if_needed(state)
    formatted = f"[{level.upper()}] {message}"
    state["logs"].append((formatted, level))
    _write_monitor_line_colored(state, (formatted, level))


def test_provider_connection(state, provider: str) -> dict:
    """Run a provider connectivity check using the current proxy preferences."""
    provider = provider.lower().strip()
    key_var = state.get(f"{provider}_api_key")
    if key_var is None:
        raise APIError("API key field is unavailable for the chosen provider.")

    api_key = key_var.get().strip()
    if not api_key:
        raise AuthenticationError("Enter an API key before testing the connection.")

    proxy_enabled_var = state.get("proxy_enabled")
    proxy_override_var = state.get("proxy_override")

    proxy_enabled = bool(proxy_enabled_var.get()) if proxy_enabled_var is not None else True
    proxy_override = proxy_override_var.get().strip() if proxy_override_var is not None else ""

    configure_global_proxy(enabled=proxy_enabled, override=proxy_override or None, force=False)
    proxies = get_requests_proxies(enabled=proxy_enabled, override=proxy_override or None)

    if provider == "openai":
        return check_openai_key(api_key, proxies=proxies)
    if provider == "openrouter":
        return check_openrouter_key(api_key, proxies=proxies)

    raise APIError(f"Unknown provider '{provider}' for health check.")


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

    if state.get("activity_filters"):
        if not _log_item_matches_filters(log_item, state["activity_filters"]):
            return

    text_widget = state["log_text"]
    text, level = log_item

    if "show_timestamps" in state and state["show_timestamps"].get():
        timestamp = datetime.now().strftime("%H:%M:%S")
        text = f"{timestamp} {text}"

    text_widget.config(state="normal")
    text_widget.insert("end", str(text) + "\n", level)

    auto_scroll_var = state.get("log_auto_scroll")
    if auto_scroll_var is None or auto_scroll_var.get():
        text_widget.see("end")

    text_widget.config(state="disabled")
def _trim_log_if_needed(state) -> None:
    """Keep the log buffer within the configured limit."""
    max_entries = state.get("log_entry_limit", MAX_LOG_ENTRIES)
    logs = state.get("logs")
    if logs is None or max_entries <= 0:
        return
    trimmed = False
    while len(logs) >= max_entries:
        logs.pop(0)
        trimmed = True
    if trimmed:
        refresh_log_view(state)


def _log_item_matches_filters(log_item: tuple[str, str], filters: dict[str, bool]) -> bool:
    """Return True if the log item should be shown for the active filters."""
    if not filters:
        return True
    text, level = log_item
    level = level.lower()
    allowed_levels = [lvl for lvl, enabled in filters.get("levels", {}).items() if enabled]
    if allowed_levels and level not in allowed_levels:
        return False
    keyword = filters.get("keyword", "").strip().lower()
    if keyword and keyword not in text.lower():
        return False
    return True


def refresh_log_view(state) -> None:
    """Re-render the entire activity log with current filters."""
    if "log_text" not in state:
        return
    text_widget = state["log_text"]
    text_widget.config(state="normal")
    text_widget.delete("1.0", "end")

    for log_item in state.get("logs", []):
        _write_monitor_line_colored(state, log_item)

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

    set_input_folder(state, input_path)


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
        update_global_stats_label(state)
        append_monitor_colored(state, "Global statistics reset", "warn")
    else:
        append_monitor_colored(state, "No statistics to reset", "warn")


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
            pricing_info.append(f"Context: {context_window:,} tokens")

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
    state["llm_provider"].trace_add(
        "write", lambda *_: (_refresh_provider_sections(state), _refresh_model_choices(state))
    )
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
        self.placeholder_color = "grey"
        self.default_fg_color = self["foreground"]

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)

        self._add_placeholder()

    def _add_placeholder(self, e=None):
        if not self.get():
            self.insert(0, self.placeholder)
            self["foreground"] = self.placeholder_color

    def _clear_placeholder(self, e=None):
        if self.get() == self.placeholder:
            self.delete(0, "end")
            self["foreground"] = self.default_fg_color


class Tooltip:
    """Create a tooltip for a given widget."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        try:
            bbox = self.widget.bbox("insert")
        except Exception:
            bbox = None

        if bbox:
            x, y, _, _ = bbox
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 25
        else:
            x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        style = ttk.Style()
        bg = style.lookup("TFrame", "background")
        fg = style.lookup("TLabel", "foreground")

        label = ttk.Label(
            self.tooltip_window,
            text=self.text,
            justify="left",
            background=bg,
            foreground=fg,
            relief="solid",
            borderwidth=1,
            wraplength=200,
        )
        label.pack(ipadx=4, ipady=4)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None


def create_tooltip(widget, text):
    """Create a tooltip for a widget."""
    return Tooltip(widget, text)


class ScrollableFrame(ttk.Frame):
    """Reusable scrollable frame with scoped mouse-wheel handling."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        style = ttk.Style()
        bg_color = style.lookup("TFrame", "background")

        self.canvas = tk.Canvas(self, highlightthickness=0, bg=bg_color)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.scrollable_frame.bind("<Enter>", self._bind_mousewheel)
        self.scrollable_frame.bind("<Leave>", self._unbind_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _bind_mousewheel(self, _event):
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event):
        self.canvas.unbind("<MouseWheel>")
        self.canvas.unbind("<Button-4>")
        self.canvas.unbind("<Button-5>")

    def _on_mousewheel(self, event):
        if getattr(event, "delta", 0):
            self.canvas.yview_scroll(-int(event.delta / 120), "units")
        elif getattr(event, "num", None) == 4:
            self.canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            self.canvas.yview_scroll(1, "units")
        return "break"
