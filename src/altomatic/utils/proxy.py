"""Proxy utilities for routing network traffic."""

from __future__ import annotations

import os
from functools import lru_cache
from threading import Lock
from typing import Dict
from urllib.request import getproxies

_PROXY_LOCK = Lock()
_PREFERENCES: dict[str, object | None] = {"enabled": True, "override": None}
_ORIGINAL_ENV: dict[str, str | None] = {}
_APPLIED_KEYS: set[str] = set()


def _normalize_proxies(raw: Dict[str, str] | None) -> dict[str, str]:
    proxies: dict[str, str] = {}
    if not raw:
        return proxies

    for scheme, proxy in raw.items():
        if not proxy:
            continue
        scheme_key = str(scheme).lower().strip()
        proxy_value = str(proxy).strip()
        if not scheme_key or not proxy_value:
            continue
        proxies[scheme_key] = proxy_value

    if "all" in proxies:
        fallback = proxies["all"]
        proxies.setdefault("http", fallback)
        proxies.setdefault("https", fallback)

    return proxies


@lru_cache(maxsize=1)
def detect_system_proxies() -> dict[str, str]:
    """Return normalized proxies detected from the host system."""

    return _normalize_proxies(getproxies())


def reload_system_proxies() -> dict[str, str]:
    """Force a fresh probe of system proxy settings."""

    detect_system_proxies.cache_clear()
    return detect_system_proxies()


def _effective_preferences(
    enabled: bool | None = None,
    override: str | None = None,
) -> tuple[bool, str | None]:
    with _PROXY_LOCK:
        pref_enabled = bool(_PREFERENCES.get("enabled", True))
        pref_override = _PREFERENCES.get("override")

    final_enabled = pref_enabled if enabled is None else bool(enabled)
    final_override = pref_override if override is None else override
    if isinstance(final_override, str):
        final_override = final_override.strip() or None
    return final_enabled, final_override if final_enabled else None


def _resolve_proxies(enabled: bool, override: str | None) -> dict[str, str]:
    if not enabled:
        return {}
    if override:
        value = override.strip()
        return {"http": value, "https": value}
    proxies = detect_system_proxies()
    resolved: dict[str, str] = {}
    for scheme in ("http", "https"):
        if scheme in proxies:
            resolved[scheme] = proxies[scheme]
    if not resolved and "all" in proxies:
        resolved = {"http": proxies["all"], "https": proxies["all"]}
    return resolved


def _record_original(key: str) -> None:
    if key not in _ORIGINAL_ENV:
        _ORIGINAL_ENV[key] = os.environ.get(key)


def _restore_key(key: str) -> None:
    original = _ORIGINAL_ENV.get(key)
    if original is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = original
    _APPLIED_KEYS.discard(key)


def _restore_all() -> None:
    for key in list(_APPLIED_KEYS):
        _restore_key(key)


def _apply_env(proxies: dict[str, str], *, force: bool) -> None:
    schemes = ("http", "https")
    for scheme in schemes:
        value = proxies.get(scheme)
        for env_key in (f"{scheme}_proxy", f"{scheme}_proxy".upper()):
            if value:
                if not force and env_key not in _APPLIED_KEYS and env_key in os.environ:
                    continue
                _record_original(env_key)
                os.environ[env_key] = value
                _APPLIED_KEYS.add(env_key)
            else:
                if env_key in _APPLIED_KEYS:
                    _restore_key(env_key)

    # Ensure we clean up schemes not provided
    for scheme in schemes:
        if scheme in proxies:
            continue
        for env_key in (f"{scheme}_proxy", f"{scheme}_proxy".upper()):
            if env_key in _APPLIED_KEYS:
                _restore_key(env_key)


def set_proxy_preferences(enabled: bool, override: str | None) -> dict[str, str]:
    """Persist proxy preferences and apply them globally."""

    normalized_override = override.strip() if isinstance(override, str) else override
    if isinstance(normalized_override, str) and not normalized_override:
        normalized_override = None

    with _PROXY_LOCK:
        _PREFERENCES["enabled"] = bool(enabled)
        _PREFERENCES["override"] = normalized_override

    return configure_global_proxy(force=True)


def configure_global_proxy(
    *,
    enabled: bool | None = None,
    override: str | None = None,
    force: bool = False,
) -> dict[str, str]:
    """Populate environment variables based on preferences and return the mapping."""

    effective_enabled, effective_override = _effective_preferences(enabled, override)
    proxies = _resolve_proxies(effective_enabled, effective_override)

    with _PROXY_LOCK:
        if not proxies:
            _restore_all()
            return {}
        _apply_env(proxies, force=force or bool(effective_override))
        return dict(proxies)


def get_requests_proxies(*, enabled: bool | None = None, override: str | None = None) -> dict[str, str]:
    """Return a proxies mapping suitable for the Requests library."""

    effective_enabled, effective_override = _effective_preferences(enabled, override)
    return _resolve_proxies(effective_enabled, effective_override)
