"""Custom exceptions for API provider interactions."""


class ProviderError(Exception):
    """Base exception for all provider-related errors."""

    pass


class AuthenticationError(ProviderError):
    """Raised when there is an issue with API key authentication."""

    pass


class APIError(ProviderError):
    """Raised for general API errors, such as invalid requests or server-side issues."""

    pass


class NetworkError(ProviderError):
    """Raised for network-related issues, such as connection errors or timeouts."""

    pass
