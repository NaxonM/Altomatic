"""Text processing utilities for Altomatic."""

import re
import json

def extract_json_from_string(text: str) -> dict | None:
    """
    Finds and parses the first valid JSON object from a string.
    Handles JSON embedded in Markdown code blocks.
    """
    if not text:
        return None

    # Pattern to find JSON within ```json ... ``` or ``` ... ```
    pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(pattern, text, re.DOTALL)

    json_str = ""
    if match:
        json_str = match.group(1)
    else:
        # Fallback for plain JSON objects that might have surrounding text
        start_brace = text.find('{')
        end_brace = text.rfind('}')
        if start_brace != -1 and end_brace != -1 and start_brace < end_brace:
            json_str = text[start_brace:end_brace+1]
        else:
            return None

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None
