# Application Update System

The Cockatrice Assistant now includes an integrated update system that helps users stay current with the latest features and bug fixes.

## Features

### Automatic Update Checking
- **Startup Check**: Silently checks for updates when the application starts (uses cached results)
- **Manual Check**: Users can manually check for updates in the "About" tab
- **Smart Caching**: Update checks are cached for 1 hour to avoid excessive API calls

### Update Notifications
- **Status Bar**: Shows brief update notifications when available
- **About Tab**: Detailed update information with release notes
- **Visual Indicators**: Color-coded status messages (green for updates, blue for up-to-date)

### Update Installation
- **One-Click Download**: Downloads updates directly from GitHub releases
- **Progress Tracking**: Shows download progress with MB transferred
- **Safe Installation**: Prompts before installing, allows "install later" option
- **Auto-Restart**: Optionally restarts the application with the new version

## How It Works

### Version Management
The application uses semantic versioning (e.g., `1.0.0`) defined in `version.py`:
- `__version__`: Current application version
- `is_newer_version()`: Compares version strings to detect updates

### GitHub Integration
- Checks GitHub releases via API: `https://api.github.com/repos/Swiftzn/CockatriceAssistant/releases/latest`
- Automatically finds `.exe` files in release assets
- Extracts release notes and publication dates

### Update Process
1. **Check**: Compare current version with latest GitHub release
2. **Notify**: Show update availability in UI and status bar
3. **Download**: Stream download with progress tracking to temp file
4. **Install**: Execute new version and exit current application

## User Interface

### About Tab
- **Application Info**: Name, version, description
- **Update Status**: Current vs. latest version information
- **Action Buttons**: 
  - "Check for Updates": Force fresh update check
  - "Download Update": Download available update
  - "View All Releases": Open GitHub releases page
- **Release Notes**: Formatted display of latest release changelog

### Automatic Behavior
- **Silent Check**: On startup, checks using cached results (no UI interruption)
- **Notification**: If update available, shows brief message in status bar
- **Smart Timing**: Delays update check until after app initialization (500ms)

## Building with Version Info

The build script automatically includes version metadata in the executable:

```python
# Build creates: CockatriceAssistant-v1.0.0.exe
python build_executable.py
```

Features:
- **Versioned Filename**: Executable includes version number
- **Windows Metadata**: Version info embedded in .exe properties
- **Auto-Cleanup**: Removes temporary version files after build

## Error Handling

### Network Issues
- Graceful fallback to cached results
- User-friendly error messages
- Non-blocking operation (doesn't prevent app usage)

### Download Failures
- Retry capability through manual check
- Temporary file cleanup on errors
- Safe fallback to manual GitHub download

### Installation Issues
- Option to save update for manual installation
- Clear error reporting
- No corruption of current installation

## Configuration

### GitHub Repository
Set in `version.py`:
```python
GITHUB_REPO_OWNER = "Swiftzn"
GITHUB_REPO_NAME = "CockatriceAssistant"
```

### Cache Settings
Configurable in `UpdateManager`:
- **Update Cache**: 1 hour (3600 seconds)
- **Cache Location**: `~/.cockatrice_assistant_cache/update_cache.json`

### Update Frequency
- **Startup**: Every launch (cached)
- **Manual**: On-demand via UI
- **Background**: Not implemented (manual checks only)

## Release Workflow

To release a new version:

1. **Update Version**: Edit `__version__` in `version.py`
2. **Build Executable**: Run `python build_executable.py`
3. **Create GitHub Release**: Upload the generated `.exe` file
4. **Tag Release**: Use version tag (e.g., `v1.1.0`)
5. **Add Notes**: Include changelog in release description

The update system will automatically detect and offer the new version to users on their next app launch or manual check.

## Security

- **HTTPS Only**: All downloads use secure GitHub URLs
- **Official Releases**: Only downloads from the official repository
- **User Consent**: Requires user approval before installation
- **Temp Files**: Downloads to secure temporary directory
- **Clean Exit**: Properly closes current app before installing update