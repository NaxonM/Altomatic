"""Defines the abstract base class for AI providers in the Altomatic application."""

import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

from .exceptions import APIError, NetworkError


class BaseProvider(ABC):
    """
    Abstract base class for an AI provider with built-in retry logic.
    """

    def _request_with_retry(self, request_func: Callable[[], Any], max_retries: int = 3, initial_delay: int = 1) -> Any:
        """
        Executes a request function with a retry mechanism for transient errors.
        """
        retries = 0
        delay = initial_delay
        while True:
            try:
                return request_func()
            except (NetworkError, APIError) as e:
                if retries >= max_retries:
                    raise
                retries += 1
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            except Exception:
                raise

    @abstractmethod
    def describe_image(self, image_data: str, prompt: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes an image and returns a description.
        This method should be implemented by subclasses and wrap the core API call
        with `self._request_with_retry`.
        """
        pass
