"""Utility helpers."""

from .images import (
    PreprocessedImage,
    extract_text_from_image,
    generate_output_filename,
    generate_session_folder_name,
    generate_short_id,
    get_all_images,
    get_image_count_in_folder,
    find_tesseract_executable,
    image_to_base64,
    preprocess_image_for_llm,
    slugify,
)
from .proxy import (
    configure_global_proxy,
    detect_system_proxies,
    get_requests_proxies,
    reload_system_proxies,
    set_proxy_preferences,
)

__all__ = [
    "PreprocessedImage",
    "configure_global_proxy",
    "detect_system_proxies",
    "get_requests_proxies",
    "reload_system_proxies",
    "set_proxy_preferences",
    "generate_short_id",
    "image_to_base64",
    "preprocess_image_for_llm",
    "generate_session_folder_name",
    "generate_output_filename",
    "get_image_count_in_folder",
    "get_all_images",
    "slugify",
    "extract_text_from_image",
    "find_tesseract_executable",
]
