"""Image processing pipeline."""

from __future__ import annotations

import os
import shutil
from queue import Queue

from ..models import DEFAULT_PROVIDER, get_provider_label
from ..services.ai import describe_image
from ..ui import cleanup_temp_drop_folder
from ..utils.images import (
    generate_output_filename,
    generate_session_folder_name,
    get_all_images,
    get_output_folder,
    slugify,
)


def process_images(state) -> None:
    """The core image processing pipeline."""
    ui_queue: Queue = state["ui_queue"]

    try:
        provider_var = state.get("llm_provider")
        provider = provider_var.get() if provider_var is not None else DEFAULT_PROVIDER
        if provider not in {"openai", "openrouter"}:
            provider = DEFAULT_PROVIDER

        api_key_field = "openrouter_api_key" if provider == "openrouter" else "openai_api_key"
        api_key = state[api_key_field].get().strip() if api_key_field in state else ""
        if not api_key:
            ui_queue.put(
                {
                    "type": "error",
                    "title": "Missing API Key",
                    "value": f"Please enter your {get_provider_label(provider)} API key in the Settings tab.",
                }
            )
            return

        input_path = state["input_path"].get()
        if not os.path.exists(input_path):
            ui_queue.put({"type": "error", "title": "Invalid Input", "value": "Input path does not exist."})
            return

        if state["input_type"].get() == "File":
            images = [input_path]
        else:
            images = get_all_images(input_path)

        if not images:
            ui_queue.put({"type": "error", "title": "No Images", "value": "No valid image files found."})
            return

        ui_queue.put({"type": "log", "value": f"Found {len(images)} images to process.", "level": "info"})
        state["total_tokens"].set(0)

        base_output_folder = get_output_folder(state)
        os.makedirs(base_output_folder, exist_ok=True)

        session_name = generate_session_folder_name()
        session_path = os.path.join(base_output_folder, session_name)
        os.makedirs(session_path, exist_ok=True)
        ui_queue.put({"type": "log", "value": f"Session folder: {session_path}", "level": "info"})

        renamed_folder = os.path.join(session_path, "renamed_images")
        os.makedirs(renamed_folder, exist_ok=True)

        summary_path = os.path.join(session_path, generate_output_filename())
        log_path = os.path.join(session_path, "failed.log")

        ui_queue.put({"type": "progress_max", "value": len(images)})
        ui_queue.put({"type": "progress", "value": 0})

        failed_items: list[tuple[str, str]] = []

        with open(summary_path, "w", encoding="utf-8") as summary_file:
            for index, image_path in enumerate(images):
                try:
                    ui_queue.put({"type": "log", "value": f"Analyzing {image_path}", "level": "info"})
                    result = describe_image(state, image_path)

                    if not result or "name" not in result or "alt" not in result:
                        raise ValueError("Invalid or empty response from the model.")

                    base_name = slugify(result["name"])[:100]
                    if not base_name:
                        base_name = f"image-{index + 1}"

                    ext = os.path.splitext(image_path)[1].lower()
                    new_name = f"{base_name}{ext}"
                    destination = os.path.join(renamed_folder, new_name)
                    counter = 1
                    while os.path.exists(destination):
                        destination = os.path.join(renamed_folder, f"{base_name}-{counter}{ext}")
                        counter += 1

                    shutil.copy(image_path, destination)

                    final_name = os.path.basename(destination)
                    summary_file.write(f"[Original: {os.path.basename(image_path)}]\n")
                    summary_file.write(f"Name: {os.path.splitext(final_name)[0]}\n")
                    summary_file.write(f"Alt: {result['alt']}\n\n")
                    ui_queue.put({"type": "log", "value": f"-> {final_name}", "level": "success"})

                except Exception as exc:
                    failed_items.append((image_path, str(exc)))
                    ui_queue.put({"type": "log", "value": f"FAIL: {image_path} :: {exc}", "level": "error"})

                ui_queue.put({"type": "progress", "value": index + 1})

        if failed_items:
            with open(log_path, "w", encoding="utf-8") as log_file:
                for path, error in failed_items:
                    log_file.write(f"{path} :: {error}\n")
        elif os.path.exists(log_path):
            try:
                os.remove(log_path)
            except OSError:
                pass

        if "global_images_count" in state:
            previous = state["global_images_count"].get()
            new_total = previous + len(images)
            state["global_images_count"].set(new_total)
        else:
            new_total = len(images)

        total_tokens = state["total_tokens"].get()
        message = (
            f"Processed {len(images)} image(s).\n"
            f"Session folder: {session_path}\n"
            f"Output file: {os.path.basename(summary_path)}\n\n"
            f"Token usage this run: {total_tokens}\n"
            f"Total images analyzed overall: {new_total}"
        )
        ui_queue.put({"type": "log", "value": message.replace("\n", " | "), "level": "info"})
        ui_queue.put({"type": "done", "value": message})

    except Exception as exc:
        ui_queue.put(
            {
                "type": "error",
                "title": "Processing Error",
                "value": f"An unexpected error occurred: {exc}",
            }
        )
    finally:
        cleanup_temp_drop_folder(state)
