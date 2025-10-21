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
from src.altomatic.core.processor import process_images


class TestImageProcessor(unittest.TestCase):

    def setUp(self):
        """Set up a fresh state for each test."""
        self.state = {
            "llm_provider": MagicMock(get=lambda: "openai"),
            "openai_api_key": MagicMock(get=lambda: "fake_api_key"),
            "openrouter_api_key": MagicMock(get=lambda: ""),
            "input_path": MagicMock(get=lambda: "/fake/input"),
            "input_type": MagicMock(get=lambda: "Folder"),
            "include_subdirectories": MagicMock(get=lambda: False),
            "output_folder_option": MagicMock(get=lambda: "Same as input"),
            "custom_output_path": MagicMock(get=lambda: ""),
            "show_results_table": MagicMock(get=lambda: False),
            "total_tokens": MagicMock(get=lambda: 0, set=MagicMock()),
            "ui_queue": MagicMock(),
        }
        # Simplify the get method for MagicMock
        for key, mock_obj in self.state.items():
            if hasattr(mock_obj, "get"):
                mock_obj.get.return_value = mock_obj.get()

    @patch("src.altomatic.core.processor.os.path.exists")
    @patch("src.altomatic.core.processor.get_all_images")
    def test_no_images_found(self, mock_get_all_images, mock_exists):
        """Test that an error is queued if no images are found."""
        mock_exists.return_value = True
        mock_get_all_images.return_value = []
        process_images(self.state)
        self.state["ui_queue"].put.assert_called_with(
            {"type": "error", "title": "No Images", "value": "No valid image files found."}
        )

    @patch("src.altomatic.core.processor.os.path.exists")
    @patch("src.altomatic.core.processor.get_all_images")
    @patch("src.altomatic.core.processor.describe_image")
    @patch("src.altomatic.core.processor.shutil.copy")
    @patch("src.altomatic.core.processor.os.makedirs")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_successful_processing(
        self,
        mock_open,
        mock_makedirs,
        mock_copy,
        mock_describe_image,
        mock_get_all_images,
        mock_exists,
    ):
        """Test the full processing pipeline for a successful run."""
        mock_exists.return_value = True
        mock_get_all_images.return_value = ["/fake/input/image1.jpg"]
        mock_describe_image.return_value = {
            "name": "A sunny day",
            "alt": "A picture of a sunny day.",
        }
        process_images(self.state)
        mock_describe_image.assert_called_once()
        mock_copy.assert_called_once()
        self.assertIn(
            unittest.mock.call().write("[Original: image1.jpg]\n"), mock_open.mock_calls
        )

    @patch("src.altomatic.core.processor.os.path.exists")
    def test_input_path_does_not_exist(self, mock_exists):
        """Test error handling when the input path is invalid."""
        mock_exists.return_value = False
        process_images(self.state)
        self.state["ui_queue"].put.assert_called_with(
            {"type": "error", "title": "Invalid Input", "value": "Input path does not exist."}
        )

    @patch("src.altomatic.core.processor.os.path.exists")
    @patch("src.altomatic.core.processor.get_all_images")
    @patch("src.altomatic.core.processor.describe_image")
    def test_api_error_handling(
        self, mock_describe_image, mock_get_all_images, mock_exists
    ):
        """Test that API errors are caught and logged."""
        from src.altomatic.services.providers.exceptions import APIError

        mock_exists.return_value = True
        mock_get_all_images.return_value = ["/fake/input/image1.jpg"]
        mock_describe_image.side_effect = APIError("Model not found")
        with patch("builtins.open", unittest.mock.mock_open()):
            process_images(self.state)
        self.state["ui_queue"].put.assert_any_call(
            {
                "type": "log",
                "value": "FAIL: /fake/input/image1.jpg :: Model not found",
                "level": "error",
            }
        )

    def test_missing_api_key(self):
        """Test that the function exits if the API key is not set."""
        self.state["openai_api_key"].get.return_value = " "
        process_images(self.state)
        self.state["ui_queue"].put.assert_called_with(
            {
                "type": "error",
                "title": "Missing API Key",
                "value": "Please enter your OpenAI API key in the Settings tab.",
            }
        )


if __name__ == "__main__":
    unittest.main()
