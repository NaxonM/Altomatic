"""Image utilities for Altomatic."""

from __future__ import annotations

import base64
import math
import os
import random
import string
import sys
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from shutil import which
from typing import Literal

from PIL import Image, ImageOps


ImageFormat = Literal["JPEG", "PNG"]


@dataclass(slots=True)
class PreprocessedImage:
    data_url: str
    mime_type: str
    original_size_bytes: int
    processed_size_bytes: int
    original_dimensions: tuple[int, int]
    processed_dimensions: tuple[int, int]
    format: ImageFormat
    quality: int | None
    resized: bool


def generate_short_id(length: int = 4) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def image_to_base64(path: str) -> str:
    extension = os.path.splitext(path)[1].lower().replace(".", "")
    if extension == "jpg":
        extension = "jpeg"
    with open(path, "rb") as fh:
        encoded = base64.b64encode(fh.read()).decode("utf-8")
    return f"data:image/{extension};base64,{encoded}"


def _encode_image_bytes(image_bytes: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def preprocess_image_for_llm(
    path: str,
    *,
    max_edge: int = 1600,
    max_megapixels: float = 1.3,
    target_size_kb: int = 900,
    jpeg_quality: int = 90,
    min_quality: int = 75,
) -> PreprocessedImage:
    """Compress and resize an image while retaining text legibility.

    The function favours JPEG output for opaque images and falls back to PNG
    for images with transparency. It iteratively scales quality (and if
    required, resolution) until the encoded payload is within the requested
    bounds.
    """

    original_size = os.path.getsize(path)
    max_pixels = int(max_megapixels * 1_000_000)

    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        original_width, original_height = img.size

        has_alpha = "A" in img.getbands()
        target_format: ImageFormat = "PNG" if has_alpha else "JPEG"
        mime_type = "image/png" if target_format == "PNG" else "image/jpeg"

        current = img
        resized = False

        def _resize_if_needed(image: Image.Image) -> tuple[Image.Image, bool]:
            width, height = image.size
            factor = 1.0
            if max(width, height) > max_edge:
                factor = min(factor, max_edge / max(width, height))
            total_pixels = width * height
            if total_pixels > max_pixels:
                factor = min(factor, math.sqrt(max_pixels / total_pixels))
            if factor < 1.0:
                new_size = (max(1, int(width * factor)), max(1, int(height * factor)))
                return image.resize(new_size, Image.Resampling.LANCZOS), True
            return image, False

        current, resized_flag = _resize_if_needed(current)
        resized = resized or resized_flag

        buffer = BytesIO()
        quality = jpeg_quality

        def _save(image: Image.Image, *, q: int | None) -> bytes:
            buffer.seek(0)
            buffer.truncate(0)
            save_kwargs: dict[str, object] = {"optimize": True}
            if target_format == "JPEG":
                converted = image.convert("RGB")
                save_kwargs["quality"] = q if q is not None else jpeg_quality
                save_kwargs["progressive"] = True
                save_kwargs["subsampling"] = 1
                converted.save(buffer, target_format, **save_kwargs)
            else:
                converted = image.convert("RGBA") if has_alpha else image.convert("RGB")
                save_kwargs["compress_level"] = 7
                converted.save(buffer, target_format, **save_kwargs)
            return buffer.getvalue()

        image_bytes = _save(current, q=quality if target_format == "JPEG" else None)
        size_kb = len(image_bytes) / 1024

        while size_kb > target_size_kb:
            if target_format == "JPEG" and quality > min_quality:
                quality = max(min_quality, quality - 5)
                image_bytes = _save(current, q=quality)
            else:
                width, height = current.size
                if max(width, height) <= 720:
                    break
                new_width = max(1, int(width * 0.9))
                new_height = max(1, int(height * 0.9))
                current = current.resize((new_width, new_height), Image.Resampling.LANCZOS)
                resized = True
                image_bytes = _save(current, q=quality if target_format == "JPEG" else None)
            size_kb = len(image_bytes) / 1024

        processed_width, processed_height = current.size

        data_url = _encode_image_bytes(image_bytes, mime_type)

        result = PreprocessedImage(
            data_url=data_url,
            mime_type=mime_type,
            original_size_bytes=original_size,
            processed_size_bytes=len(image_bytes),
            original_dimensions=(original_width, original_height),
            processed_dimensions=(processed_width, processed_height),
            format=target_format,
            quality=quality if target_format == "JPEG" else None,
            resized=resized,
        )

        if current is not img:
            current.close()

        return result


def _timestamp_prefix() -> str:
    return datetime.now().strftime("%Y-%m-%d-%H-%M")


def generate_session_folder_name() -> str:
    return f"session-{_timestamp_prefix()}-{generate_short_id()}"


def generate_output_filename() -> str:
    return f"altomatic-output-{_timestamp_prefix()}-{generate_short_id()}.txt"


def get_image_count_in_folder(folder: str) -> int:
    if not os.path.isdir(folder):
        return 0
    return len([
        file
        for file in os.listdir(folder)
        if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ])


def get_all_images(folder: str) -> list[str]:
    if not os.path.isdir(folder):
        return []
    return [
        os.path.join(folder, file)
        for file in os.listdir(folder)
        if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]


def get_output_folder(state) -> str:
    preset = state["output_folder_option"].get()
    input_path = state["input_path"].get()
    input_type = state["input_type"].get()

    if preset == "Same as input":
        if input_type == "File":
            return os.path.dirname(input_path)
        return input_path
    if preset == "Desktop":
        return os.path.join(os.path.expanduser("~"), "Desktop")
    if preset == "Pictures":
        return os.path.join(os.path.expanduser("~"), "Pictures")
    if preset == "Custom":
        return state["custom_output_path"].get()
    return os.getcwd()


def slugify(text: str) -> str:
    import re

    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text


def find_tesseract_executable(preferred_path: str = "") -> str | None:
    if preferred_path:
        candidate = Path(preferred_path).expanduser()
        if candidate.is_file():
            return str(candidate)
        if candidate.is_dir():
            exe_path = candidate / "tesseract.exe"
            if exe_path.is_file():
                return str(exe_path)

    env_path = which("tesseract")
    if env_path:
        return env_path

    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        bundle_candidate = Path(bundle_dir) / "tesseract.exe"
        if bundle_candidate.is_file():
            return str(bundle_candidate)

    if os.name == "nt":
        search_roots = [
            os.environ.get("TESSERACT_DIR"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Tesseract-OCR"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Tesseract-OCR"),
        ]
        for root in search_roots:
            if not root:
                continue
            exe_path = Path(root) / "tesseract.exe"
            if exe_path.is_file():
                return str(exe_path)

    return None


def extract_text_from_image(image_path: str, tesseract_path: str = "", lang: str = "eng") -> str:
    try:
        import pytesseract
    except Exception as exc:
        return f"⚠️ OCR failed: {exc}"

    not_found_error = getattr(pytesseract, "TesseractNotFoundError", RuntimeError)

    try:
        resolved_path = find_tesseract_executable(tesseract_path)
        if resolved_path:
            pytesseract.pytesseract.tesseract_cmd = resolved_path
        elif tesseract_path:
            return "⚠️ OCR unavailable: Tesseract executable not found."
        with Image.open(image_path) as image:
            text = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
    except not_found_error:
        return "⚠️ OCR unavailable: Tesseract executable not found. Configure the path in Settings."
    except Exception as exc:
        return f"⚠️ OCR failed: {exc}"
