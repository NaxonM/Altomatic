"""Tests for OCR functionality."""

import sys
from unittest.mock import patch

import pytest

from altomatic.services.providers.exceptions import OCRError
from altomatic.utils.images import extract_text_from_image


def test_ocr_raises_exception_when_pytesseract_is_not_installed():
    """Verify that OCRError is raised when pytesseract is not installed."""
    with patch.dict('sys.modules', {'pytesseract': None}):
        with pytest.raises(OCRError, match="Pytesseract library not found"):
            extract_text_from_image("dummy_path")
