"""Image processing pipeline."""

from __future__ import annotations

import os
import shutil
from queue import Queue
from typing import Dict, Any, List

from PIL import UnidentifiedImageError

from ..models import DEFAULT_PROVIDER, get_provider_label
from ..services.ai import describe_image
from ..services.providers.exceptions import AuthenticationError, APIError, NetworkError
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
    results: List[Dict[str, Any]] = []

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

        base_output_folder = get_output_folder(state)
        if not os.access(base_output_folder, os.W_OK):
            ui_queue.put(
                {
                    "type": "error",
                    "title": "Permission Error",
                    "value": f"Cannot write to the selected output directory:\n{base_output_folder}",
                }
            )
            return

        if state["input_type"].get() == "File":
            images = [input_path]
        else:
            recursive = state["include_subdirectories"].get()
            images = get_all_images(input_path, recursive)

        if not images:
            ui_queue.put({"type": "error", "title": "No Images", "value": "No valid image files found."})
            return

        ui_queue.put({"type": "log", "value": f"Found {len(images)} images to process.", "level": "info"})
        state["total_tokens"].set(0)

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

        failed_items: list[tuple[str, str, int]] = []

        def _process_single_image(image_path: str, index: int, summary_handle, *, attempt: str = "primary") -> tuple[bool, str]:
            attempt_tag = "[Retry] " if attempt == "retry" else ""
            try:
                ui_queue.put({"type": "log", "value": f"{attempt_tag}Analyzing {image_path}", "level": "info"})
                result = describe_image(state, image_path)

                if not result or "name" not in result or "alt" not in result:
                    raise APIError("Invalid or empty response from the model.")

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
                summary_handle.write(f"[Original: {os.path.basename(image_path)}]\n")
                summary_handle.write(f"Name: {os.path.splitext(final_name)[0]}\n")
                summary_handle.write(f"Alt: {result['alt']}\n\n")
                ui_queue.put({"type": "log", "value": f"{attempt_tag}-> {final_name}", "level": "success"})

                results.append(
                    {
                        "original_path": image_path,
                        "original_filename": os.path.basename(image_path),
                        "new_filename": final_name,
                        "alt_text": result["alt"],
                    }
                )

                return True, ""

            except UnidentifiedImageError:
                message = "Unsupported or corrupted image format."
                ui_queue.put({"type": "log", "value": f"{attempt_tag}FAIL: {image_path} :: {message}", "level": "error"})
                return False, message
            except (AuthenticationError, APIError, NetworkError) as exc:
                message = str(exc)
                ui_queue.put({"type": "log", "value": f"{attempt_tag}FAIL: {image_path} :: {message}", "level": "error"})
                return False, message
            except Exception as exc:
                message = f"An unexpected error occurred: {exc}"
                ui_queue.put({"type": "log", "value": f"{attempt_tag}FAIL: {image_path} :: {message}", "level": "error"})
                return False, message

        with open(summary_path, "w", encoding="utf-8") as summary_file:
            for index, image_path in enumerate(images):
                success, error_message = _process_single_image(image_path, index, summary_file)
                if not success:
                    failed_items.append((image_path, error_message, index))

                ui_queue.put({"type": "progress", "value": index + 1})

        if failed_items:
            ui_queue.put(
                {
                    "type": "log",
                    "value": f"Automatic retry triggered for {len(failed_items)} failed item(s)...",
                    "level": "warn",
                }
            )

            retry_failures: list[tuple[str, str, int]] = []
            with open(summary_path, "a", encoding="utf-8") as summary_file:
                for image_path, _error, original_index in failed_items:
                    success, error_message = _process_single_image(
                        image_path,
                        original_index,
                        summary_file,
                        attempt="retry",
                    )
                    if not success:
                        retry_failures.append((image_path, error_message, original_index))

            failed_items = retry_failures

        if failed_items:
            with open(log_path, "w", encoding="utf-8") as log_file:
                for path, error, _original_index in failed_items:
                    log_file.write(f"{path} :: {error}\n")
        elif os.path.exists(log_path):
            try:
                os.remove(log_path)
            except OSError:
                pass

        if "global_images_count" in state:
            previous = int(state["global_images_count"].get())
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
            f"Lifetime images processed: {new_total}"
        )
        ui_queue.put({"type": "log", "value": message.replace("\n", " | "), "level": "info"})

        auto_clear = bool(state.get("auto_clear_input") and state["auto_clear_input"].get())
        if auto_clear:
            ui_queue.put({"type": "log", "value": "Input path cleared per preference.", "level": "info"})
            ui_queue.put({"type": "status", "value": "Input cleared. Ready for a new folder."})
            ui_queue.put({"type": "clear_input"})

        if state["show_results_table"].get():
            ui_queue.put({"type": "done_with_results", "value": message, "results": results})
        else:
            ui_queue.put({"type": "done", "value": message})

        if failed_items:
            ui_queue.put(
                {
                    "type": "retry_failed",
                    "value": {
                        "count": len(failed_items),
                        "log_path": log_path,
                    },
                }
            )

        if state.get("auto_open_results") and state["auto_open_results"].get():
            ui_queue.put({"type": "open_folder", "value": session_path})

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
