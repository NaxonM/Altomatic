"""Drag-and-drop bindings."""

from __future__ import annotations

import os

from tkinterdnd2 import DND_FILES

import shutil
import tempfile

from ..utils import get_image_count_in_folder
from .ui_toolkit import append_monitor_colored, cleanup_temp_drop_folder


def configure_drag_and_drop(root, state) -> None:
    state["input_card"].drop_target_register(DND_FILES)
    state["input_card"].dnd_bind("<<Drop>>", lambda event: _handle_input_drop(event, state))


def _handle_input_drop(event, state) -> None:
    paths_list = event.widget.tk.splitlist(event.data)
    input_files: list[str] = []
    recursive = state["recursive_search"].get()

    for raw_path in paths_list:
        clean_path = raw_path.strip("{}")
        if os.path.isdir(clean_path):
            cleanup_temp_drop_folder(state)
            state["input_type"].set("Folder")
            state["input_path"].set(clean_path)
            count = get_image_count_in_folder(clean_path, recursive)
            state["image_count"].set(f"{count} image(s) found.")
            if "context_widget" in state:
                state["context_widget"].delete("1.0", "end")
                state["context_text"].set("")
            append_monitor_colored(state, f"[DRAGDROP] Folder dropped: {clean_path} ({count} images)", "info")
            return
        if os.path.isfile(clean_path):
            input_files.append(clean_path)

    if input_files:
        if len(input_files) == 1:
            cleanup_temp_drop_folder(state)
            state["input_type"].set("File")
            state["input_path"].set(input_files[0])
            state["image_count"].set("1 image selected.")
            if "context_widget" in state:
                state["context_widget"].delete("1.0", "end")
                state["context_text"].set("")
            append_monitor_colored(state, f"[DRAGDROP] Single file dropped: {input_files[0]}", "info")
        else:
            cleanup_temp_drop_folder(state)
            drop_folder = tempfile.mkdtemp(prefix="altomatic_dropped_")
            for image in input_files:
                basename = os.path.basename(image)
                target = os.path.join(drop_folder, basename)
                try:
                    shutil.copy(image, target)
                except Exception as exc:
                    append_monitor_colored(state, f"[WARN] Failed to copy {image}: {exc}", "warn")

            state["temp_drop_folder"] = drop_folder
            state["input_type"].set("Folder")
            state["input_path"].set(drop_folder)
            count = get_image_count_in_folder(drop_folder, recursive)
            state["image_count"].set(f"{count} image(s) dropped.")
            if "context_widget" in state:
                state["context_widget"].delete("1.0", "end")
                state["context_text"].set("")
            append_monitor_colored(state, f"[DRAGDROP] {len(input_files)} files => {drop_folder}", "info")
