"""Drag-and-drop bindings."""

from __future__ import annotations

import os

from tkinterdnd2 import DND_FILES

import shutil
import tempfile
import atexit

from ..utils import get_image_count_in_folder
from .ui_toolkit import append_monitor_colored, cleanup_temp_drop_folder


def configure_drag_and_drop(root, state: dict[str, Any]) -> None:
    input_card = state.get("input_card")
    if input_card:
        input_card.drop_target_register(DND_FILES)
        input_card.dnd_bind("<<Drop>>", lambda event: _handle_input_drop(event, state))


def _handle_input_drop(event, state: dict[str, Any]) -> None:
    paths_list = event.widget.tk.splitlist(event.data)
    input_files: list[str] = []
    recursive_var = state.get("recursive_search")
    recursive = recursive_var.get() if recursive_var else False

    for raw_path in paths_list:
        clean_path = raw_path.strip("{}")
        if os.path.isdir(clean_path):
            cleanup_temp_drop_folder(state)
            if state.get("input_type"):
                state["input_type"].set("Folder")
            if state.get("input_path"):
                state["input_path"].set(clean_path)
            count = get_image_count_in_folder(clean_path, recursive)
            if state.get("image_count"):
                state["image_count"].set(f"{count} image(s) found.")

            context_widget = state.get("context_widget")
            if context_widget:
                context_widget.delete("1.0", "end")
            if state.get("context_text"):
                state["context_text"].set("")

            append_monitor_colored(state, f"[DRAGDROP] Folder dropped: {clean_path} ({count} images)", "info")
            return
        if os.path.isfile(clean_path):
            input_files.append(clean_path)

    if input_files:
        context_widget = state.get("context_widget")
        if context_widget:
            context_widget.delete("1.0", "end")
        if state.get("context_text"):
            state["context_text"].set("")

        if len(input_files) == 1:
            cleanup_temp_drop_folder(state)
            if state.get("input_type"):
                state["input_type"].set("File")
            if state.get("input_path"):
                state["input_path"].set(input_files[0])
            if state.get("image_count"):
                state["image_count"].set("1 image selected.")
            append_monitor_colored(state, f"[DRAGDROP] Single file dropped: {input_files[0]}", "info")
        else:
            cleanup_temp_drop_folder(state)
            drop_folder = tempfile.mkdtemp(prefix="altomatic_dropped_")
            atexit.register(shutil.rmtree, drop_folder, ignore_errors=True)

            for image in input_files:
                basename = os.path.basename(image)
                name, ext = os.path.splitext(basename)
                target = os.path.join(drop_folder, basename)
                counter = 1
                while os.path.exists(target):
                    target = os.path.join(drop_folder, f"{name}-{counter}{ext}")
                    counter += 1
                try:
                    shutil.copy(image, target)
                except Exception as exc:
                    append_monitor_colored(state, f"[WARN] Failed to copy {image}: {exc}", "warn")

            state["temp_drop_folder"] = drop_folder
            if state.get("input_type"):
                state["input_type"].set("Folder")
            if state.get("input_path"):
                state["input_path"].set(drop_folder)
            count = get_image_count_in_folder(drop_folder, recursive)
            if state.get("image_count"):
                state["image_count"].set(f"{count} image(s) dropped.")
            append_monitor_colored(state, f"[DRAGDROP] {len(input_files)} files => {drop_folder}", "info")
