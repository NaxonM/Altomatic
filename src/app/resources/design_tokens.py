
# src/app/resources/design_tokens.py

class Colors:
    """
    Defines the color palette for the application, based on the original
    Arctic Light theme.
    """
    PRIMARY = "#3498db"
    PRIMARY_FOREGROUND = "#ffffff"
    SECONDARY = "#f1f1f1"
    SECONDARY_FOREGROUND = "#333333"
    BACKGROUND = "#ffffff"
    FOREGROUND = "#333333"
    SURFACE = "#f8f9fa"
    SURFACE_2 = "#e9ecef"
    DANGER = "#e74c3c"
    WARNING = "#f39c12"
    SUCCESS = "#2ecc71"
    INFO = "#3498db"
    MUTED = "#868e96"

class Typography:
    """
    Defines typography settings for the application.
    """
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_BASE = "13px"
    FONT_SIZE_LARGE = "15px"
    FONT_SIZE_SMALL = "11px"
    FONT_WEIGHT_BOLD = "600"
    FONT_WEIGHT_NORMAL = "400"

class Spacing:
    """
    Defines spacing units for consistent layout.
    """
    BASE_UNIT = 3
    SMALL = f"{BASE_UNIT * 2}px"
    MEDIUM = f"{BASE_UNIT * 4}px"
    LARGE = f"{BASE_UNIT * 6}px"
