# Cockatrice Assistant - Changelog

## Version History and Release Notes

---

<<<<<<< HEAD
## Version 1.2.1 (Latest) - December 6, 2025
*"Moxfield Import Fix"*

### 🐛 Bug Fixes
- **Moxfield Import**: Fixed broken Moxfield deck imports due to Cloudflare API protection
  - Integrated `cloudscraper` library to bypass Cloudflare challenges
  - Added retry logic with exponential backoff for handling API rate limits
  - Moxfield imports now work for all deck types (Commander, Standard, Modern, etc.)
  - Properly handles commander decks with correct card counts (98 mainboard + 2 commanders = 100 total)

### 🔧 Improvements
- **API Resilience**: Enhanced error handling for protected API endpoints
- **Retry Logic**: Automatic retry mechanism for transient API failures
- **User Experience**: Better error messages when API requests fail

### 📦 Dependencies
- **New Requirement**: Added `cloudscraper>=1.2.71` for Cloudflare bypass capability
=======
## Version 1.2.0 (Latest) - November 27, 2025
*"Archidekt Deck Import Support"*

### ✨ New Features
- **Archidekt.com Integration**: Added complete support for Archidekt deck imports
  - Direct URL-based importing from popular modern deck building platform
  - Supports all Archidekt deck URLs (format: `https://archidekt.com/decks/{id}/{name}`)
  - Automatic format detection (Commander, Standard, Modern, etc.)
  - Category-based filtering respecting deck composition settings
  - Proper handling of Maybeboard exclusion (cards marked as not included)
- **Multi-Platform Deck Import**: Expanded deck source ecosystem
  - **Archidekt**: Modern deck building with advanced categorization ✨ **NEW**
  - **Moxfield**: Community deck sharing platform
  - **MTGGoldfish**: Popular MTG website database
  - **MTGJSON**: Official preconstructed decks
- **Enhanced Commander Support**: Improved Commander format handling
  - Accurate 100-card validation (1 commander + 99 library cards)
  - Proper quantity accounting for multi-quantity cards (e.g., 2x Forest)
  - Correct commander placement (separate from mainboard/sideboard)
- **Advanced API Integration**: Robust API handling with comprehensive error recovery
  - Category inclusion/exclusion filtering based on deck settings
  - Nested JSON parsing for complex deck structures
  - Layout-aware card processing for Adventure cards and special formats

### 🔧 Improvements
- **Deck Import Manager**: Enhanced universal import system
  - Automatic scraper selection based on URL patterns
  - Consistent conversion to Cockatrice format across all sources
  - Unified error handling and progress reporting
- **Card Quantity Handling**: Fixed quantity counting in deck statistics
  - Display shows actual card totals, not just unique card entries
  - Proper accounting for multi-quantity basic lands and staples
  - Accurate Commander format validation (exactly 100 cards)
- **API Error Recovery**: Improved handling of external service issues
  - Graceful degradation when APIs are unavailable
  - Clear error messages distinguishing network vs parsing issues
  - Robust timeout handling and connection management

### 🐛 Bug Fixes
- **Commander Deck Composition**: Fixed commander duplication in sideboard
  - Commanders now properly stored separately from mainboard/sideboard
  - Correct Cockatrice format conversion with commander in appropriate zone
  - Accurate total card counting for format validation
- **Quantity Display**: Fixed deck statistics showing incorrect card counts
  - Display now shows total cards by quantity, not unique entries
  - Proper handling of cards with quantity > 1 (basic lands, etc.)
  - Accurate format validation based on total card count

### 📦 Build Information  
- **Executable Size**: 18.6MB standalone Windows executable (optimized from ~19.4MB)
- **Dependencies**: All dependencies bundled (no Python installation required)
- **Performance**: Full multi-platform import support with robust error handling

---

## Version 1.1.6 - November 23, 2025
*"Adventure Card Support"*

### 🐛 Bug Fixes
- **Adventure Card Names**: Fixed Adventure cards showing as "Unknown" in Cockatrice
  - Adventure cards (e.g., "Murderous Rider // Swift End") now preserve the full name including "//"
  - Other dual-faced cards (Transform, Modal DFC) still correctly use only the front face name
  - Added layout detection to properly handle different card types from MTGJSON data
- **Card Name Processing**: Enhanced card name cleaning to be layout-aware
  - MTGJSON imports now include layout information for proper card name handling
  - Backward compatibility maintained for existing import formats

### 🔧 Improvements
- **MTGJSON Integration**: Better handling of card metadata including layout information
- **Code Documentation**: Added comments about Adventure card handling limitations in Moxfield imports
>>>>>>> c178c45c3598275919c58e847facee00ad43323d

---

## Version 1.1.5 - November 18, 2025
*"API Error Handling & UI Polish"*

### 🐛 Bug Fixes
- **API Error Handling**: Fixed silent failures when MTGJSON API is down (HTTP 500 errors)
  - Deck imports now properly report errors instead of creating empty .cod files
  - Added specific error messages for server outages and network issues
  - Application now stops processing when API failures are detected
- **Update Dialog**: Simplified update installation dialog
  - Removed verbose text and reduced dialog size (400x250)
  - Clean, minimal interface showing only essential information

### 🔧 Improvements
- **Error Reporting**: Clear distinction between API failures and file write errors
- **User Experience**: Better feedback when external services are unavailable
- **UI Design**: Streamlined update dialog with focused messaging

### 📦 Build Information
- **Executable Size**: ~19.4MB standalone Windows executable
- **Dependencies**: All dependencies bundled (no Python installation required)
- **Performance**: Robust error handling with graceful API failure recovery

---

## Version 1.1.4 - November 18, 2025
*"Update Installation Enhancement"*

### 🐛 Bug Fixes
- **Update Installation**: Enhanced automatic update replacement system
  - Fixed update process to properly replace existing executable instead of creating versioned files
  - Added backup and restore functionality for safer updates
  - Improved error handling with automatic rollback on failed updates
  - Updates now replace the current executable with the same filename

### 🔧 Improvements
- **Update Safety**: Enhanced update script with backup/restore mechanism
- **Error Recovery**: Automatic restoration of original executable if update fails
- **User Experience**: Seamless executable replacement maintains user shortcuts and associations

### 📦 Build Information
- **Executable Size**: ~19.4MB standalone Windows executable
- **Dependencies**: All dependencies bundled (no Python installation required)
- **Performance**: Full MTGJSON integration with enhanced update system

---

## Version 1.1.3 - November 18, 2025
*"MTGJSON Import System Fix"*

### 🐛 Bug Fixes
- **MTGJSON Import**: Fixed deck import functionality in MTGJSON system
  - Resolved type mismatch in `get_deck_summary` method
  - Fixed `get_preconstructed_decks` to properly convert MTGDeck objects
  - Deck imports now populate card lists correctly instead of creating empty .cod files
  - All 2,571 preconstructed decks now import with proper card data

### 📦 Build Information
- **Executable Size**: ~19.4MB standalone Windows executable
- **Dependencies**: All dependencies bundled (no Python installation required)
- **Performance**: Full MTGJSON integration with verified import functionality

---

## Version 1.1.2 - November 13, 2025
*"Critical Update Installation Fix"*

### 🐛 Critical Bug Fixes
- **Update Installation**: Fixed critical bug preventing users from installing updates
  - Resolved method name mismatch in `src/core/updater.py`
  - Update installation now works properly through GUI
  - Users can successfully install new versions without manual intervention

### 📦 Build Information
- **Executable Size**: ~19.4MB standalone Windows executable
- **Dependencies**: All dependencies bundled (no Python installation required)
- **Performance**: Maintains all MTGJSON integration and documentation features

---

## Version 1.1.1 - November 13, 2025
*"Update Dialog Display Fix"*

### 🐛 Bug Fixes
- **Update Dialog Display**: Fixed update popup window sizing and layout issues
  - Increased dialog size from 400x250 to 500x350 to accommodate all content
  - Improved content layout with proper spacing and centering
  - Enhanced button positioning and keyboard navigation
  - Fixed dialog centering to work on all screen resolutions
- **UI Polish**: Better visual hierarchy in update installation dialog

### 📦 Build Information
- **Executable Size**: 19.4MB standalone Windows executable
- **Dependencies**: All dependencies bundled (no Python installation required)
- **Performance**: Maintains all MTGJSON integration features

---

## Version 1.1.0 - November 13, 2025
*"MTGJSON Integration & Professional Polish"*

### ✨ New Features
- **Complete MTGJSON Integration**: Switched from Moxfield to MTGJSON API as primary data source
  - Access to 2,571 preconstructed Magic decks from official Wizards of the Coast data
  - Comprehensive format coverage: Commander (198), Standard (197), Limited (453), Historic, Modern, Pioneer
- **Smart Cache System**: Intelligent 24-hour cache management
  - Automatic cache validation on application startup
  - Dramatically improved loading performance (0.5s cached vs 3-5s fresh)
  - Full offline mode capability with cached data
- **Format-Based Filtering**: Complete deck organization redesign
  - 7 distinct format categories with accurate deck counts
  - Intuitive organization replacing confusing deck type system
- **Real-Time Search**: Live deck search functionality
  - Search across deck names, codes, and types as you type
  - Instant filtering combined with format selection
- **Enhanced Commander Support**: Proper Commander deck handling
  - Commanders automatically placed in sideboard for Cockatrice compatibility
  - First commander set as banner card for visual identification
  - Accurate format detection for Commander vs non-Commander decks
- **Comprehensive Documentation System**: Complete documentation overhaul
  - **USER_GUIDE.md**: Step-by-step user manual with screenshots and troubleshooting
  - **TECHNICAL_DOCUMENTATION.md**: Complete developer reference with architecture details
  - **Professional README.md**: Modern project overview with quick start guides
- **Documentation Consolidation**: Merged 14+ scattered documentation files
  - Eliminated duplicate information across multiple files
  - Single source of truth for each documentation topic
  - Improved discoverability and maintainability

### 🔧 Improvements
- **Auto-Update Behavior**: Removed manual update button
  - Cache updates automatically on application startup
  - Smart update checking prevents unnecessary downloads
  - Background operation maintains UI responsiveness
- **Performance Optimization**: Significant speed improvements
  - Threaded operations for network requests
  - Efficient deck filtering and search algorithms
  - Reduced memory footprint for large deck collections
- **User Experience**: Streamlined interface design
  - Removed unnecessary advanced filtering options
  - Simplified filter controls to format + search only
  - Cleaner, more intuitive navigation
- **Project Organization**: Major cleanup of development artifacts
  - Removed redundant test scripts and temporary files
  - Streamlined project structure for better navigation
  - Clean build system with proper version management
- **Professional Presentation**: Enhanced project appearance
  - Modern README with feature highlights and statistics
  - Platform-specific installation instructions
  - Clear architecture overview and development guidelines

### 🐛 Bug Fixes
- **Secret Lair Filtering**: Automatically exclude "Secret Lair Drop" decks by default
- **Deck Import Accuracy**: Fixed Commander deck conversion issues
  - Proper mainboard vs sideboard placement
  - Correct banner card assignment
  - Format detection improvements
- **Cache Reliability**: Improved cache validation and error handling
  - Better network failure recovery
  - Consistent cache metadata management
  - Graceful degradation for offline usage
- **Version Management**: Proper version numbering system
- **Build Process**: Clean artifact removal and consistent naming
- **File Organization**: Consistent documentation structure

### 🔄 Breaking Changes
- **Data Source Migration**: Removed Moxfield integration in favor of MTGJSON
  - Existing Moxfield imports no longer supported
  - All deck data now sourced from official MTGJSON
- **Filter System Redesign**: Replaced deck type filtering with format-based system
  - Previous deck type preferences will be reset
  - New format categories provide better organization

### 📦 Build Information
- **Executable Size**: 19.4MB standalone Windows executable
- **Dependencies**: All dependencies bundled (no Python installation required)
- **Performance**: 6x faster loading with smart cache system

---

## Version 1.0.3 - November 2025
*"Stability & Infrastructure Improvements"*

### 🔧 Improvements
- **Build System**: Enhanced executable generation process
- **Error Handling**: Improved error recovery mechanisms
- **Performance**: Optimized application loading and processing
- **Code Quality**: Enhanced type hints and documentation

### � Bug Fixes
- **Memory Management**: Fixed memory issues with large operations
- **Thread Safety**: Resolved GUI update race conditions
- **File Permissions**: Better handling of protected directories

---

## Version 1.0.2 - November 2025
*"Moxfield Integration & Deck Import Enhancement"*

### ✨ New Features
- **Moxfield Integration**: Added support for Moxfield deck imports
  - Direct URL-based deck importing from popular deck building site
  - Automatic format detection and parsing
  - Proper card conversion to Cockatrice format
- **Advanced Filtering**: Enhanced deck filtering capabilities
  - Multiple filter criteria support
  - Date range filtering for deck releases
  - Format-specific deck discovery

### 🔧 Improvements
- **Deck Conversion Engine**: Improved Universal Deck format
  - Better handling of Commander deck structures
  - Enhanced sideboard management
  - More accurate format detection
- **User Interface**: Refined GUI elements
  - Better error messaging
  - Improved progress indicators
  - Enhanced filter controls

### 🐛 Bug Fixes
- **Import Reliability**: Fixed various deck import edge cases
- **Format Detection**: Improved accuracy of format recognition
- **File Handling**: Better error recovery for corrupted files

---

## Version 1.0.1 - November 2025
*"Stability & Performance Update"*

### 🔧 Improvements
- **Error Handling**: Enhanced error recovery mechanisms
- **Performance**: Optimized deck loading and processing
- **UI Responsiveness**: Improved GUI thread management

### 🐛 Bug Fixes
- **Memory Leaks**: Fixed memory issues with large deck collections
- **Thread Safety**: Resolved GUI update race conditions
- **File Permissions**: Better handling of protected directories

---

## Version 1.0.0 - November 2025
*"Initial Release"*

### ✨ New Features
- **Core Deck Import System**: First stable release of Cockatrice Assistant
- **Theme Management**: Curated theme download and installation system
- **GUI Application**: Complete tkinter-based desktop interface
- **Cross-Platform Support**: Windows, macOS, and Linux compatibility

### 🐛 Bug Fixes
- **Deck Export**: Fixed .cod file generation issues
- **Theme Installation**: Resolved theme downloading problems
- **Path Detection**: Improved Cockatrice installation discovery

### 🔧 Improvements
- **Logging**: Added comprehensive debug logging
- **Validation**: Enhanced input validation throughout application

---

## Development History

### Pre-Release Development - 2025
*"Initial Development & Prototypes"*

The development of Cockatrice Assistant began in 2025 with the goal of creating a comprehensive deck import and theme management tool for the Cockatrice Magic: The Gathering client.

#### Key Development Milestones
- **October 2025**: Project inception and initial prototypes
- **November 2025**: Core functionality implementation
  - MTGJSON integration for official deck data
  - Smart caching system development
  - Format-based filtering design
  - Commander deck handling improvements
  - Professional documentation structure
- Core deck import functionality
- Basic GUI interface

#### Version 1.2.x - March 2024
- Private beta testing
- Initial theme support
- Command-line interface

#### Version 1.1.x - February 2024
- Alpha development
- Proof of concept
- Basic .cod file generation

#### Version 1.0.x - January 2024
- Initial development
- Core concept validation
- Research and design

---

## Development Timeline

### Key Milestones

```
October 2025    │ Project Inception
    ↓           │ • Initial concept and research
    ↓           │ • Core architecture planning
November 2025   │ Development & Implementation
    ↓           │ • MTGJSON integration
    ↓           │ • Smart caching system
    ↓           │ • Format-based filtering
    ↓           │ • Commander deck fixes
    ↓           │ v1.0.0 - Initial Release
    ↓           │ v1.0.1 - Stability improvements
    ↓           │ v1.0.2 - Moxfield integration
    ↓           │ v1.0.3 - MTGJSON integration
    ↓           │ v1.1.0 - Documentation consolidation
Present         │ • Current stable release
```

### Project Stats

- **Deck Sources**: 4 major platforms (MTGJSON, Moxfield, MTGGoldfish, Archidekt)
- **Deck Collection**: 2,571+ official MTG preconstructed decks + unlimited community decks
- **Format Support**: All MTG formats with accurate categorization and validation
- **Performance**: 6x faster loading with smart cache system
- **Platform Support**: Windows (primary), macOS, Linux compatible
- **Documentation**: Comprehensive user and developer guides

---

## Migration Guides

### From v1.0.x to v1.1.0

#### Documentation Structure
```
Previous: Scattered documentation files (14+ files)
Current: Organized documentation system (3 main files)
Benefit: Clear, consolidated information structure
Action: Use new USER_GUIDE.md for instructions
```

#### Project Organization
```
Previous: Mixed development and release files
Current: Clean project structure
Benefit: Better maintainability and navigation
Action: None required - automatic improvement
```

### Key Migration Notes

#### MTGJSON Integration (v1.0.3+)
```
Data Source: Official MTGJSON API with 2,571 decks
Cache System: 24-hour intelligent caching for performance
Format Filtering: 7 distinct MTG formats for better organization
Search: Real-time deck search across multiple fields
```

#### Commander Deck Handling
```
Sideboard Placement: Commanders properly placed in sideboard
Banner Cards: First commander automatically set as banner
Format Detection: Accurate Commander vs non-Commander recognition
```

---

## Future Roadmap

### Planned Features (v1.3.0)
- **Enhanced Search**: Advanced search with card name filtering and mana cost filters
- **Deck Statistics**: Analysis tools showing format distribution and deck characteristics
- **Bulk Operations**: Export multiple decks simultaneously
- **Additional Deck Sources**: EDHRec, TappedOut, and other popular platforms
- **Theme Previews**: Visual theme previews before installation

### Long-term Vision (v2.0.0+)
- **Database Integration**: SQLite for advanced queries and better performance
- **Enhanced Search**: Card-level filtering and advanced deck analysis
- **Collection Integration**: Sync with popular MTG collection tools
- **Community Features**: Deck sharing and rating system

### Technical Improvements
- **Test Coverage**: Comprehensive automated test suite
- **Performance**: Sub-second loading for all operations
- **Cross-Platform**: Native installers for macOS and Linux
- **Accessibility**: Full screen reader and keyboard navigation support

---

## Support and Resources

### Getting Help
- **User Guide**: Complete feature documentation in USER_GUIDE.md
- **Technical Docs**: Developer reference in TECHNICAL_DOCUMENTATION.md
- **GitHub Issues**: Bug reports and feature requests
- **Community Discord**: Real-time support and discussion

### Contributing
- **Bug Reports**: Use GitHub issue templates
- **Feature Requests**: Community voting on roadmap items
- **Code Contributions**: Pull requests welcome with tests
- **Documentation**: Help improve user and developer guides

### Release Process
1. **Development**: Feature branches with comprehensive testing
2. **Beta Testing**: Community preview with feedback integration
3. **Quality Assurance**: Automated and manual testing suites
4. **Release**: GitHub release with auto-update distribution
5. **Post-Release**: Community feedback and patch releases

---

*For technical support or contributions, visit: https://github.com/Swiftzn/CockatriceAssistant*

*Last updated: November 27, 2025*