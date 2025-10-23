"""Text processing utilities for Altomatic."""

import re
import json


def extract_json_from_string(text: str) -> dict | None:
    """
    Finds and parses the first valid JSON object from a string.
    Handles JSON embedded in Markdown code blocks and nested structures.
    """
    if not text:
        return None

    # Pattern to find JSON within ```json ... ``` or ``` ... ```
    pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        json_str = match.group(1)
        try:
            result = json.loads(json_str)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            # Fallback to brace counting if markdown content is invalid
            pass

    # Robust fallback for plain JSON objects with brace counting
    # This will find the first complete and valid JSON object
    for start_index in [m.start() for m in re.finditer(r"{", text)]:
        brace_count = 0
        for i, char in enumerate(text[start_index:]):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1

            if brace_count == 0:
                end_index = start_index + i + 1
                potential_json = text[start_index:end_index]
                try:
                    result = json.loads(potential_json)
                    if isinstance(result, dict):
                        return result
                except json.JSONDecodeError:
                    # This substring was not valid JSON, so we continue searching
                    # from the same start_index to find a larger balanced object.
                    pass

    return None
