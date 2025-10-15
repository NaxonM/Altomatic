
from PySide6.QtCore import Signal, Property, bool, str
from .base_viewmodel import BaseViewModel
import os

class InputViewModel(BaseViewModel):
    """
    ViewModel for the input section.
    """
    input_type_changed = Signal(str)
    input_path_changed = Signal(str)
    include_subdirectories_changed = Signal(bool)
    image_count_text_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._input_type = "Folder"
        self._input_path = ""
        self._include_subdirectories = False
        self._image_count_text = ""

    # --- Properties ---
    @Property(str, notify=input_type_changed)
    def input_type(self):
        return self._input_type

    @input_type.setter
    def input_type(self, value):
        if self._input_type != value:
            self._input_type = value
            self.input_type_changed.emit(value)
            self._update_image_count()

    @Property(str, notify=input_path_changed)
    def input_path(self):
        return self._input_path

    @input_path.setter
    def input_path(self, value):
        if self._input_path != value:
            self._input_path = value
            self.input_path_changed.emit(value)
            self._update_image_count()

    @Property(bool, notify=include_subdirectories_changed)
    def include_subdirectories(self):
        return self._include_subdirectories

    @include_subdirectories.setter
    def include_subdirectories(self, value):
        if self._include_subdirectories != value:
            self._include_subdirectories = value
            self.include_subdirectories_changed.emit(value)
            self._update_image_count()

    @Property(str, notify=image_count_text_changed)
    def image_count_text(self):
        return self._image_count_text

    def _set_image_count_text(self, value):
        if self._image_count_text != value:
            self._image_count_text = value
            self.image_count_text_changed.emit(value)

    # --- Private Methods ---
    def _get_image_count_in_folder(self, folder_path: str, recursive: bool) -> int:
        """Counts image files in a given folder."""
        if not os.path.isdir(folder_path):
            return 0

        count = 0
        image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif"}

        if recursive:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if os.path.splitext(file)[1].lower() in image_extensions:
                        count += 1
        else:
            for item in os.listdir(folder_path):
                if os.path.isfile(os.path.join(folder_path, item)):
                    if os.path.splitext(item)[1].lower() in image_extensions:
                        count += 1
        return count

    def _update_image_count(self):
        """Updates the image count based on the current path and settings."""
        if not self._input_path:
            self._set_image_count_text("")
            return

        count = 0
        if self._input_type == "Folder":
            if os.path.isdir(self._input_path):
                 count = self._get_image_count_in_folder(self._input_path, self._include_subdirectories)
        else: # File
            if os.path.isfile(self._input_path):
                count = 1

        if count > 0:
            self._set_image_count_text(f"{count} image(s) selected.")
        else:
            self._set_image_count_text("No images found.")
