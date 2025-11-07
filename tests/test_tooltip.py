import pytest

from altomatic.ui.ui_toolkit import Tooltip


def _create_root():
    tkinter = pytest.importorskip("tkinter")
    root = tkinter.Tk()
    root.withdraw()
    return tkinter, root


def test_tooltip_handles_widgets_without_insert_bbox():
    tkinter, root = _create_root()
    try:
        frame = tkinter.Frame(root)
        frame.pack()

        tooltip = Tooltip(frame, "Example tooltip")

        tooltip.show_tooltip()
        root.update_idletasks()

        assert tooltip.tooltip_window is not None

        tooltip.hide_tooltip()
        root.update_idletasks()

        assert tooltip.tooltip_window is None
    finally:
        root.destroy()
