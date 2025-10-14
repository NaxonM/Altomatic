"""Module entry point for running Altomatic."""

if __package__ in {None, ""}:
    import os
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from altomatic.app import run
else:
    from .app import run


def main() -> None:
    run()


if __name__ == "__main__":
    main()
