
#!/usr/bin/env python3

from __future__ import annotations

import sys
import os

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def main():
    """
    Application entry point.
    """
    from src.core.app import run
    run()


if __name__ == "__main__":
    main()
