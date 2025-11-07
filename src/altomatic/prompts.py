"""Prompt management utilities with metadata support."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


DATA_DIR = Path(__file__).resolve().parent / "data"
PROMPTS_PATH = DATA_DIR / "prompts.json"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


DEFAULT_PROMPTS: Dict[str, dict] = {
    "default": {
        "label": "Balanced descriptive",
        "template": (
            "You are Altomatic, an accessibility and SEO expert tasked with returning a lowercase, "
            "hyphenated image file name followed by concise, context-aware alt text. The file name "
            "must describe the subject in three to five keywords, use hyphens instead of spaces or "
            "underscores, stay in lowercase, and avoid filler words. The alt text should be a single "
            "sentence under 125 characters that explains the visible content and its context without "
            "starting with phrases like 'image of'. Incorporate supplied context naturally and include "
            "relevant keywords only when they make sense."
        ),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    },
    "concise": {
        "label": "Concise captions",
        "template": (
            "You are Altomatic, crafting streamlined image filenames and alt text for fast scanning. "
            "Generate a lowercase, hyphen-separated file name that captures the subject in up to four "
            "keywords. Then provide alt text in one sentence (≤125 characters) that highlights the "
            "subject and the single most important detail, keeping the wording natural, specific, and "
            "free of redundant openings like 'photo of'."
        ),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    },
    "product": {
        "label": "Product focus",
        "template": (
            "You are Altomatic, preparing ecommerce-ready image filenames and alt text. Produce a "
            "lowercase, hyphenated file name that emphasizes product type, key attributes, and a "
            "relevant keyword if appropriate. For the alt text, write one sentence under 125 characters "
            "that clearly states the product, standout materials or finishes, notable colors, and any "
            "usage context that matters to shoppers, avoiding filler language."
        ),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    },
}


def _ensure_prompt_entry(key: str, entry: dict) -> dict:
    entry = dict(entry)
    if "label" not in entry:
        entry["label"] = key
    if "template" not in entry:
        entry["template"] = ""
    created = entry.get("created_at")
    if not created:
        created = _now_iso()
        entry["created_at"] = created
    updated = entry.get("updated_at")
    if not updated:
        entry["updated_at"] = created
    return entry


def _ensure_prompts_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PROMPTS_PATH.exists():
        PROMPTS_PATH.write_text(
            json.dumps(DEFAULT_PROMPTS, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def load_prompts() -> Dict[str, dict]:
    _ensure_prompts_file()
    try:
        with PROMPTS_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("Invalid prompts structure")
        normalized = {key: _ensure_prompt_entry(key, entry) for key, entry in data.items()}
        return normalized
    except Exception:
        return {key: dict(value) for key, value in DEFAULT_PROMPTS.items()}


def save_prompts(prompts: Dict[str, dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    normalized = {key: _ensure_prompt_entry(key, value) for key, value in prompts.items()}
    PROMPTS_PATH.write_text(
        json.dumps(normalized, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_prompt_template(key: str) -> str:
    prompts = load_prompts()
    entry = prompts.get(key) or prompts.get("default") or next(iter(prompts.values()))
    return entry.get("template", "")


def get_prompt_label(key: str) -> str:
    prompts = load_prompts()
    entry = prompts.get(key) or prompts.get("default") or next(iter(prompts.values()))
    return entry.get("label", key)
