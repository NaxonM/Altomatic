"""Application bootstrap for Altomatic."""

from __future__ import annotations

import queue
import threading
from importlib import resources
from tkinter import messagebox

from tkinterdnd2 import TkinterDnD

from .config.manager import DEFAULT_CONFIG, load_config, reset_config, save_config
from .core.processor import process_images
from .ui.components import append_monitor_colored, build_ui, set_status
from .ui.dragdrop import configure_drag_and_drop
from .ui.themes import apply_theme


def _scaled_geometry(widget, base_width: int, base_height: int) -> str:
    widget.update_idletasks()
    screen_w = widget.winfo_screenwidth()
    screen_h = widget.winfo_screenheight()

    min_w = int(screen_w * 0.55)
    max_w = int(screen_w * 0.9)
    min_h = int(screen_h * 0.55)
    max_h = int(screen_h * 0.9)

    width = min(max(base_width, min_w), max_w)
    height = min(max(base_height, min_h), max_h)

    width = max(720, min(width, screen_w - 40))
    height = max(540, min(height, screen_h - 80))

    return f"{width}x{height}"


def _apply_window_icon(window) -> None:
    try:
        with resources.as_file(
            resources.files("altomatic.resources") / "altomatic_icon.ico"
        ) as icon_path:
            window.iconbitmap(default=str(icon_path))
    except Exception:
        pass


def run() -> None:
    """Initialize the UI, wire dependencies, and start the main loop."""
    user_config = load_config()

    root = TkinterDnD.Tk()
    root.title("Altomatic")
    stored_geometry = user_config.get("window_geometry", DEFAULT_CONFIG.get("window_geometry", "1133x812"))
    if stored_geometry == DEFAULT_CONFIG.get("window_geometry", "1133x812"):
        geometry = _scaled_geometry(root, 1133, 812)
    else:
        geometry = stored_geometry
    root.geometry(geometry)
    root.resizable(True, True)
    _apply_window_icon(root)

    current_theme = user_config.get("ui_theme", "Arctic Light")  # Changed default
    apply_theme(root, current_theme)

    state = build_ui(root, user_config)
    state["root"] = root

    # Apply the theme once the window is mapped to the screen
    has_been_mapped = False

    def on_first_map(event):
        nonlocal has_been_mapped
        if not has_been_mapped:
            apply_theme(root, state["ui_theme"].get())
            has_been_mapped = True

    root.bind("<Map>", on_first_map)

    # Create a thread-safe queue for communication
    ui_queue = queue.Queue()
    state["ui_queue"] = ui_queue

    def start_image_processing():
        """Run image processing in a separate thread."""
        state["process_button"].config(state="disabled")
        set_status(state, "Starting...")
        thread = threading.Thread(
            target=process_images,
            args=(state,),
            daemon=True,
        )
        thread.start()

    def process_queue():
        """Check queue for messages from the processor and update UI."""
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

    # Start the queue processor
    root.after(100, process_queue)
    root.mainloop()
