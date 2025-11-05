"""templates.py

Helper to download and manage Cockatrice themes.
"""

import requests
import zipfile
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class CockatriceTheme:
    """Represents a Cockatrice theme with metadata."""

    name: str
    download_url: str
    description: str = ""
    version: str = ""
    author: str = ""


"""CockatriceTheme(
            name="MaterialDark",
            download_url="https://github.com/user/material-dark-cockatrice/archive/refs/tags/v1.5.zip",
            description="Material Design inspired dark theme with rounded corners and smooth animations",
            version="1.5",
            author="MaterialDesigner",
        ),
        CockatriceTheme(
            name="RetroGaming",
            download_url="https://github.com/retro/cockatrice-retro/archive/refs/tags/v3.0.zip",
            description="Nostalgic 90s gaming aesthetic with pixel-perfect fonts and classic colors",
            version="3.0",
            author="RetroThemes",
        ),
        CockatriceTheme(
            name="MinimalWhite",
            download_url="https://github.com/minimal/white-cockatrice/archive/refs/tags/v1.2.zip",
            description="Clean, minimal white theme perfect for streaming and content creation",
            version="1.2",
            author="MinimalDesign",
        ),
"""


def get_curated_themes() -> List[CockatriceTheme]:
    """Return a list of curated Cockatrice themes."""
    return [
        CockatriceTheme(
            name="DarkMingo",
            download_url="https://github.com/mingomongo/DarkMingo-Theme-for-Cockatrice/archive/refs/tags/1.3.zip",
            description="A dark theme for Cockatrice with improved visibility and modern design",
            version="1.3",
            author="mingomongo",
        ),
        # Add more themes here in the future
    ]


def download_template(url: str, dest_folder: str) -> Path:
    """Download a file from url and save into dest_folder. Returns path to saved file.
    This is a minimal placeholder; no validation beyond HTTP status.
    """
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    fname = url.split("/")[-1] or "template.bin"
    dest = Path(dest_folder) / fname
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(1024 * 8):
            if chunk:
                f.write(chunk)
    return dest


def _find_existing_theme_versions(themes_path: Path, theme_name: str) -> List[dict]:
    """Find all existing versions of a theme in the themes folder."""
    existing_versions = []

    # Look for folders matching theme name patterns
    for folder in themes_path.iterdir():
        if not folder.is_dir():
            continue

        folder_name = folder.name

        # Check for exact match (no version)
        if folder_name == theme_name:
            existing_versions.append(
                {
                    "path": folder,
                    "version": "0.0.0",  # Default version for unversioned themes
                    "folder_name": folder_name,
                }
            )
        # Check for versioned match (ThemeName_vX.X.X)
        elif folder_name.startswith(f"{theme_name}_v"):
            version_part = folder_name[len(f"{theme_name}_v") :]
            if _is_valid_version(version_part):
                existing_versions.append(
                    {
                        "path": folder,
                        "version": version_part,
                        "folder_name": folder_name,
                    }
                )

    return existing_versions


def _is_valid_version(version_str: str) -> bool:
    """Check if a string is a valid version number."""
    import re

    # Match patterns like 1.0, 1.0.0, 2.5.3, etc.
    pattern = r"^\d+(\.\d+)*$"
    return bool(re.match(pattern, version_str))


def _get_latest_version(versions: List[dict]) -> dict:
    """Get the latest version from a list of version info dictionaries."""
    if not versions:
        return None

    # Sort by version number (descending)
    def version_key(version_info):
        version = version_info["version"]
        # Convert version string to tuple of integers for proper sorting
        try:
            return tuple(int(x) for x in version.split("."))
        except ValueError:
            return (0, 0, 0)  # Fallback for invalid versions

    return max(versions, key=version_key)


def _compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings. Returns: 1 if v1 > v2, -1 if v1 < v2, 0 if equal."""

    def version_tuple(v):
        try:
            return tuple(int(x) for x in v.split("."))
        except ValueError:
            return (0, 0, 0)

    v1_tuple = version_tuple(version1)
    v2_tuple = version_tuple(version2)

    if v1_tuple > v2_tuple:
        return 1
    elif v1_tuple < v2_tuple:
        return -1
    else:
        return 0


def download_and_install_theme(theme: CockatriceTheme, themes_folder: str) -> Path:
    """Download and install a Cockatrice theme with version management.

    Args:
        theme: The theme to download and install
        themes_folder: Path to Cockatrice themes folder

    Returns:
        Path to the installed theme folder
    """
    themes_path = Path(themes_folder)
    themes_path.mkdir(parents=True, exist_ok=True)

    # Create versioned theme folder name
    if theme.version:
        theme_folder_name = f"{theme.name}_v{theme.version}"
    else:
        theme_folder_name = theme.name

    theme_folder = themes_path / theme_folder_name

    # Check for existing versions and handle updates
    existing_versions = _find_existing_theme_versions(themes_path, theme.name)

    if existing_versions:
        print(f"Found existing versions of {theme.name}: {existing_versions}")
        latest_installed = _get_latest_version(existing_versions)

        if (
            theme.version
            and _compare_versions(theme.version, latest_installed["version"]) <= 0
        ):
            print(
                f"Version {theme.version} is not newer than installed version {latest_installed['version']}"
            )
            print(
                f"Skipping installation. Use existing version at: {latest_installed['path']}"
            )
            return latest_installed["path"]
        else:
            print(
                f"Installing newer version {theme.version} (replacing {latest_installed['version']})"
            )
            # Remove all old versions
            for version_info in existing_versions:
                print(f"Removing old version: {version_info['path']}")
                shutil.rmtree(version_info["path"])

    # Remove existing theme folder if it exists (shouldn't happen after above logic, but safety check)
    if theme_folder.exists():
        shutil.rmtree(theme_folder)

    # Download ZIP to temporary location
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Download the ZIP file
        print(f"Downloading {theme.name} from {theme.download_url}...")
        resp = requests.get(theme.download_url, stream=True, timeout=30)
        resp.raise_for_status()

        zip_path = temp_path / f"{theme.name}.zip"
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Extract ZIP file
        print(f"Extracting {theme.name}...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            extract_path = temp_path / "extracted"
            zip_ref.extractall(extract_path)

            # Find the theme files (usually in a subfolder)
            extracted_items = list(extract_path.iterdir())

            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                # If there's only one folder, use its contents
                source_folder = extracted_items[0]
            else:
                # Use the extraction root
                source_folder = extract_path

            # Copy theme files to themes folder
            theme_folder.mkdir(parents=True, exist_ok=True)

            # Copy all files from source to theme folder
            for item in source_folder.iterdir():
                if item.is_file():
                    shutil.copy2(item, theme_folder)
                elif item.is_dir():
                    shutil.copytree(item, theme_folder / item.name, dirs_exist_ok=True)

    # Create version info file for future update detection
    _create_version_info_file(theme_folder, theme)

    print(f"Theme '{theme.name}' v{theme.version} installed to: {theme_folder}")
    return theme_folder


def _create_version_info_file(theme_folder: Path, theme: CockatriceTheme):
    """Create a version info file in the theme folder for update tracking."""
    import json

    version_info = {
        "name": theme.name,
        "version": theme.version,
        "author": theme.author,
        "description": theme.description,
        "download_url": theme.download_url,
        "installed_date": str(
            Path().ctime() if hasattr(Path(), "ctime") else "unknown"
        ),
    }

    version_file = theme_folder / ".theme_info.json"
    try:
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(version_info, f, indent=2)
        print(f"Created version info file: {version_file}")
    except Exception as e:
        print(f"Warning: Could not create version info file: {e}")


def get_installed_theme_info(theme_folder: Path) -> dict:
    """Get version info from an installed theme folder."""
    import json

    version_file = theme_folder / ".theme_info.json"
    if version_file.exists():
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not read version info file: {e}")

    # Fallback: try to parse from folder name
    folder_name = theme_folder.name
    if "_v" in folder_name:
        name_part, version_part = folder_name.rsplit("_v", 1)
        if _is_valid_version(version_part):
            return {
                "name": name_part,
                "version": version_part,
                "author": "Unknown",
                "description": "Installed theme",
                "download_url": "",
                "installed_date": "unknown",
            }

    # Default fallback
    return {
        "name": folder_name,
        "version": "0.0.0",
        "author": "Unknown",
        "description": "Installed theme",
        "download_url": "",
        "installed_date": "unknown",
    }


def get_default_themes_folder() -> str:
    """Get the default Cockatrice themes folder path."""
    import os

    # Default Cockatrice themes folder
    if os.name == "nt":  # Windows
        appdata = (
            Path.home() / "AppData" / "Local" / "Cockatrice" / "Cockatrice" / "themes"
        )
    else:  # Linux/Mac
        appdata = Path.home() / ".local" / "share" / "Cockatrice" / "themes"

    return str(appdata)
