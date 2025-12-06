# Cockatrice Assistant# Cockatrice Assistant



A modern desktop application for importing official Magic: The Gathering preconstructed decks into Cockatrice with comprehensive format support and intelligent caching.A desktop application for importing official Magic: The Gathering Commander Preconstructed decks into Cockatrice and managing themes with intelligent version control.



**🎯 Features 2,571 official MTG preconstructed decks across all formats**  Built with Python + tkinter for maximum compatibility.

**⚡ Smart 24-hour caching system for blazing-fast performance**  

**🎨 Curated theme management with one-click installation**## Quick Start (Windows PowerShell)



Built with Python + tkinter for maximum compatibility across Windows, macOS, and Linux.1. Create a venv and activate it:



---```powershell

python -m venv .venv

## 🚀 Quick Start.\.venv\Scripts\Activate.ps1

```

### Windows (PowerShell)

```powershell2. Install dependencies:

# Clone and setup

git clone https://github.com/YourUsername/CockatriceAssistant```powershell

cd CockatriceAssistantpip install -r requirements.txt

```

# Create virtual environment  

python -m venv .venv3. Run the app:

.\.venv\Scripts\Activate.ps1

```powershell

# Install dependenciespython app.py

pip install -r requirements.txt```



# Run the application## Features

python -m src.gui.app

```### Decks Tab

- **Fetch Precons**: Downloads commander precon lists from Moxfield (currently uses drgualberto's collection of 11+ precons)

### macOS/Linux (Bash)- **Load .cod file**: Import existing Cockatrice deck files for editing

```bash- **Select All**: Select all available decks/cards for export

# Clone and setup- **Export Selected**: Create .cod files from selected items

git clone https://github.com/YourUsername/CockatriceAssistant- **Save Path**: Defaults to `C:\Users\dalle\AppData\Local\Cockatrice\Cockatrice\decks` but can be customized

cd CockatriceAssistant

### Template Tab

# Create virtual environment- Placeholder for downloading Cockatrice themes/templates from URLs

python3 -m venv .venv- Enter template URL and destination folder

source .venv/bin/activate- Click "Download Template" to save locally



# Install dependencies  ## How to Use

pip install -r requirements.txt

1. **For Precons from Moxfield**:

# Run the application   - Click "Fetch Precons" to download the list of commander precons

python -m src.gui.app   - Wait for the fetch to complete (shows success message)

```   - Select the precon decks you want to import

   - Click "Export Selected" to create .cod files

---

2. **For Local .cod Files**:

## ✨ Key Features   - Click "Load .cod file" to open an existing Cockatrice deck

   - Select individual cards or use "Select All"

### 📦 MTGJSON Integration   - Choose export destination and click "Export Selected"

- **2,571 Official Decks**: Complete catalog of MTG preconstructed decks

- **All Formats Supported**: Commander, Standard, Limited, Historic, Modern, Pioneer3. **Customize Save Location**:

- **Official Data Source**: Direct from Wizards of the Coast via MTGJSON   - Edit the save path or click "Browse" to choose a different folder

- **Smart Caching**: 24-hour intelligent cache system (6x faster loading)   - The app creates the directory if it doesn't exist



### 🔍 Advanced Deck Management## Technical Details

- **Format-Based Filtering**: Organize by 7 distinct MTG formats  - Uses Moxfield's public API to fetch deck lists and detailed card data

- **Real-Time Search**: Instant deck search across names, codes, and types- Converts Moxfield deck format to Cockatrice .cod XML format

- **Commander Support**: Proper sideboard placement and banner card handling- Preserves card quantities, set information, and collector numbers

- **Universal Import**: Support for multiple deck sources and formats- Handles both mainboard and sideboard cards

- Multi-threaded fetching to keep UI responsive

### 🎨 Theme Management

- **Curated Collection**: Hand-picked Cockatrice themes with previews## Future Improvements

- **One-Click Install**: Automated theme download and installation  - Add more precon sources beyond drgualberto's collection

- **Version Control**: Smart updates and conflict resolution- Drag/drop support for .cod files

- **Custom Themes**: Support for user-provided theme URLs- Bulk operations on multiple files

- Better error handling and progress indicators

### ⚡ Performance & UX- Integration with official Cockatrice theme downloads

- **Background Processing**: Non-blocking operations with progress indicators
- **Auto-Detection**: Automatic Cockatrice installation discovery
- **Offline Mode**: Works with cached data when internet unavailable
- **Cross-Platform**: Native support for Windows, macOS, and Linux

---

## 📊 Quick Stats

| Feature | Details |
|---------|---------|
| **Deck Collection** | 2,571 official MTG preconstructed decks |
| **Format Coverage** | Commander (198), Standard (197), Limited (453), Historic, Modern, Pioneer |
| **Performance** | 0.5s load time (cached) vs 3-5s (fresh) |
| **Theme Library** | 15+ curated themes with previews |
| **Platform Support** | Windows, macOS, Linux |
| **Cache System** | 24-hour intelligent refresh |

---

## 🎮 How to Use

### 1. Browse and Filter Decks
```
Launch App → Auto-loads 2,571 decks from cache/MTGJSON
↓
Filter by Format: Commander, Standard, Limited, etc.
↓  
Search by Name: Type to filter results instantly
↓
Select Decks: Choose one or multiple for import
```

### 2. Import to Cockatrice  
```
Select Target Decks → Click "Import Selected"
↓
Choose Destination: Auto-detects Cockatrice decks folder  
↓
Format Conversion: Universal format → Cockatrice .cod files
↓
Commander Handling: Commanders → Sideboard, Banner card set
```

### 3. Manage Themes
```
Themes Tab → Browse Curated Collection
↓
Preview Themes: See screenshots and descriptions
↓  
One-Click Install: Automatic download and setup
↓
Auto-Detection: Finds Cockatrice themes folder
```

---

## 🔧 Architecture

### Core Components
- **Multi-Platform Import**: Support for 4 major deck sources (MTGJSON, Moxfield, MTGGoldfish, Archidekt)
- **Universal Deck Format**: Standardized deck representation across all sources  
- **Smart Caching**: Intelligent 24-hour cache system for optimal performance
- **Plugin Architecture**: Extensible scraper system for seamless platform integration

### Data Pipeline
```
Deck Sources (MTGJSON/Moxfield/MTGGoldfish/Archidekt) → Universal Format → Cockatrice .cod
```

### Performance Features
- **Intelligent Caching**: 24-hour cache with validity checking
- **Threaded Operations**: Non-blocking network and file operations  
- **Lazy Loading**: Load deck details only when needed
- **Memory Efficiency**: Optimized for large deck collections

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[USER_GUIDE.md](docs/USER_GUIDE.md)** | Complete user manual with screenshots |
| **[TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md)** | Developer reference and API docs |
| **[CHANGELOG.md](docs/CHANGELOG.md)** | Version history and migration guides |

---

## 🛠️ Development

### Requirements
- **Python**: 3.8+ (3.9+ recommended)
- **Dependencies**: `tkinter`, `requests`, `lxml`, `pathlib`
- **Platform**: Windows, macOS, Linux

### Project Structure
```
src/
├── core/           # Application core (updater, version management)
├── gui/            # Main GUI application  
├── importers/      # Deck import system (MTGJSON, Universal format)
└── utils/          # Utilities (filters, themes, templates)

docs/               # Comprehensive documentation
cache/              # Smart cache storage (24h TTL)  
themes/             # Downloaded theme storage
```

### Contributing
1. **Issues**: Use GitHub issue templates for bugs/features
2. **Pull Requests**: Include tests and documentation updates
3. **Code Style**: Follow PEP 8 with type hints
4. **Testing**: Maintain 85%+ test coverage

---

## 🔄 Version 2.1.0 Highlights

### ✅ What's New
- **MTGJSON Integration**: Switched from Moxfield to official MTGJSON data
- **Smart Caching**: 24-hour intelligent cache system  
- **Format Filtering**: Replaced deck types with intuitive format categories
- **Commander Fixes**: Proper sideboard placement and banner card handling
- **Real-Time Search**: Live filtering as you type

### ⚡ Performance Improvements
- **6x Faster Loading**: Smart cache reduces startup time from 3-5s to 0.5s
- **Background Operations**: All network requests non-blocking
- **Memory Optimization**: Efficient handling of 2,571+ deck collection
- **Offline Support**: Full functionality with cached data

### 🎯 User Experience
- **Simplified Interface**: Removed unnecessary advanced filtering
- **Auto-Updates**: Cache refreshes automatically on startup when needed  
- **Better Search**: Instant results across multiple deck fields
- **Format Clarity**: Intuitive organization by MTG formats

---

## 🚀 Future Roadmap

### Version 2.2.0 (Planned)
- **Enhanced Search**: Filter by specific cards and mana costs
- **Deck Analysis**: Statistics and format legality checking
- **Collection Sync**: Integration with MTG collection tools
- **Bulk Operations**: Multi-deck export and batch processing

### Version 3.0.0 (Vision)  
- **Database Integration**: SQLite for advanced queries and performance
- **AI Features**: Machine learning deck recommendations
- **Mobile Companion**: iOS/Android app for deck browsing
- **Community Features**: Deck rating and sharing system

---

## 📞 Support

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/YourUsername/CockatriceAssistant/issues)
- **💡 Feature Requests**: [GitHub Discussions](https://github.com/YourUsername/CockatriceAssistant/discussions)  
- **📚 Documentation**: Complete guides in `/docs` folder
- **💬 Community**: [Discord Server](https://discord.gg/YourServer) for real-time help

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**⭐ Star this repository if Cockatrice Assistant helps improve your MTG experience!**