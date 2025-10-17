
"""Image processing pipeline."""

from __future__ import annotations

import os
import shutil
from typing import Dict, Any, List, TYPE_CHECKING

from PIL import UnidentifiedImageError

from ..models import DEFAULT_PROVIDER, get_provider_label
from ..services.ai import describe_image
from ..services.providers.exceptions import AuthenticationError, APIError, NetworkError
from ..utils.images import (
    SUPPORTED_EXTENSIONS,
    generate_output_filename,
    generate_session_folder_name,
    get_all_images,
    slugify,
)

if TYPE_CHECKING:
    from src.app.viewmodels.main_viewmodel import MainViewModel

from typing import Callable

def process_images(main_vm: MainViewModel, progress_callback: Callable[[int], None]) -> tuple[List[Dict[str, Any]], str]:
    """The core image processing pipeline."""
    results: List[Dict[str, Any]] = []
    session_path = ""

    try:
        provider = main_vm.prompts_model_vm.provider_vm.llm_provider
        if provider not in {"openai", "openrouter"}:
            provider = DEFAULT_PROVIDER

        api_key = (
            main_vm.prompts_model_vm.provider_vm.openrouter_api_key
            if provider == "openrouter"
            else main_vm.prompts_model_vm.provider_vm.openai_api_key
        )
        if not api_key:
            main_vm.log_vm.add_log(f"Please enter your {get_provider_label(provider)} API key.", "error")
            return results

        sources = main_vm.input_vm.selected_sources()
        if not sources:
            main_vm.log_vm.add_log("Select at least one image or folder to begin.", "error")
            return results
        missing = [path for path in sources if not os.path.exists(path)]
        for path in missing:
            main_vm.log_vm.add_log(f"Skipping missing source: {path}", "warn")
        sources = [path for path in sources if os.path.exists(path)]
        if not sources:
            main_vm.log_vm.add_log("No valid sources remain after validation.", "error")
            return results

        base_output_folder = get_output_folder_from_vm(main_vm)
        if not os.access(base_output_folder, os.W_OK):
            main_vm.log_vm.add_log(f"Cannot write to the selected output directory: {base_output_folder}", "error")
            return results

        include_subdirectories = main_vm.input_vm.include_subdirectories
        images: list[str] = []
        for source in sources:
            if os.path.isdir(source):
                images.extend(get_all_images(source, include_subdirectories))
            elif os.path.isfile(source):
                if source.lower().endswith(SUPPORTED_EXTENSIONS):
                    images.append(source)
                else:
                    main_vm.log_vm.add_log(f"Ignoring unsupported file type: {source}", "warn")
            else:
                main_vm.log_vm.add_log(f"Unrecognised source: {source}", "warn")

        images = list(dict.fromkeys(images))

        if not images:
            main_vm.log_vm.add_log("No valid image files found.", "error")
            return results

        total_images = len(images)
        main_vm.log_vm.add_log(f"Found {total_images} images to process.", "info")
        main_vm.footer_vm.total_tokens = 0

        os.makedirs(base_output_folder, exist_ok=True)

        session_name = generate_session_folder_name()
        session_path = os.path.join(base_output_folder, session_name)
        os.makedirs(session_path, exist_ok=True)
        main_vm.log_vm.add_log(f"Session folder: {session_path}", "info")

        renamed_folder = os.path.join(session_path, "renamed_images")
        os.makedirs(renamed_folder, exist_ok=True)

        summary_path = os.path.join(session_path, generate_output_filename())
        log_path = os.path.join(session_path, "failed.log")

        failed_items: list[tuple[str, str]] = []

        with open(summary_path, "w", encoding="utf-8") as summary_file:
            for index, image_path in enumerate(images):
                try:
                    main_vm.log_vm.add_log(f"Analyzing {image_path}", "info")
                    result = describe_image_from_vm(main_vm, image_path)

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
                    summary_file.write(f"[Original: {os.path.basename(image_path)}]\\n")
                    summary_file.write(f"Name: {os.path.splitext(final_name)[0]}\\n")
                    summary_file.write(f"Alt: {result['alt']}\\n\\n")
                    main_vm.log_vm.add_log(f"-> {final_name}", "success")

                    results.append({
                        "original_path": image_path,
                        "original_filename": os.path.basename(image_path),
                        "new_filename": final_name,
                        "alt_text": result["alt"]
                    })

                except UnidentifiedImageError:
                    exc_message = "Unsupported or corrupted image format."
                    failed_items.append((image_path, exc_message))
                    main_vm.log_vm.add_log(f"FAIL: {image_path} :: {exc_message}", "error")
                except (AuthenticationError, APIError, NetworkError) as exc:
                    failed_items.append((image_path, str(exc)))
                    main_vm.log_vm.add_log(f"FAIL: {image_path} :: {exc}", "error")
                except Exception as exc:
                    failed_items.append((image_path, str(exc)))
                    main_vm.log_vm.add_log(f"FAIL: {image_path} :: An unexpected error occurred: {exc}", "error")

                progress_percentage = int(((index + 1) / total_images) * 100)
                progress_callback(progress_percentage)

        if failed_items:
            with open(log_path, "w", encoding="utf-8") as log_file:
                for path, error in failed_items:
                    log_file.write(f"{path} :: {error}\\n")
        elif os.path.exists(log_path):
            try:
                os.remove(log_path)
            except OSError:
                pass

        message = (
            f"Processed {len(images)} image(s).\\n"
            f"Session folder: {session_path}\\n"
            f"Output file: {os.path.basename(summary_path)}\\n\\n"
            f"Token usage this run: {main_vm.footer_vm.total_tokens}"
        )
        main_vm.log_vm.add_log(message.replace("\\n", " | "), "info")

    except Exception as exc:
        main_vm.log_vm.add_log(f"An unexpected error occurred: {exc}", "error")

    return results

def get_output_folder_from_vm(main_vm: MainViewModel) -> str:
    """Gets the output folder from the view model."""
    option = main_vm.workflow_vm.output_vm.output_folder_option
    if option == "Custom":
        return main_vm.workflow_vm.output_vm.custom_output_path
    elif option == "Pictures":
        return os.path.expanduser("~/Pictures")
    elif option == "Desktop":
        return os.path.expanduser("~/Desktop")
    else:  # Same as input
        sources = main_vm.input_vm.sources()
        if not sources:
            return os.getcwd()
        first = sources[0]
        if os.path.isfile(first):
            base = os.path.dirname(first)
            return base or os.getcwd()
        return first

def describe_image_from_vm(main_vm: MainViewModel, image_path: str) -> Dict[str, Any]:
    """Describes an image using the settings from the view model."""
    state = {
        "main_vm": main_vm,
        "log_vm": main_vm.log_vm,
        "footer_vm": main_vm.footer_vm,
        "llm_provider": main_vm.prompts_model_vm.provider_vm.llm_provider,
        "llm_model": main_vm.prompts_model_vm.provider_vm.model,
        "openai_api_key": main_vm.prompts_model_vm.provider_vm.openai_api_key,
        "openrouter_api_key": main_vm.prompts_model_vm.provider_vm.openrouter_api_key,
        "prompt_key": main_vm.prompts_model_vm.prompts_vm.selected_prompt,
        "context_text": main_vm.workflow_vm.context_vm.context_text,
        "filename_language": main_vm.workflow_vm.processing_vm.filename_language,
        "alttext_language": main_vm.workflow_vm.processing_vm.alttext_language,
        "name_detail_level": main_vm.workflow_vm.processing_vm.name_detail_level,
        "vision_detail": main_vm.workflow_vm.processing_vm.vision_detail,
        "ocr_enabled": main_vm.workflow_vm.processing_vm.ocr_enabled,
        "tesseract_path": main_vm.workflow_vm.processing_vm.tesseract_path,
        "ocr_language": main_vm.workflow_vm.processing_vm.ocr_language,
        "proxy_enabled": main_vm.advanced_vm.network_vm.proxy_enabled,
        "proxy_override": main_vm.advanced_vm.network_vm.proxy_override,
    }

    return describe_image(state, image_path)
