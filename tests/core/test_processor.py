"""Unit tests for the processor module."""

import os
import queue
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Mock UI modules before they are imported by the application code
sys.modules["tkinter"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()
sys.modules["tkinterdnd2"] = MagicMock()
sys.modules["pyperclip"] = MagicMock()


from src.altomatic.core.processor import process_images
from PIL import UnidentifiedImageError


class TestProcessor(unittest.TestCase):
    """Test cases for the image processor."""

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.output_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def create_dummy_image(self, filename="test_image.png"):
        """Creates a dummy image file."""
        path = os.path.join(self.test_dir, filename)
        with open(path, "w") as f:
            f.write("dummy image data")
        return path

    def get_default_state(self):
        """Returns a default state dictionary for testing."""
        state = {
            "ui_queue": queue.Queue(),
            "llm_provider": MagicMock(get=MagicMock(return_value="openai")),
            "openai_api_key": MagicMock(get=MagicMock(return_value="test_api_key")),
            "input_path": MagicMock(get=MagicMock(return_value=self.test_dir)),
            "output_folder_option": MagicMock(get=MagicMock(return_value="Custom")),
            "custom_output_path": MagicMock(get=MagicMock(return_value=self.output_dir)),
            "input_type": MagicMock(get=MagicMock(return_value="Directory")),
            "include_subdirectories": MagicMock(get=MagicMock(return_value=False)),
            "total_tokens": MagicMock(get=MagicMock(return_value=0), set=MagicMock()),
            "show_results_table": MagicMock(get=MagicMock(return_value=False)),
        }
        state.setdefault("global_images_count", MagicMock(get=MagicMock(return_value=0), set=MagicMock()))
        return state

    @patch("src.altomatic.core.processor.describe_image")
    @patch("src.altomatic.utils.images.get_all_images")
    def test_process_images_success(self, mock_get_all_images, mock_describe_image):
        """Test successful image processing."""
        image_path = self.create_dummy_image()
        mock_get_all_images.return_value = [image_path]
        mock_describe_image.return_value = {"name": "test", "alt": "alt text"}
        state = self.get_default_state()

        process_images(state)

        # Check that the output file was created
        session_dirs = os.listdir(self.output_dir)
        self.assertEqual(len(session_dirs), 1)
        renamed_images_dir = os.path.join(self.output_dir, session_dirs[0], "renamed_images")
        output_files = os.listdir(renamed_images_dir)
        self.assertEqual(len(output_files), 1)
        self.assertTrue(output_files[0].startswith("test"))

    def test_process_images_no_api_key(self):
        """Test processing with a missing API key."""
        state = self.get_default_state()
        state["openai_api_key"].get.return_value = ""

        process_images(state)

        # Check for the error message in the queue
        error_message = state["ui_queue"].get()
        self.assertEqual(error_message["type"], "error")
        self.assertEqual(error_message["title"], "Missing API Key")

    def test_process_images_invalid_input_path(self):
        """Test processing with an invalid input path."""
        state = self.get_default_state()
        state["input_path"].get.return_value = "non_existent_path"

        process_images(state)

        # Check for the error message in the queue
        error_message = state["ui_queue"].get()
        self.assertEqual(error_message["type"], "error")
        self.assertEqual(error_message["title"], "Invalid Input")

    @patch("src.altomatic.utils.images.get_all_images", return_value=[])
    def test_process_images_no_images_found(self, mock_get_all_images):
        """Test processing when no images are found."""
        state = self.get_default_state()
        process_images(state)

        # Check for the error message in the queue
        error_message = state["ui_queue"].get()
        self.assertEqual(error_message["type"], "error")
        self.assertEqual(error_message["title"], "No Images")

    @patch("src.altomatic.core.processor.describe_image", side_effect=UnidentifiedImageError)
    @patch("src.altomatic.utils.images.get_all_images")
    def test_process_images_unidentified_image_error(self, mock_get_all_images, mock_describe_image):
        """Test that UnidentifiedImageError is handled gracefully."""
        image_path = self.create_dummy_image()
        mock_get_all_images.return_value = [image_path]
        state = self.get_default_state()

        process_images(state)

        # Check that the log file was created with the correct error message
        session_dirs = os.listdir(self.output_dir)
        self.assertEqual(len(session_dirs), 1)
        log_path = os.path.join(self.output_dir, session_dirs[0], "failed.log")
        self.assertTrue(os.path.exists(log_path))
        with open(log_path, "r") as f:
            log_content = f.read()
        self.assertIn("Unsupported or corrupted image format", log_content)


if __name__ == "__main__":
    unittest.main()
