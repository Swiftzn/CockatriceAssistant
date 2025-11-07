"""
Build script for creating Windows executable of Cockatrice Assistant
"""

import os
import subprocess
import sys
from pathlib import Path
from version import __version__, APP_NAME, APP_DESCRIPTION


def create_version_info():
    """Create version info file for PyInstaller."""
    version_parts = __version__.split(".")
    while len(version_parts) < 4:
        version_parts.append("0")

    version_tuple = ", ".join(version_parts)

    version_info_content = f"""# UTF-8
#
# Version information for {APP_NAME}
#

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_tuple}),
    prodvers=({version_tuple}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{APP_NAME}'),
        StringStruct(u'FileDescription', u'{APP_DESCRIPTION}'),
        StringStruct(u'FileVersion', u'{__version__}'),
        StringStruct(u'InternalName', u'CockatriceAssistant'),
        StringStruct(u'LegalCopyright', u'© 2025 {APP_NAME}'),
        StringStruct(u'OriginalFilename', u'CockatriceAssistant.exe'),
        StringStruct(u'ProductName', u'{APP_NAME}'),
        StringStruct(u'ProductVersion', u'{__version__}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""

    with open("version_info.txt", "w", encoding="utf-8") as f:
        f.write(version_info_content)

    print(f"Created version info file for v{__version__}")


def build_executable():
    """Build the executable using PyInstaller"""

    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)

    # Create version info file
    create_version_info()

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
        f"CockatriceAssistant-v{__version__}",
        "--add-data",
        "requirements.txt;.",  # Include requirements
        f"--version-file=version_info.txt",  # Add version info file
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
        spec_file = Path(f"CockatriceAssistant-v{__version__}.spec")
        if spec_file.exists():
            spec_file.unlink()

        # Remove version info file
        version_info_file = Path("version_info.txt")
        if version_info_file.exists():
            version_info_file.unlink()

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
