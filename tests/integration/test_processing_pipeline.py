import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import tempfile
import shutil

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


class TestProcessingPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.input_dir)
        os.makedirs(self.output_dir)

        # Create dummy image files
        for i in range(3):
            with open(os.path.join(self.input_dir, f"image{i}.png"), "w") as f:
                f.write("dummy image data")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("src.altomatic.core.processor.describe_image")
    def test_pipeline_creates_files_and_folders(self, mock_describe_image):
        mock_describe_image.return_value = {
            "name": "test name",
            "alt": "test alt text",
        }

        state = {
            "llm_provider": MagicMock(get=lambda: "openai"),
            "openai_api_key": MagicMock(get=lambda: "fake_key"),
            "openrouter_api_key": MagicMock(get=lambda: ""),
            "input_path": MagicMock(get=lambda: self.input_dir),
            "output_folder_option": MagicMock(get=lambda: "Custom"),
            "custom_output_path": MagicMock(get=lambda: self.output_dir),
            "input_type": MagicMock(get=lambda: "Folder"),
            "include_subdirectories": MagicMock(get=lambda: False),
            "show_results_table": MagicMock(get=lambda: False),
            "total_tokens": MagicMock(get=lambda: 0, set=MagicMock()),
            "ui_queue": MagicMock(),
        }

        # Simplify the get method for MagicMock
        for key, mock_obj in state.items():
            if hasattr(mock_obj, "get"):
                mock_obj.get.return_value = mock_obj.get()

        process_images(state)

        # Verify that session folder, renamed_images folder, and summary file were created
        session_folders = [
            d
            for d in os.listdir(self.output_dir)
            if os.path.isdir(os.path.join(self.output_dir, d))
        ]
        self.assertEqual(len(session_folders), 1)
        session_path = os.path.join(self.output_dir, session_folders[0])
        self.assertTrue(os.path.isdir(os.path.join(session_path, "renamed_images")))
        self.assertTrue(any(f.endswith(".txt") for f in os.listdir(session_path)))

        # Verify that images were "renamed" (copied)
        renamed_images_path = os.path.join(session_path, "renamed_images")
        self.assertEqual(len(os.listdir(renamed_images_path)), 3)
        self.assertTrue(
            os.path.exists(os.path.join(renamed_images_path, "test-name.png"))
        )


if __name__ == "__main__":
    unittest.main()
