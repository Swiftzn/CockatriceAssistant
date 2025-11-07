"""Version management for Cockatrice Assistant."""

# Application version - update this when releasing new versions
__version__ = "1.0.2"
__version_info__ = (1, 0, 2)

# GitHub repository information for update checking
GITHUB_REPO_OWNER = "Swiftzn"
GITHUB_REPO_NAME = "CockatriceAssistant"
GITHUB_REPO_URL = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"

# Application metadata
APP_NAME = "Cockatrice Assistant"
APP_DESCRIPTION = "Precon Deck Importer and Theme Manager for Cockatrice"


def get_version() -> str:
    """Get the current application version string."""
    return __version__


def get_version_info() -> tuple:
    """Get the current application version as a tuple."""
    return __version_info__


def is_newer_version(current: str, latest: str) -> bool:
    """Compare two version strings and determine if latest is newer than current.

    Args:
        current: Current version string (e.g., "1.0.0")
        latest: Latest version string (e.g., "1.1.0")

    Returns:
        True if latest is newer than current
    """
    try:
        # Parse version strings into tuples for comparison
        current_parts = tuple(map(int, current.lstrip("v").split(".")))
        latest_parts = tuple(map(int, latest.lstrip("v").split(".")))

        return latest_parts > current_parts
    except (ValueError, AttributeError):
        # If parsing fails, assume update is available to be safe
        return True
