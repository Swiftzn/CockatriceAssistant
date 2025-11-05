"""
Build script for creating Windows executable of Cockatrice Assistant
"""

import os
import subprocess
import sys
from pathlib import Path


def build_executable():
    """Build the executable using PyInstaller"""

    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)

    # Ensure release directory exists
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)

    # PyInstaller command with all necessary options
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",  # Create single executable file
        "--windowed",  # No console window (GUI app)
        "--distpath",
        "release",  # Output directory
        "--workpath",
        "build",  # Temporary build directory
        "--name",
        "CockatriceAssistant",
        "--add-data",
        "requirements.txt;.",  # Include requirements
        "--hidden-import",
        "lxml",
        "--hidden-import",
        "lxml.etree",
        "--hidden-import",
        "lxml._elementpath",
        "--hidden-import",
        "requests",
        "--hidden-import",
        "bs4",
        "--collect-all",
        "tkinter",
        "--collect-all",
        "lxml",
        "app.py",
    ]

    # Add icon if it exists
    if Path("icon.ico").exists():
        cmd.insert(-1, "--icon")
        cmd.insert(-1, "icon.ico")

    print("Building Cockatrice Assistant executable...")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build successful!")
        print(f"Executable created at: release/CockatriceAssistant.exe")

        # Clean up build artifacts
        import shutil

        build_dir = Path("build")
        if build_dir.exists():
            shutil.rmtree(build_dir)

        # Remove PyInstaller spec file
        spec_file = Path("CockatriceAssistant.spec")
        if spec_file.exists():
            spec_file.unlink()

        # Remove __pycache__ directories
        for pycache in Path(".").glob("**/__pycache__"):
            if pycache.is_dir():
                shutil.rmtree(pycache)

        print("🧹 Cleaned up build artifacts")

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error code {e.returncode}")
        print(f"Error output: {e.stderr}")
        return False


if __name__ == "__main__":
    success = build_executable()
    if not success:
        sys.exit(1)
