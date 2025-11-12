"""templates.py

Helper to download and manage Cockatrice themes.
"""

import requests
import zipfile
import tempfile
import shutil
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CockatriceTheme:
    """Represents a Cockatrice theme with metadata."""

    name: str
    download_url: str
    description: str = ""
    version: str = ""
    author: str = ""


# Cache for GitHub release info to avoid repeated API calls
_github_cache = {}
_cache_duration = 300  # 5 minutes cache

# Remote curated themes configuration
REMOTE_THEMES_URL = (
    "https://gist.githubusercontent.com/Swiftzn/ad3dbd7384da4162e5f8fbc58f223312/raw"
)
_remote_themes_cache = {}
_remote_themes_cache_duration = 86400  # 24 hours cache for remote themes list


def get_latest_github_release(
    repo_owner: str, repo_name: str, use_cache: bool = True
) -> Optional[dict]:
    """Fetch the latest release information from a GitHub repository.

    Args:
        repo_owner: GitHub username/organization
        repo_name: Repository name
        use_cache: Whether to use cached results

    Returns:
        Dictionary with release information or None if failed
    """
    cache_key = f"{repo_owner}/{repo_name}"
    current_time = time.time()

    # Check cache first if enabled
    if use_cache and cache_key in _github_cache:
        cached_data, cache_time = _github_cache[cache_key]
        if current_time - cache_time < _cache_duration:
            print(f"Using cached release info for {cache_key}")
            return cached_data

    try:
        api_url = (
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        )
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CockatriceAssistant/1.0",
        }

        print(f"Fetching latest release info from: {api_url}")
        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code == 200:
            release_data = response.json()
            result = {
                "tag_name": release_data.get("tag_name", ""),
                "name": release_data.get("name", ""),
                "body": release_data.get("body", ""),
                "published_at": release_data.get("published_at", ""),
                "zipball_url": release_data.get("zipball_url", ""),
                "tarball_url": release_data.get("tarball_url", ""),
                "html_url": release_data.get("html_url", ""),
            }

            # Cache the result
            _github_cache[cache_key] = (result, current_time)
            return result
        else:
            print(f"Failed to fetch release info: HTTP {response.status_code}")

            # Return cached data if available even if expired
            if cache_key in _github_cache:
                print("Falling back to cached data due to API error")
                cached_data, _ = _github_cache[cache_key]
                return cached_data
            return None

    except Exception as e:
        print(f"Error fetching GitHub release info: {e}")

        # Return cached data if available even if expired
        if cache_key in _github_cache:
            print("Falling back to cached data due to network error")
            cached_data, _ = _github_cache[cache_key]
            return cached_data
        return None


def clear_github_cache():
    """Clear the GitHub API cache to force fresh requests."""
    global _github_cache
    _github_cache.clear()
    print("GitHub release cache cleared")


def clear_remote_themes_cache():
    """Clear the remote themes cache to force fresh requests."""
    global _remote_themes_cache
    _remote_themes_cache.clear()
    print("Remote themes cache cleared")


def get_remote_curated_themes_list() -> Optional[List[dict]]:
    """Fetch the curated themes list from remote JSON.

    Returns:
        List of theme definitions or None if failed
    """
    cache_key = "remote_themes"
    current_time = time.time()

    # Check cache first
    if cache_key in _remote_themes_cache:
        cached_data, cache_time = _remote_themes_cache[cache_key]
        if current_time - cache_time < _remote_themes_cache_duration:
            print("Using cached remote themes list")
            return cached_data

    try:
        print(f"Fetching remote curated themes from: {REMOTE_THEMES_URL}")
        headers = {
            "User-Agent": "CockatriceAssistant/1.0",
            "Accept": "application/json",
        }

        response = requests.get(REMOTE_THEMES_URL, headers=headers, timeout=10)

        if response.status_code == 200:
            themes_data = response.json()

            # Validate the JSON structure
            if isinstance(themes_data, dict) and "themes" in themes_data:
                themes_list = themes_data["themes"]
                if isinstance(themes_list, list):
                    print(f"Successfully fetched {len(themes_list)} remote themes")

                    # Cache the result
                    _remote_themes_cache[cache_key] = (themes_list, current_time)
                    return themes_list
                else:
                    print("Invalid remote themes format: 'themes' is not a list")
            else:
                print("Invalid remote themes format: missing 'themes' key")

        else:
            print(f"Failed to fetch remote themes: HTTP {response.status_code}")

        # Return cached data if available even if expired
        if cache_key in _remote_themes_cache:
            print("Falling back to cached remote themes due to fetch error")
            cached_data, _ = _remote_themes_cache[cache_key]
            return cached_data

        return None

    except Exception as e:
        print(f"Error fetching remote curated themes: {e}")

        # Return cached data if available even if expired
        if cache_key in _remote_themes_cache:
            print("Falling back to cached remote themes due to network error")
            cached_data, _ = _remote_themes_cache[cache_key]
            return cached_data

        return None


def check_themes_list_update() -> dict:
    """Check if there's an update available for the curated themes list.

    Returns:
        Dictionary with update information
    """
    result = {
        "update_available": False,
        "current_version": "unknown",
        "latest_version": "unknown",
        "message": "",
    }

    try:
        # Get current cached version info if available
        cache_key = "remote_themes"
        current_version = "0.0.0"  # Default if no cache

        if cache_key in _remote_themes_cache:
            cached_data, cache_time = _remote_themes_cache[cache_key]
            # Try to extract version from cached data
            if isinstance(cached_data, list) and len(cached_data) > 0:
                # Check if there's version metadata in the first theme or elsewhere
                current_version = "cached"

        # Force fetch latest remote themes (ignore cache)
        print("Checking for themes list updates...")
        headers = {
            "User-Agent": "CockatriceAssistant/1.0",
            "Accept": "application/json",
        }

        response = requests.get(REMOTE_THEMES_URL, headers=headers, timeout=10)

        if response.status_code == 200:
            themes_data = response.json()

            if isinstance(themes_data, dict):
                latest_version = themes_data.get("version", "unknown")
                theme_count = len(themes_data.get("themes", []))

                result["current_version"] = current_version
                result["latest_version"] = latest_version

                # Simple check - if we don't have the exact same data, consider it an update
                if cache_key not in _remote_themes_cache:
                    result["update_available"] = True
                    result["message"] = (
                        f"New themes list available with {theme_count} themes"
                    )
                else:
                    cached_data, _ = _remote_themes_cache[cache_key]
                    if len(cached_data) != theme_count:
                        result["update_available"] = True
                        result["message"] = (
                            f"Updated themes list available ({theme_count} themes)"
                        )
                    else:
                        result["message"] = (
                            f"Themes list is up to date ({theme_count} themes)"
                        )
            else:
                result["message"] = "Invalid remote themes format"
        else:
            result["message"] = (
                f"Failed to check for updates: HTTP {response.status_code}"
            )

    except Exception as e:
        result["message"] = f"Error checking for updates: {e}"

    return result


def create_theme_from_definition(theme_def: dict) -> Optional[CockatriceTheme]:
    """Create a CockatriceTheme from a remote theme definition.

    Args:
        theme_def: Dictionary containing theme definition

    Returns:
        CockatriceTheme object or None if creation failed
    """
    try:
        # Validate required fields
        required_fields = ["name", "repo_owner", "repo_name", "author"]
        for field in required_fields:
            if field not in theme_def:
                print(f"Missing required field '{field}' in theme definition")
                return None

        # Extract theme information
        theme_name = theme_def["name"]
        repo_owner = theme_def["repo_owner"]
        repo_name = theme_def["repo_name"]
        author = theme_def["author"]
        fallback_version = theme_def.get("fallback_version", "1.0")
        fallback_description = theme_def.get("description", "A Cockatrice theme")

        print(f"Creating theme: {theme_name}")

        # Use the existing create_github_theme function
        return create_github_theme(
            repo_owner=repo_owner,
            repo_name=repo_name,
            theme_name=theme_name,
            author=author,
            fallback_version=fallback_version,
            fallback_description=fallback_description,
        )

    except Exception as e:
        print(f"Error creating theme from definition: {e}")
        return None


def create_github_theme(
    repo_owner: str,
    repo_name: str,
    theme_name: str,
    author: str,
    fallback_version: str = "1.0",
    fallback_description: str = "A Cockatrice theme",
) -> CockatriceTheme:
    """Create a theme from a GitHub repository with automatic version detection.

    Args:
        repo_owner: GitHub username/organization
        repo_name: Repository name
        theme_name: Display name for the theme
        author: Theme author name
        fallback_version: Version to use if API fails
        fallback_description: Description to use if API fails or no description available

    Returns:
        CockatriceTheme object with latest or fallback information
    """
    # Fallback theme info
    fallback_theme = CockatriceTheme(
        name=theme_name,
        download_url=f"https://github.com/{repo_owner}/{repo_name}/archive/refs/tags/{fallback_version}.zip",
        description=fallback_description,
        version=fallback_version,
        author=author,
    )

    try:
        release_info = get_latest_github_release(repo_owner, repo_name)

        if release_info and release_info.get("tag_name"):
            version = release_info["tag_name"].lstrip("v")
            download_url = f"https://github.com/{repo_owner}/{repo_name}/archive/refs/tags/{release_info['tag_name']}.zip"

            # Use JSON description if provided, otherwise use GitHub release description
            if fallback_description and fallback_description != "A Cockatrice theme":
                description = fallback_description
            else:
                description = release_info.get("body", "").strip()
                if description:
                    # Clean up markdown
                    description = (
                        description.replace("#", "").replace("*", "").replace("_", "")
                    )
                    if len(description) > 150:
                        description = description[:147] + "..."
                else:
                    description = fallback_description

            print(f"Using {theme_name} latest release: {version}")

            return CockatriceTheme(
                name=theme_name,
                download_url=download_url,
                description=description,
                version=version,
                author=author,
            )
        else:
            print(
                f"No valid release info found for {theme_name}, using fallback version"
            )
            return fallback_theme

    except Exception as e:
        print(f"Error creating {theme_name} theme: {e}")
        return fallback_theme


def get_curated_themes() -> List[CockatriceTheme]:
    """Return a list of curated Cockatrice themes from remote source with latest versions from GitHub."""
    themes = []

    # Try to fetch remote curated themes list
    remote_themes = get_remote_curated_themes_list()

    if remote_themes:
        print(f"Processing {len(remote_themes)} remote theme definitions")

        for theme_def in remote_themes:
            try:
                theme = create_theme_from_definition(theme_def)
                if theme:
                    themes.append(theme)
                else:
                    print(
                        f"Failed to create theme from definition: {theme_def.get('name', 'Unknown')}"
                    )
            except Exception as e:
                print(f"Error processing theme definition: {e}")
    else:
        # Fallback to hardcoded themes if remote fetch fails
        print("Remote themes unavailable, using fallback themes")

        try:
            darkmingo_theme = create_github_theme(
                repo_owner="mingomongo",
                repo_name="DarkMingo-Theme-for-Cockatrice",
                theme_name="DarkMingo",
                author="mingomongo",
                fallback_version="1.3",
                fallback_description="A dark theme for Cockatrice with improved visibility and modern design",
            )
            themes.append(darkmingo_theme)
        except Exception as e:
            print(f"Error adding fallback DarkMingo theme: {e}")

    print(f"Successfully loaded {len(themes)} curated themes")
    return themes


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
