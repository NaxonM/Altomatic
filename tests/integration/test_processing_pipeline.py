"""Integration tests for the processing pipeline."""

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


class TestProcessingPipeline(unittest.TestCase):
    """Test cases for the processing pipeline."""

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
            "llm_model": MagicMock(get=MagicMock(return_value="gpt-4-vision-preview")),
            "vision_detail": MagicMock(get=MagicMock(return_value="high")),
            "monitor": MagicMock(),
            "logs": [],
        }
        state.setdefault("global_images_count", MagicMock(get=MagicMock(return_value=0), set=MagicMock()))
        return state

    @patch("src.altomatic.core.processor.describe_image")
    @patch("src.altomatic.utils.images.get_all_images")
    def test_pipeline_with_mock_provider(self, mock_get_all_images, mock_describe_image):
        """Test the full pipeline with a mock AI provider."""
        image_path = self.create_dummy_image()
        mock_get_all_images.return_value = [image_path]
        mock_describe_image.return_value = {"name": "test-integration", "alt": "alt text integration"}
        state = self.get_default_state()

        process_images(state)

        # Check that the output file was created with the correct content
        session_dirs = os.listdir(self.output_dir)
        self.assertEqual(len(session_dirs), 1)
        session_dir = os.path.join(self.output_dir, session_dirs[0])
        renamed_images_dir = os.path.join(session_dir, "renamed_images")
        output_files = os.listdir(renamed_images_dir)
        self.assertEqual(len(output_files), 1)
        self.assertTrue(output_files[0].startswith("test-integration"))

        # Find the summary file
        summary_file = next((f for f in os.listdir(session_dir) if f.endswith(".txt")), None)
        self.assertIsNotNone(summary_file)
        summary_path = os.path.join(session_dir, summary_file)
        with open(summary_path, "r") as f:
            summary_content = f.read()
        self.assertIn("Name: test-integration", summary_content)
        self.assertIn("Alt: alt text integration", summary_content)


if __name__ == "__main__":
    unittest.main()
