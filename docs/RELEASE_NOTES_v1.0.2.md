# Cockatrice Assistant v1.0.2 Release Notes

## 🚀 Major Features

### Automatic Update System
- **Complete GitHub Integration**: Automatically checks for new releases from the GitHub repository
- **One-Click Updates**: Simple "Install Update" button that automatically downloads and installs new versions
- **Smart Caching**: 5-minute cache for update checks to avoid API rate limits
- **Version Display**: Current version shown in window title and About tab
- **Seamless Installation**: Updates automatically replace the current executable and restart the application

### Remote Theme Management
- **Dynamic Theme Loading**: Themes are now fetched from a remote JSON configuration
- **24-Hour Smart Caching**: Remote themes cached locally for 24 hours for optimal performance
- **GitHub-Hosted Themes**: All themes hosted on GitHub for easy maintenance and updates
- **Automatic Fallback**: Falls back to built-in themes if remote fetch fails
- **No More Manual Updates**: New themes appear automatically without app updates

### Commander Deck Enhancements
- **Banner Card Support**: Full support for commander banner cards in COD files
- **Proper XML Generation**: Banner cards correctly added to `<cockatrice_deck>` XML structure
- **Commander Integration**: Seamless integration with Moxfield commander deck imports

## 🛠️ Improvements & Fixes

### Card Processing
- **Dual-Faced Card Support**: Automatically handles cards with "//" in names (e.g., "Delver of Secrets // Insectile Aberration")
- **Smart Name Cleaning**: Takes the front face name for dual-faced cards to ensure Cockatrice compatibility
- **Enhanced Parsing**: Improved card name processing for better compatibility

### User Experience
- **Simplified Interface**: Streamlined update process with clear, single-action dialogs
- **Better File Naming**: Removed redundant "Decklist" from exported filenames
- **Improved Terminology**: Changed "export" to "import" for clearer user understanding
- **Organized Structure**: Cleaned up project folder structure for better maintenance

### Performance & Reliability
- **Startup Optimization**: Fixed cache loading issues on application startup
- **URL Import Fixes**: Resolved hanging issues with Moxfield URL imports
- **Better Error Handling**: Improved error handling throughout the application
- **Background Processing**: Smart background updates that don't block the UI

## 🔧 Technical Improvements

### Build System
- **Versioned Outputs**: Build system now outputs to organized `release/` folder
- **Automated Versioning**: Executable filenames include version numbers
- **Windows Metadata**: Proper version information embedded in executable files
- **Clean Builds**: Improved build scripts with better error handling

### Code Organization
- **Modular Architecture**: Split functionality into focused modules (updater.py, version.py)
- **Configuration Management**: Centralized GitHub repository configuration
- **Better Documentation**: Comprehensive inline documentation and system guides

### Development Workflow
- **Git Integration**: Updated .gitignore to exclude build artifacts and executables
- **Environment Setup**: Improved virtual environment handling and dependency management
- **Testing Infrastructure**: Better import testing and validation systems

## 📦 Installation & Updates

This version introduces automatic updates! After installing v1.0.2:
1. The app will automatically check for newer versions
2. Click "Check for Updates" in the About tab
3. If an update is available, click "Install Update" for automatic installation
4. The app will restart with the new version

## 🔄 Upgrade Path

**From v1.0.0/v1.0.1**: 
- All existing functionality preserved
- New features added seamlessly
- Settings and preferences maintained
- Remote themes will load automatically

## 🐛 Bug Fixes

- ✅ Fixed application hanging on Moxfield URL imports
- ✅ Resolved cache loading errors on startup
- ✅ Fixed dual-faced card names causing import errors
- ✅ Corrected commander deck banner card handling
- ✅ Improved file path handling across different Windows configurations

## 🎯 What's Next

The automatic update system means future improvements will be delivered seamlessly:
- New themes added to remote configuration appear immediately
- Bug fixes and feature updates install with one click
- Community-requested features can be deployed rapidly

## 💝 Acknowledgments

This release represents a major step forward in making Cockatrice Assistant a fully automated, self-maintaining tool for the Magic: The Gathering community. The remote theme system and automatic updates ensure users always have access to the latest features without manual intervention.

---

**Full Changelog**: [v1.0.1...v1.0.2](https://github.com/Swiftzn/CockatriceAssistant/compare/v1.0.1...v1.0.2)

**Download**: [Latest Release](https://github.com/Swiftzn/CockatriceAssistant/releases/latest)