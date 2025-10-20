"""Application bootstrap for Altomatic."""

from __future__ import annotations

import queue
import threading
from importlib import resources
from tkinter import messagebox

from tkinterdnd2 import TkinterDnD

from .config.manager import DEFAULT_CONFIG, load_config, reset_config, save_config
from .core.processor import process_images
from .ui.components import build_ui
from .ui.ui_toolkit import append_monitor_colored, set_status
from .ui.dragdrop import configure_drag_and_drop
from .ui.results import create_results_window
from .ui.themes import apply_theme
from .utils import configure_global_proxy, set_proxy_preferences


def _scaled_geometry(widget, base_width: int, base_height: int) -> str:
    widget.update_idletasks()
    screen_w = widget.winfo_screenwidth()
    screen_h = widget.winfo_screenheight()

    min_w = int(screen_w * 0.4)
    max_w = int(screen_w * 0.8)
    min_h = int(screen_h * 0.5)
    max_h = int(screen_h * 0.9)

    width = min(max(base_width, min_w), max_w)
    height = min(max(base_height, min_h), max_h)

    width = max(540, min(width, screen_w - 40))
    height = max(600, min(height, screen_h - 80))

    return f"{width}x{height}"


def _apply_window_icon(window) -> None:
    try:
        with resources.as_file(resources.files("altomatic.resources") / "altomatic_icon.ico") as icon_path:
            window.iconbitmap(default=str(icon_path))
    except Exception:
        pass


def run() -> None:
    """Initialize the UI, wire dependencies, and start the main loop."""
    user_config = load_config()

    set_proxy_preferences(
        user_config.get("proxy_enabled", True),
        user_config.get("proxy_override", ""),
    )
    configure_global_proxy(force=True)

    root = TkinterDnD.Tk()
    root.title("Altomatic")
    stored_geometry = user_config.get("window_geometry", DEFAULT_CONFIG.get("window_geometry", "540x680"))
    if stored_geometry == DEFAULT_CONFIG.get("window_geometry", "540x680"):
        geometry = _scaled_geometry(root, 540, 680)
    else:
        geometry = stored_geometry
    root.geometry(geometry)
    root.resizable(True, True)
    _apply_window_icon(root)

    current_theme = user_config.get("ui_theme", "Arctic Light")
    apply_theme(root, current_theme)

    state = build_ui(root, user_config)
    state["root"] = root

    has_been_mapped = False

    def on_first_map(event):
        nonlocal has_been_mapped
        if not has_been_mapped:
            apply_theme(root, state["ui_theme"].get())
            has_been_mapped = True

    root.bind("<Map>", on_first_map)

    ui_queue = queue.Queue()
    state["ui_queue"] = ui_queue

    def start_image_processing():
        # Pre-flight checks
        provider = state["llm_provider"].get()
        api_key_var = f"{provider}_api_key"
        if not state[api_key_var].get().strip():
            messagebox.showerror(
                "API Key Missing",
                f"The API key for {provider} is not set. Please add it in the 'Prompts & Model' tab.",
            )
            # Switch to the correct tab to guide the user
            if "notebook" in state:
                state["notebook"].select(1)  # 1 is the index for "Prompts & Model" tab
            return

        # Switch to log tab and start processing
        if "notebook" in state:
            state["notebook"].select(2)  # 2 is the index for "Activity Log" tab
        state["process_button"].config(state="disabled")
        set_status(state, "Starting...")
        thread = threading.Thread(
            target=process_images,
            args=(state,),
            daemon=True,
        )
        thread.start()

    def process_queue():
        try:
            message = ui_queue.get_nowait()
            msg_type = message.get("type")
            value = message.get("value")

            if msg_type == "status":
                set_status(state, value)
            elif msg_type == "progress":
                if "progress_bar" in state:
                    state["progress_bar"]["value"] = value
            elif msg_type == "progress_max":
                if "progress_bar" in state:
                    state["progress_bar"]["maximum"] = value
            elif msg_type == "log":
                append_monitor_colored(state, value, message.get("level", "info"))
            elif msg_type == "done":
                state["process_button"].config(state="normal")
                set_status(state, "✅ Done!")
                messagebox.showinfo("Done", value)
            elif msg_type == "done_with_results":
                state["process_button"].config(state="normal")
                set_status(state, "✅ Done!")
                create_results_window(state, message.get("results"))
            elif msg_type == "error":
                state["process_button"].config(state="normal")
                messagebox.showerror(message.get("title", "Error"), value)
        except queue.Empty:
            pass
        finally:
            root.after(100, process_queue)

    state["process_button"].config(command=start_image_processing)
    configure_drag_and_drop(root, state)

    def on_reset_config() -> None:
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings?"):
            reset_config()
            messagebox.showinfo("Reset", "Settings reset. Please restart the application.")
            root.destroy()

    state["reset_config_callback"] = on_reset_config

    def on_close() -> None:
        geometry = root.winfo_geometry().split("+")[0]
        save_config(state, geometry)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    root.after(100, process_queue)
    root.mainloop()
