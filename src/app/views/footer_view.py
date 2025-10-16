from typing import Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QVariantAnimation, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .base_view import BaseView
from ..viewmodels.footer_viewmodel import FooterViewModel


class SessionTicker(QWidget):
    """Carousel-like ticker for session details."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("SessionCarouselTicker")
        
        # Set size policy to expand horizontally
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(22)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._scroll = QScrollArea(self)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setWidgetResizable(True)
        self._scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._scroll.setMaximumHeight(22)

        self._label = QLabel("—", self._scroll)
        self._label.setObjectName("SessionCarouselLine")
        self._label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self._label.setContentsMargins(0, 0, 0, 0)
        self._label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._scroll.setWidget(self._label)
        
        layout.addWidget(self._scroll)

        self._scrollbar_anim: Optional[QPropertyAnimation] = None

    def set_text(self, text: str) -> None:
        self._label.setText(text)
        self._label.adjustSize()
        self._restart_animation()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._restart_animation()

    def _restart_animation(self) -> None:
        if self._scrollbar_anim is not None:
            self._scrollbar_anim.stop()
            self._scrollbar_anim = None

        bar = self._scroll.horizontalScrollBar()
        bar.setValue(0)
        maximum = bar.maximum()

        if maximum <= 0:
            return

        duration = max(6000, int(maximum * 28))
        anim = QPropertyAnimation(bar, b"value", self)
        anim.setStartValue(0)
        anim.setEndValue(maximum)
        anim.setDuration(duration)
        anim.setLoopCount(-1)
        anim.setEasingCurve(QEasingCurve.Type.Linear)
        anim.start()
        self._scrollbar_anim = anim


class FooterView(BaseView):
    """
    The footer view, containing the status bar, progress bar, and process button.
    """
    def __init__(self, view_model: FooterViewModel, header_vm) -> None:
        super().__init__(view_model)
        self.setObjectName("SurfaceCard")
        self._header_vm = header_vm
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Sets up the UI widgets and layout."""
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 10, 14, 10)

        # Create widgets
        self.status_label = QLabel(self.view_model.status_text)
        self.status_label.setProperty("state", "muted")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(self.view_model.progress_value)
        self.process_button = QPushButton("Run Workflow")
        self.process_button.setProperty("text-role", "primary")
        self.token_label = QLabel()
        self.token_label.setProperty("state", "muted")

        # Left side container for stretching elements
        left_container = QWidget()
        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        # Add status label to the top of the left container
        left_layout.addWidget(self.status_label)

        # Add progress bar
        left_layout.addWidget(self.progress_bar)

        # Session ticker layout
        ticker_container = QWidget()
        ticker_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ticker_layout = QHBoxLayout(ticker_container)
        ticker_layout.setContentsMargins(0, 0, 0, 0)
        ticker_layout.setSpacing(6)

        self.session_caption = QLabel("Session overview:")
        self.session_caption.setProperty("state", "caption")
        self.session_caption.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        ticker_layout.addWidget(self.session_caption)

        self.session_ticker = SessionTicker(self)
        ticker_layout.addWidget(self.session_ticker, 1)
        
        left_layout.addWidget(ticker_container)

        # Add left container to the main layout with a stretch factor
        layout.addWidget(left_container, 1)

        # Add right-side widgets
        layout.addWidget(self.process_button)
        layout.addWidget(self.token_label)

        self._setup_button_animation()
        self._setup_progress_animation()
        self._refresh_session_ticker()

    def _setup_button_animation(self) -> None:
        accent = self._accent_color()

        glow = QGraphicsDropShadowEffect(self.process_button)
        glow.setColor(accent)
        glow.setOffset(0, 6)
        glow.setBlurRadius(18)
        self.process_button.setGraphicsEffect(glow)

        self._button_glow = QPropertyAnimation(glow, b"blurRadius", self)
        self._button_glow.setStartValue(18.0)
        self._button_glow.setEndValue(32.0)
        self._button_glow.setDuration(1400)
        self._button_glow.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._button_glow.setLoopCount(-1)
        self._button_glow.start()

        base_width = max(self.process_button.sizeHint().width(), 100)
        self.process_button.setMinimumWidth(base_width)
        self._button_base_width = base_width

        self._button_tap = QPropertyAnimation(self.process_button, b"minimumWidth", self)
        self._button_tap.setDuration(260)
        self._button_tap.setEasingCurve(QEasingCurve.Type.OutBack)
        self._button_tap.setLoopCount(1)
        self._button_tap.finished.connect(
            lambda: self.process_button.setMinimumWidth(self._button_base_width)
        )

        self.process_button.pressed.connect(self._on_button_pressed)

    def _setup_progress_animation(self) -> None:
        self._progress_anim = QVariantAnimation(self)
        self._progress_anim.setStartValue(0.0)
        self._progress_anim.setEndValue(1.0)
        self._progress_anim.setDuration(1600)
        self._progress_anim.setLoopCount(-1)
        self._progress_anim.valueChanged.connect(self._apply_progress_style)
        self._progress_anim.start()
        self._apply_progress_style(0.0)

    def _apply_progress_style(self, phase: float) -> None:
        accent = self._accent_color()
        low = QColor(accent)
        low.setAlphaF(0.65)
        high = QColor(accent)
        high = high.lighter(130)

        left = max(0.0, phase - 0.18)
        right = min(1.0, phase + 0.18)

        style = f"""
QProgressBar {{
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 14px;
    padding: 2px;
    text-align: center;
}}

QProgressBar::chunk {{
    border-radius: 12px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {low.name(QColor.HexArgb)},
        stop:{left:.2f} {low.name(QColor.HexArgb)},
        stop:{phase:.2f} {high.name(QColor.HexArgb)},
        stop:{right:.2f} {accent.name(QColor.HexArgb)},
        stop:1 {low.name(QColor.HexArgb)});
}}
"""
        self.progress_bar.setStyleSheet(style)

    def _on_button_pressed(self) -> None:
        if self._button_tap.state() == QPropertyAnimation.State.Running:
            self._button_tap.stop()
        self._button_tap.setStartValue(self._button_base_width)
        self._button_tap.setEndValue(self._button_base_width + 16)
        self._button_tap.start()

    def _accent_color(self) -> QColor:
        palette = self.process_button.palette()
        accent = palette.color(QPalette.ColorRole.Highlight)
        if accent.alpha() == 0:
            accent = palette.color(QPalette.ColorRole.ButtonText)
        return accent

    def _connect_signals(self):
        """Connects the view model's signals to the view's slots."""
        self.view_model.status_text_changed.connect(self.status_label.setText)
        self.view_model.progress_value_changed.connect(self.progress_bar.setValue)
        self.view_model.total_tokens_changed.connect(self._update_token_label)
        self.view_model.status_text_changed.connect(lambda _: self._refresh_session_ticker())
        self.process_button.clicked.connect(self.view_model.process_images)
        self._update_token_label(self.view_model.total_tokens)

    def _update_token_label(self, tokens: int) -> None:
        if tokens > 0:
            self.token_label.setText(f"Tokens: {tokens}")
            self.token_label.show()
        else:
            self.token_label.hide()
        self._refresh_session_ticker()

    def _refresh_session_ticker(self) -> None:
        hv: Optional[object] = self._header_vm
        if hv is None:
            self.session_ticker.set_text("—")
            return

        details = {
            "Provider": getattr(hv, "summary_model", "—"),
            "Prompt": getattr(hv, "summary_prompt", "—"),
            "Input": getattr(hv, "summary_output", "—"),
        }

        entries = [f"{key}: {value or '—'}" for key, value in details.items()]
        line = "   ✦   ".join(entries)
        self.session_ticker.set_text(line)