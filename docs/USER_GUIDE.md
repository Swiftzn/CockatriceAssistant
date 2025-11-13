# Cockatrice Assistant - User Guide

## Overview

Cockatrice Assistant is a desktop application that helps Magic: The Gathering players import official preconstructed decks into Cockatrice. With access to **2,500+ official decks** from MTG's entire history (1993-present), you can easily import Commander decks, Theme decks, Intro Packs, Challenger Decks, and more.

## Features

### 🃏 **Massive Deck Library**
- **2,571 official decks** from MTGJSON database
- **All formats**: Commander, Standard, Limited, Historic, Modern, Legacy
- **Complete history**: From Alpha (1993) to current releases
- **Smart filtering**: Filter by format or search by name/code
- **Auto-exclusion**: Secret Lair Drop decks filtered out by default

### ⚡ **Smart Performance**
- **Intelligent caching**: Only updates when needed (24-hour cache)
- **Fast startup**: Instant loading with fresh cache
- **Background updates**: Automatic fresh data when cache expires
- **Offline support**: Works with cached data when offline

### 🎯 **Proper Cockatrice Integration**
- **Commander support**: Commanders automatically placed in sideboard
- **Banner cards**: Proper banner card assignment for all deck types
- **Format-aware**: Different handling for different deck formats
- **.cod output**: Standard Cockatrice deck format

### 🎨 **Theme Management**
- **Curated themes**: Pre-selected high-quality Cockatrice themes
- **Custom themes**: Install themes from any URL
- **Auto-detection**: Finds your Cockatrice themes folder
- **Version tracking**: Manages theme updates

---

## Quick Start

### Installation

1. **Download**: Get the latest release or clone the repository
2. **Python Setup**: Ensure Python 3.8+ is installed
3. **Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run**: 
   ```bash
   python main.py
   ```

### First Use

1. **Automatic Loading**: App automatically downloads and caches deck data on first run
2. **Browse Decks**: Use format filter and search to find decks
3. **Select & Export**: Choose decks and click "Import Selected"
4. **Cockatrice**: Open Cockatrice and find your new decks!

---

## Using the Application

### Deck Browser

#### **Format Filtering**
- **All Formats**: Show all 1,957 decks (excluding Secret Lair Drop)
- **Commander**: 198 Commander precons 
- **Standard**: 197 Standard-legal products (Intro Packs, Challenger Decks)
- **Limited**: 453 Limited format products (Jumpstart, Draft, etc.)
- **Historic**: 118 Arena-specific products
- **Legacy/Modern**: Premium and competitive products

#### **Search Functionality**
- **Real-time search**: Results update as you type
- **Multi-field**: Searches deck names, codes, and types
- **Combined filtering**: Use format filter + search together
- **Clear button**: Quick reset to see all decks

#### **Deck Information**
Each deck shows:
- **Name**: Full official deck name
- **Code**: Set/product code (e.g., C18, M21)
- **Type**: Product type (Commander Deck, Intro Pack, etc.)
- **Release Date**: Official release date
- **Format**: Inferred play format

### Exporting Decks

#### **Selection**
- **Individual**: Click to select specific decks
- **Multiple**: Ctrl+click for multiple selections
- **Select All**: Button to select all visible decks

#### **Export Process**
1. **Choose decks**: Select the decks you want
2. **Set destination**: Browse or use default Cockatrice folder
3. **Import Selected**: Click to start export
4. **Monitor progress**: Status bar shows export progress

#### **Export Behavior**
- **Commander Decks**: 
  - Commander(s) placed in sideboard
  - First commander set as banner card
  - Main deck contains 99 cards
- **Other Decks**:
  - All cards in main deck
  - Random card selected as banner
  - Empty sideboard

### Save Locations

#### **Default Paths**
- **Windows**: `%LOCALAPPDATA%\Cockatrice\Cockatrice\decks`
- **Custom**: Browse to any folder
- **Auto-creation**: Folders created automatically if needed

#### **File Naming**
- Deck names cleaned for filesystem safety
- Spaces replaced with underscores  
- Invalid characters removed
- Extension: `.cod` (Cockatrice format)

### Theme Management

#### **Curated Themes**
- **Pre-selected**: High-quality themes from community
- **One-click install**: Simple installation process
- **Automatic updates**: Version checking and updates
- **Safe installation**: Proper file handling

#### **Custom Themes**
- **URL support**: Install any theme from a ZIP URL
- **Custom naming**: Set your own theme names
- **Manual installation**: For advanced users

---

## Advanced Features

### Importing from URLs

#### **Supported Sites**
- **Moxfield**: Full deck import support
- **MTGGoldfish**: Budget and competitive decks
- **Custom URLs**: Any supported deck list format

#### **Import Process**
1. **Get URL**: Copy deck URL from supported site
2. **Import from URL**: Click button in application
3. **Paste URL**: Enter the deck URL
4. **Auto-conversion**: Automatic format detection and conversion
5. **Export**: Standard .cod file creation

### Cache Management

#### **How Caching Works**
- **24-hour cycle**: Cache refreshes automatically after 24 hours
- **Smart loading**: Uses cache when fresh, updates when stale
- **Background operation**: No user intervention needed
- **Fallback system**: Uses cache if network unavailable

#### **Cache Location**
- **Folder**: `cache/` in application directory
- **Main cache**: `mtgjson_decklist.json` (2,571 decks)
- **Individual decks**: `deck_details/*.json` (downloaded as needed)
- **Metadata**: `cache_metadata.json` (timestamp tracking)

#### **Cache Benefits**
- **Fast startup**: ~0.5s with fresh cache
- **Bandwidth efficient**: Only updates when needed
- **Offline capable**: Full functionality with cached data
- **Automatic management**: No manual intervention required

---

## Troubleshooting

### Common Issues

#### **No Decks Loading**
- **Check internet**: Ensure connection for first-time setup
- **Restart app**: Close and reopen application
- **Cache location**: Verify cache folder permissions
- **Firewall**: Ensure MTGJSON.com is accessible

#### **Export Failures** 
- **Destination folder**: Verify write permissions
- **Disk space**: Ensure sufficient storage
- **Cockatrice running**: Close Cockatrice before export
- **File conflicts**: Check for existing files with same names

#### **Missing Commanders**
- **Format detection**: Ensure deck is recognized as Commander format
- **Details loading**: Deck details must download successfully
- **Network issues**: Check connection for detail fetching

#### **Themes Not Installing**
- **Cockatrice folder**: Verify correct themes directory
- **Permissions**: Check write access to themes folder
- **URL validity**: Ensure theme download URL works
- **ZIP format**: Themes must be in ZIP format

### Performance Tips

#### **Faster Loading**
- **Keep cache**: Don't delete cache folder
- **Stable internet**: Better connection = faster updates
- **SSD storage**: Faster disk improves cache performance
- **Close other apps**: More RAM for smooth operation

#### **Storage Management**
- **Cache size**: ~2-5MB for main cache
- **Deck details**: ~50KB per exported deck  
- **Growth pattern**: Only grows when exporting new decks
- **No cleanup needed**: Deck data doesn't change

---

## Integration with Cockatrice

### Setting Up Cockatrice

#### **Installation**
1. **Download Cockatrice**: Get from official website
2. **Install normally**: Follow standard installation process
3. **First run**: Complete initial Cockatrice setup
4. **Find deck folder**: Note location for Cockatrice Assistant

#### **Deck Folder Discovery**
- **Windows**: `%LOCALAPPDATA%\Cockatrice\Cockatrice\decks`
- **Auto-detection**: Application finds folder automatically
- **Custom path**: Browse manually if auto-detection fails
- **Create folder**: Make folder if it doesn't exist

### Using Imported Decks

#### **In Cockatrice**
1. **Open Cockatrice**: Start the application
2. **Deck Editor**: Go to deck management
3. **Load Deck**: Find your imported .cod files
4. **Banner Display**: Deck banner shows properly
5. **Sideboard**: Commanders appear in sideboard for EDH

#### **Deck Features**
- **Complete metadata**: Card sets, numbers preserved  
- **Proper zones**: Main deck vs sideboard correctly assigned
- **Banner cards**: Visual representation in deck lists
- **Format tags**: Deck format properly identified

---

## Tips and Best Practices

### Efficient Deck Management

#### **Organization**
- **Naming convention**: Use consistent deck naming
- **Folder structure**: Organize by format or set
- **Regular exports**: Keep Cockatrice collection updated
- **Backup decks**: Save important .cod files separately

#### **Discovery**
- **Format filtering**: Start with your preferred format
- **Search combinations**: Use format + search together
- **Release dates**: Sort by newest for recent products
- **Code lookup**: Search by set codes for specific products

### Performance Optimization

#### **Network Efficiency**
- **Cache timing**: App handles cache automatically
- **Batch exports**: Select multiple decks at once
- **Stable connection**: Better network = faster detail loading
- **Peak hours**: Avoid very busy internet times if possible

#### **System Resources**
- **Close other apps**: More RAM for smooth operation
- **SSD recommended**: Faster cache access
- **Updated Python**: Latest Python version for best performance
- **Regular restarts**: Occasional app restart clears memory

---

## Getting Help

### Support Channels
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check technical docs for developer info
- **Community**: MTG and Cockatrice communities for gameplay help

### Reporting Issues
Include:
- **Error messages**: Full text of any errors
- **Steps to reproduce**: What you were doing when it happened
- **System info**: Windows version, Python version
- **Logs**: Any console output or error details

### Feature Requests
- **GitHub Issues**: Tag as enhancement
- **Detail use case**: Explain what you're trying to accomplish  
- **Format support**: Specify any missing formats or sources
- **Integration ideas**: Other tools or websites to support

---

*Last updated: November 2025*