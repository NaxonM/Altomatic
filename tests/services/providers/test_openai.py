"""Unit tests for the OpenAI provider."""

import json
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock UI modules before they are imported by the application code
sys.modules["tkinter"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()
sys.modules["tkinterdnd2"] = MagicMock()
sys.modules["pyperclip"] = MagicMock()

from src.altomatic.services.providers.openai import OpenAIProvider
from src.altomatic.services.providers.exceptions import APIError, AuthenticationError


class TestOpenAIProvider(unittest.TestCase):
    """Test cases for the OpenAI provider."""

    def setUp(self):
        """Set up the test case."""
        self.provider = OpenAIProvider()
        self.state = {
            "openai_api_key": MagicMock(get=MagicMock(return_value="test_api_key")),
            "llm_model": MagicMock(get=MagicMock(return_value="gpt-4-vision-preview")),
            "vision_detail": MagicMock(get=MagicMock(return_value="high")),
            "total_tokens": MagicMock(get=MagicMock(return_value=0), set=MagicMock()),
            "monitor": MagicMock(),
            "logs": [],
        }

    @patch("src.altomatic.services.providers.openai.OpenAI")
    def test_describe_image_success(self, mock_openai):
        """Test successful image description."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({"name": "test", "alt": "alt text"})
        mock_response.usage.total_tokens = 100
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        result = self.provider.describe_image("encoded_image", "prompt", self.state)

        self.assertEqual(result, {"name": "test", "alt": "alt text"})
        self.state["total_tokens"].set.assert_called_with(100)

    @patch("src.altomatic.services.providers.openai.OpenAI")
    def test_describe_image_api_error(self, mock_openai):
        """Test API error during image description."""
        mock_openai.return_value.chat.completions.create.side_effect = APIError("API Error")

        with self.assertRaises(APIError):
            self.provider.describe_image("encoded_image", "prompt", self.state)

    @patch("src.altomatic.services.providers.openai.OpenAI")
    def test_describe_image_auth_error(self, mock_openai):
        """Test authentication error during image description."""
        # We need to import the openai exception here, as it's not available at the top level
        from openai import AuthenticationError as OpenAIAuthError

        mock_openai.return_value.chat.completions.create.side_effect = OpenAIAuthError(
            "Auth Error", response=MagicMock(), body=None
        )

        with self.assertRaises(AuthenticationError):
            self.provider.describe_image("encoded_image", "prompt", self.state)

    def test_describe_image_no_openai_package(self):
        """Test that an error is raised if the openai package is not installed."""
        with patch("src.altomatic.services.providers.openai.OpenAI", None):
            with self.assertRaises(APIError) as context:
                self.provider.describe_image("encoded_image", "prompt", self.state)
            self.assertIn("OpenAI Python package is not available", str(context.exception))


if __name__ == "__main__":
    unittest.main()
