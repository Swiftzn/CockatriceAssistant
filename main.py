#!/usr/bin/env python3
"""Cockatrice Assistant - Main entry point

This is the main launcher for the Cockatrice Assistant application.
"""

import sys
import os
from pathlib import Path

# Handle both development and PyInstaller environments
if getattr(sys, "frozen", False):
    # PyInstaller environment - files are extracted to _MEIPASS directory
    base_path = Path(sys._MEIPASS)
    src_path = base_path / "src"
else:
    # Development environment
    base_path = Path(__file__).parent
    src_path = base_path / "src"

# Add src directory to Python path so we can import our modules
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    from gui.app import main

    main()
