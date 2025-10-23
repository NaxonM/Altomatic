import tkinter as tk
import unittest
from unittest.mock import MagicMock

from altomatic.models import AppState

class TestAppState(unittest.TestCase):
    def test_app_state_initialization(self):
        """Test that the AppState dataclass can be initialized correctly."""
        root = MagicMock()
        menubar = MagicMock()
        with unittest.mock.patch('tkinter.StringVar'), \
             unittest.mock.patch('tkinter.BooleanVar'), \
             unittest.mock.patch('tkinter.IntVar'):
            state = AppState(
                root=root,
                menubar=menubar,
                input_type=tk.StringVar(value="Folder"),
                input_path=tk.StringVar(value=""),
                recursive_search=tk.BooleanVar(value=False),
                show_results_table=tk.BooleanVar(value=True),
                custom_output_path=tk.StringVar(value=""),
                output_folder_option=tk.StringVar(value="Same as input"),
                openai_api_key=tk.StringVar(value=""),
                openrouter_api_key=tk.StringVar(value=""),
                proxy_enabled=tk.BooleanVar(value=True),
                proxy_override=tk.StringVar(value=""),
                filename_language=tk.StringVar(value="English"),
                alttext_language=tk.StringVar(value="English"),
                name_detail_level=tk.StringVar(value="Detailed"),
                vision_detail=tk.StringVar(value="auto"),
                ocr_enabled=tk.BooleanVar(value=False),
                tesseract_path=tk.StringVar(value=""),
                ocr_language=tk.StringVar(value="eng"),
                ui_theme=tk.StringVar(value="Arctic Light"),
                openai_model=tk.StringVar(value="gpt-5-nano"),
                openrouter_model=tk.StringVar(value="mistralai/mistral-small-3.2-24b-instruct:free"),
                llm_provider=tk.StringVar(value="openai"),
                llm_model=tk.StringVar(value="gpt-5-nano"),
                prompt_key=tk.StringVar(value="default"),
                context_text=tk.StringVar(value=""),
                status_var=tk.StringVar(value="Ready"),
                image_count=tk.StringVar(value=""),
                total_tokens=tk.IntVar(value=0),
                token_lock=MagicMock(),
                logs=[],
                prompts={},
                prompt_names=[],
                temp_drop_folder=None,
                provider_model_map={},
                _proxy_last_settings=None,
            )
            self.assertIsInstance(state, AppState)
            state.input_type.get.return_value = "Folder"
            self.assertEqual(state.input_type.get(), "Folder")
            state.llm_provider.get.return_value = "openai"
            self.assertEqual(state.llm_provider.get(), "openai")

if __name__ == "__main__":
    unittest.main()
