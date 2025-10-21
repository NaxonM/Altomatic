import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock UI modules before any application code is imported to prevent fatal errors
# in the headless environment.
MOCK_MODULES = [
    "tkinter",
    "tkinter.ttk",
    "tkinter.font",
    "tkinter.messagebox",
    "pyperclip",
    "tkinterdnd2",
    "ttkthemes",
]
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()
from src.altomatic.services.providers.openai import OpenAIProvider
from src.altomatic.services.providers.exceptions import APIError, AuthenticationError


class TestOpenAIProvider(unittest.TestCase):

    def setUp(self):
        self.state = {
            "openai_api_key": "fake_api_key",
            "llm_model": "gpt-4-vision-preview",
            "prompt_key": "default",
            "prompts": {
                "default": {
                    "template": "Describe this image.",
                    "vision_detail": "auto",
                }
            },
            "context_text": "",
            "ui_queue": MagicMock(),
        }

    @patch("src.altomatic.services.providers.openai.OpenAI")
    def test_describe_success(self, mock_openai_class):
        """Test a successful image description call."""
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"name": "test", "alt": "test"}'
        mock_response.usage.total_tokens = 100
        mock_openai_instance.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(self.state)
        result = provider.describe("fake_image_path.jpg")

        self.assertEqual(result, {"name": "test", "alt": "test"})
        self.state["ui_queue"].put.assert_any_call(
            {"type": "token_update", "value": 100}
        )

    @patch("src.altomatic.services.providers.openai.OpenAI")
    def test_authentication_error(self, mock_openai_class):
        """Test that AuthenticationError is raised for API key issues."""
        from openai import AuthenticationError as OpenAIAuthError

        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.side_effect = OpenAIAuthError(
            "Invalid API key", response=MagicMock(), body=None
        )

        provider = OpenAIProvider(self.state)
        with self.assertRaises(AuthenticationError):
            provider.describe("fake_image_path.jpg")

    @patch("src.altomatic.services.providers.openai.OpenAI")
    def test_api_error(self, mock_openai_class):
        """Test that APIError is raised for general API issues."""
        from openai import APIError as OpenAIAPIError

        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.side_effect = OpenAIAPIError(
            "Model not found", response=MagicMock(), body=None
        )

        provider = OpenAIProvider(self.state)
        with self.assertRaises(APIError):
            provider.describe("fake_image_path.jpg")

    @patch("src.altomatic.services.providers.openai.OpenAI")
    def test_invalid_json_response(self, mock_openai_class):
        """Test handling of responses that are not valid JSON."""
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is not JSON."
        mock_openai_instance.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(self.state)
        with self.assertRaises(APIError):
            provider.describe("fake_image_path.jpg")


if __name__ == "__main__":
    unittest.main()
