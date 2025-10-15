
from PySide6.QtCore import Signal, Property, str, bool
from .base_viewmodel import BaseViewModel
from src.core.utils import detect_system_proxies, get_requests_proxies, reload_system_proxies, configure_global_proxy, set_proxy_preferences

class NetworkViewModel(BaseViewModel):
    """
    ViewModel for the Network sub-tab.
    """
    proxy_enabled_changed = Signal(bool)
    proxy_override_changed = Signal(str)
    detected_proxy_changed = Signal(str)
    effective_proxy_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._proxy_enabled = True
        self._proxy_override = ""
        self._detected_proxy = ""
        self._effective_proxy = ""
        self.refresh_detected_proxy()

    @Property(bool, notify=proxy_enabled_changed)
    def proxy_enabled(self):
        return self._proxy_enabled

    @proxy_enabled.setter
    def proxy_enabled(self, value):
        if self._proxy_enabled != value:
            self._proxy_enabled = value
            self.proxy_enabled_changed.emit(value)
            self.update_effective_proxy()

    @Property(str, notify=proxy_override_changed)
    def proxy_override(self):
        return self._proxy_override

    @proxy_override.setter
    def proxy_override(self, value):
        if self._proxy_override != value:
            self._proxy_override = value
            self.proxy_override_changed.emit(value)
            self.update_effective_proxy()

    @Property(str, notify=detected_proxy_changed)
    def detected_proxy(self):
        return self._detected_proxy

    @Property(str, notify=effective_proxy_changed)
    def effective_proxy(self):
        return self._effective_proxy

    def _format_proxy_mapping(self, mapping: dict[str, str]) -> str:
        if not mapping:
            return "None"
        lines = [f"{scheme}: {value}" for scheme, value in sorted(mapping.items())]
        return "\\n".join(lines)

    def refresh_detected_proxy(self):
        detected = reload_system_proxies()
        self._detected_proxy = self._format_proxy_mapping(detected)
        self.detected_proxy_changed.emit(self._detected_proxy)
        configure_global_proxy(force=True)
        self.update_effective_proxy()

    def update_effective_proxy(self):
        proxies = get_requests_proxies(enabled=self.proxy_enabled, override=self.proxy_override or None)
        self._effective_proxy = self._format_proxy_mapping(proxies)
        self.effective_proxy_changed.emit(self._effective_proxy)
        set_proxy_preferences(self.proxy_enabled, self.proxy_override or None)
