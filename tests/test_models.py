"""Tests for the models module."""

def test_import_models():
    """Verify that the models module can be imported without errors."""
    try:
        from altomatic import models
    except ImportError as e:
        assert False, f"Failed to import models module: {e}"
