"""Defines the abstract base class for AI providers in the Altomatic application."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseProvider(ABC):
    """
    Abstract base class for an AI provider.

    This class defines the common interface that all concrete provider
    implementations (e.g., OpenAI, OpenRouter) must adhere to.
    """

    @abstractmethod
    def describe_image(self, image_data: str, prompt: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes an image and returns a description.

        Args:
            image_data: The base64-encoded image data.
            prompt: The prompt to use for the analysis.
            state: The current application state.

        Returns:
            A dictionary containing the image description.
        """
        pass
