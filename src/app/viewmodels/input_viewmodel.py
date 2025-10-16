
from __future__ import annotations

import os
from typing import List

from PySide6.QtCore import Property, Signal

from .base_viewmodel import BaseViewModel


class InputViewModel(BaseViewModel):
    """ViewModel managing user-selected sources for processing."""

    sources_changed = Signal(list)
    sources_summary_changed = Signal(str)
    include_subdirectories_changed = Signal(bool)
    image_count_text_changed = Signal(str)

    _IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif"}

    def __init__(self) -> None:
        super().__init__()
        self._sources: list[str] = []
        self._include_subdirectories = False
        self._image_count_text = ""
        self._sources_summary = "Drop images or folders to begin"

    # --- Properties ---
    @Property(bool, notify=include_subdirectories_changed)
    def include_subdirectories(self) -> bool:
        return self._include_subdirectories

    @include_subdirectories.setter
    def include_subdirectories(self, value: bool) -> None:
        if self._include_subdirectories != value:
            self._include_subdirectories = value
            self.include_subdirectories_changed.emit(value)
            self._update_image_count()

    @Property(str, notify=image_count_text_changed)
    def image_count_text(self) -> str:
        return self._image_count_text

    @Property(str, notify=sources_summary_changed)
    def sources_summary(self) -> str:
        return self._sources_summary

    # --- Public API ---
    def sources(self) -> List[str]:
        return list(self._sources)

    def set_sources(self, paths: List[str]) -> None:
        normalized = self._normalise(paths)
        if normalized == self._sources:
            return
        self._sources = normalized
        self.sources_changed.emit(self.sources())
        self._refresh_summary()
        self._update_image_count()

    def add_sources(self, paths: List[str]) -> None:
        if not paths:
            return
        combined = self._sources + paths
        self.set_sources(combined)

    def remove_source(self, path: str) -> None:
        resolved = os.path.abspath(path)
        if resolved not in self._sources:
            return
        updated = [p for p in self._sources if p != resolved]
        self.set_sources(updated)

    def clear_sources(self) -> None:
        if not self._sources:
            return
        self._sources.clear()
        self.sources_changed.emit([])
        self._refresh_summary()
        self._update_image_count()

    # --- Private Methods ---
    def _normalise(self, paths: List[str]) -> List[str]:
        seen: dict[str, None] = {}
        for raw in paths:
            if not raw:
                continue
            resolved = os.path.abspath(raw)
            if not os.path.exists(resolved):
                continue
            seen.setdefault(resolved, None)
        return list(seen.keys())

    def _refresh_summary(self) -> None:
        if not self._sources:
            summary = "Drop images or folders to begin"
        else:
            folders = sum(1 for path in self._sources if os.path.isdir(path))
            files = len(self._sources) - folders
            parts = []
            if folders:
                parts.append(f"{folders} folder{'s' if folders > 1 else ''}")
            if files:
                parts.append(f"{files} file{'s' if files > 1 else ''}")
            summary = ", ".join(parts)
        if summary != self._sources_summary:
            self._sources_summary = summary
            self.sources_summary_changed.emit(summary)

    def _set_image_count_text(self, value: str) -> None:
        if self._image_count_text != value:
            self._image_count_text = value
            self.image_count_text_changed.emit(value)

    def _get_image_count_in_folder(self, folder_path: str) -> int:
        if not os.path.isdir(folder_path):
            return 0

        count = 0
        if self._include_subdirectories:
            walker = os.walk(folder_path)
        else:
            walker = [(folder_path, [], os.listdir(folder_path))]

        for root, _, files in walker:
            for file in files:
                if os.path.splitext(file)[1].lower() in self._IMAGE_EXTENSIONS:
                    count += 1
        return count

    def _update_image_count(self) -> None:
        if not self._sources:
            self._set_image_count_text("")
            return

        count = 0
        for path in self._sources:
            if os.path.isdir(path):
                count += self._get_image_count_in_folder(path)
            elif os.path.isfile(path):
                if os.path.splitext(path)[1].lower() in self._IMAGE_EXTENSIONS:
                    count += 1

        if count > 0:
            self._set_image_count_text(f"{count} image(s) ready for processing.")
        else:
            self._set_image_count_text("No supported images found in the selected sources.")
