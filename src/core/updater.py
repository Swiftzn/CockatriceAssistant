"""Update management for Cockatrice Assistant."""

import requests
import json
import time
import tempfile
import subprocess
import webbrowser
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.version import (
    __version__,
    GITHUB_REPO_OWNER,
    GITHUB_REPO_NAME,
    GITHUB_REPO_URL,
    is_newer_version,
)


class UpdateManager:
    """Manages application updates via GitHub releases."""

    def __init__(self):
        self.current_version = __version__
        self.api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
        self.cache_file = (
            Path.home() / ".cockatrice_assistant_cache" / "update_cache.json"
        )
        self.cache_duration = 3600  # 1 hour cache

        # Ensure cache directory exists
        self.cache_file.parent.mkdir(exist_ok=True)

    def _is_cache_valid(self) -> bool:
        """Check if cached update info is still valid."""
        if not self.cache_file.exists():
            return False

        try:
            cache_time = self.cache_file.stat().st_mtime
            return (time.time() - cache_time) < self.cache_duration
        except OSError:
            return False

    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """Load update info from cache."""
        if not self._is_cache_valid():
            return None

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def _save_cache(self, data: Dict[str, Any]) -> None:
        """Save update info to cache."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass  # Ignore cache save errors

    def check_for_updates(self, use_cache: bool = True) -> Dict[str, Any]:
        """Check for available updates.

        Args:
            use_cache: Whether to use cached results

        Returns:
            Dictionary with update information
        """
        result = {
            "update_available": False,
            "current_version": self.current_version,
            "latest_version": None,
            "download_url": None,
            "release_notes": None,
            "release_date": None,
            "assets": [],
            "error": None,
        }

        # Try cache first
        if use_cache:
            cached_data = self._load_cache()
            if cached_data:
                return cached_data

        try:
            print(f"Checking for updates from: {self.api_url}")

            headers = {
                "User-Agent": f"CockatriceAssistant/{self.current_version}",
                "Accept": "application/vnd.github.v3+json",
            }

            response = requests.get(self.api_url, headers=headers, timeout=10)
            response.raise_for_status()

            release_data = response.json()

            # Extract release information
            latest_version = release_data.get("tag_name", "").lstrip("v")
            release_notes = release_data.get("body", "")
            release_date = release_data.get("published_at", "")

            # Find executable asset
            assets = release_data.get("assets", [])
            exe_asset = None
            for asset in assets:
                if asset.get("name", "").endswith(".exe"):
                    exe_asset = asset
                    break

            download_url = exe_asset.get("browser_download_url") if exe_asset else None

            # Check if update is available
            update_available = False
            if latest_version and is_newer_version(
                self.current_version, latest_version
            ):
                update_available = True

            result.update(
                {
                    "update_available": update_available,
                    "latest_version": latest_version,
                    "download_url": download_url,
                    "release_notes": release_notes,
                    "release_date": release_date,
                    "assets": assets,
                }
            )

            # Cache the result
            self._save_cache(result)

            if update_available:
                print(f"Update available: {self.current_version} → {latest_version}")
            else:
                print(f"Application is up to date: {self.current_version}")

        except requests.RequestException as e:
            result["error"] = f"Network error: {e}"
            print(f"Update check failed: {e}")
        except Exception as e:
            result["error"] = f"Unexpected error: {e}"
            print(f"Update check error: {e}")

        return result

    def download_update(
        self, download_url: str, progress_callback=None
    ) -> Optional[Path]:
        """Download update to temporary file.

        Args:
            download_url: URL to download the update from
            progress_callback: Optional callback for download progress

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            print(f"Downloading update from: {download_url}")

            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            # Get file size for progress tracking
            total_size = int(response.headers.get("content-length", 0))

            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".exe", prefix="CockatriceAssistant_update_"
            )

            downloaded_size = 0
            chunk_size = 8192

            with temp_file as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # Report progress
                        if progress_callback and total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            progress_callback(progress, downloaded_size, total_size)

            temp_path = Path(temp_file.name)
            print(f"Update downloaded to: {temp_path}")
            return temp_path

        except Exception as e:
            print(f"Download failed: {e}")
            return None

    def install_update(
        self, update_path: Path, target_directory: Optional[Path] = None
    ) -> bool:
        """Install the downloaded update by replacing current exe.

        Args:
            update_path: Path to the downloaded update executable
            target_directory: Directory to install to (where current exe is located)

        Returns:
            True if installation was initiated successfully
        """
        try:
            print(f"Installing update from: {update_path}")

            if target_directory and target_directory.is_dir():
                # Install to the same directory as current exe
                install_path = target_directory / update_path.name
                current_exe = self._get_current_executable_path()

                print(f"Installing to: {install_path}")
                self._create_update_script(update_path, install_path, current_exe)
                return True
            else:
                # Fallback: just run the temp file
                print("No target directory specified, running from temp location")
                subprocess.Popen([str(update_path)], shell=True)
                return True

        except Exception as e:
            print(f"Installation failed: {e}")
            return False

    def _get_current_executable_path(self) -> Optional[Path]:
        """Get the path to the current executable."""
        try:
            import sys

            if getattr(sys, "frozen", False):
                # Running as PyInstaller executable
                return Path(sys.executable)
            else:
                # Running as Python script - return None to use temp method
                return None
        except Exception:
            return None

    def _create_update_script(
        self, source_path: Path, target_path: Path, current_exe: Optional[Path]
    ) -> None:
        """Create a batch script to handle the automatic update installation."""
        try:
            script_content = f"""@echo off
echo Installing Cockatrice Assistant Update...
timeout /t 2 /nobreak >nul

REM Wait for current application to close
:wait_loop
tasklist /FI "IMAGENAME eq {current_exe.name if current_exe else 'CockatriceAssistant*.exe'}" 2>NUL | find /I /N "{current_exe.name if current_exe else 'CockatriceAssistant'}" >NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak >nul
    goto wait_loop
)

REM Replace current exe with new version
echo Installing new version...
copy /Y "{source_path}" "{target_path}" >nul

REM Start new version
echo Starting updated application...
start "" "{target_path}"

REM Clean up
timeout /t 2 /nobreak >nul
del "{source_path}" >nul 2>nul
del "%~f0" >nul 2>nul
"""

            # Create update script in temp directory
            script_path = Path(tempfile.gettempdir()) / "cockatrice_update.bat"
            with open(script_path, "w") as f:
                f.write(script_content)

            # Run the update script
            subprocess.Popen(
                [str(script_path)],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            print(f"Update script created: {script_path}")

        except Exception as e:
            print(f"Failed to create update script: {e}")
            # Fallback to simple launch
            subprocess.Popen([str(source_path)], shell=True)

    def open_releases_page(self) -> None:
        """Open the GitHub releases page in the default browser."""
        releases_url = f"{GITHUB_REPO_URL}/releases"
        webbrowser.open(releases_url)
        print(f"Opened releases page: {releases_url}")


# Global update manager instance
update_manager = UpdateManager()


def check_for_updates(use_cache: bool = True) -> Dict[str, Any]:
    """Convenience function to check for updates."""
    return update_manager.check_for_updates(use_cache)


def get_current_version() -> str:
    """Get the current application version."""
    return __version__
