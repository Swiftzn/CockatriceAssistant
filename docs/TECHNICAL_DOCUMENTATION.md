# Cockatrice Assistant - Technical Documentation

## Architecture Overview

Cockatrice Assistant is a Python desktop application built with tkinter that integrates with the MTGJSON API to provide comprehensive Magic: The Gathering preconstructed deck importing capabilities.

### Core Components

```
src/
├── core/
│   ├── deck_parser.py          # Cockatrice .cod file handling
│   ├── updater.py              # Application update system
│   └── version.py              # Version management
├── gui/
│   └── app.py                  # Main GUI application
├── importers/
│   ├── mtgjson_scraper.py      # MTGJSON API integration
│   ├── deck_import.py          # Universal deck import system
│   └── deck_import_init.py     # Scraper initialization
└── utils/
    ├── deck_filters.py         # Deck filtering and categorization
    └── templates.py            # Theme management system
```

---

## Data Flow Architecture

### 1. **MTGJSON Integration**

#### **API Structure**
```
MTGJSON API v5 (https://mtgjson.com/api/v5/)
├── DeckList.json               # Catalog of all decks (2,571 entries)
└── decks/{filename}.json       # Individual deck details
```

#### **Data Pipeline**
```python
MTGJsonScraper
├── fetch_deck_list()          # Main catalog with caching
├── fetch_deck_details()       # Individual deck on-demand  
├── get_available_deck_types()  # Type enumeration
└── _is_cache_valid()          # Smart cache management
```

#### **Caching System**
```
cache/
├── mtgjson_decklist.json      # Main catalog cache (24h TTL)
├── cache_metadata.json        # Timestamp and management data
└── deck_details/              # Individual deck cache (permanent)
    ├── {DeckName}_{Code}.json
    └── ...
```

### 2. **Deck Processing Pipeline**

#### **Format Detection**
```python
# utils/deck_filters.py
DeckFilters.infer_format(deck_data) → Format
├── Commander: deck.type == "Commander Deck" OR commanders present
├── Standard: deck.type in ["Intro Pack", "Challenger Deck"]  
├── Limited: deck.type in ["Jumpstart", "Draft"]
├── Historic: deck.type in ["Arena Starter", "Arena Promotional"]
└── Unknown: fallback category
```

#### **Conversion Process**
```python
MTGDeck → UniversalDeck → CockatriceDeck → .cod file
     ↓           ↓              ↓            ↓
  MTGJSON    Normalized    Cockatrice    XML File
   Format     Format       Format      on Disk
```

### 3. **GUI Architecture**

#### **Main Application Flow**
```python
MainWindow.__init__()
├── Create UI components
├── Initialize scrapers and filters  
├── Schedule load_initial_decks() 
└── Start tkinter mainloop

load_initial_decks()
├── Check cache validity (24h)
├── Use cache OR fetch fresh data
├── Update GUI in main thread
└── Enable user interaction
```

#### **Threading Strategy**
- **Main Thread**: GUI updates, user interaction
- **Background Threads**: Network operations, data processing
- **Synchronization**: `root.after()` for thread-safe GUI updates

---

## Key Classes and Methods

### MTGJsonScraper

#### **Core Methods**
```python
class MTGJsonScraper:
    def __init__(self, cache_dir="cache"):
        # Initialize with 24-hour cache duration
        
    def fetch_deck_list(self, force_refresh=False) -> List[MTGDeck]:
        # Smart caching: use cache if < 24h old, else refresh
        
    def fetch_deck_details(self, filename: str) -> Dict:
        # On-demand detail fetching with permanent caching
        
    def get_available_deck_types(self) -> List[str]:
        # Extract unique deck types from catalog
```

#### **MTGDeck Class**
```python
class MTGDeck:
    def __init__(self, deck_data: Dict):
        self._data = deck_data
        
    def to_cockatrice(self) -> CockatriceDeck:
        # Convert MTGJSON format to Cockatrice .cod format
        # Handles commander placement, banner cards, format detection
```

### Deck Conversion System

#### **Universal Format**
```python
@dataclass
class UniversalDeck:
    name: str
    format: str = ""
    mainboard: List[Dict] = None
    sideboard: List[Dict] = None  
    commanders: List[str] = None
```

#### **Cockatrice Format**
```python
@dataclass  
class CockatriceDeck:
    deckname: str
    zone_main: List[CardEntry] = field(default_factory=list)
    zone_side: List[CardEntry] = field(default_factory=list)
    banner_card: str = ""
```

#### **Conversion Logic**
```python
def convert_universal_to_cockatrice(universal_deck: UniversalDeck) -> CockatriceDeck:
    # Format-aware conversion:
    if deck_format == "commander":
        # Place commanders in sideboard
        # Set first commander as banner card
    else:
        # All cards in main deck
        # Random card as banner
```

### Filtering and Search

#### **DeckFilters Class**
```python
class DeckFilters:
    # Format inference based on type and naming patterns
    def infer_format(self, deck_data: Dict) -> str
    
    # Deck categorization for UI grouping  
    def categorize_deck_type(self, deck_type: str) -> str
    
    # Era classification for historical filtering
    def get_era_from_date(self, release_date: str) -> str
```

#### **AdvancedDeckFilter Class**
```python
class AdvancedDeckFilter:
    def multi_filter(self, categories=None, formats=None, **kwargs) -> List[MTGDeck]:
        # Complex filtering with multiple criteria
        
    def search_decks(self, query: str, fields=None) -> List[MTGDeck]:
        # Text search across multiple fields
```

---

## Implementation Details

### Smart Cache Management

#### **Cache Validation Logic**
```python
def _is_cache_valid(self, timestamp: float) -> bool:
    return time.time() - timestamp < self.cache_duration  # 24 hours

def load_initial_decks(self):
    metadata = self.mtgjson_scraper._load_cache_metadata()
    cache_is_valid = self.mtgjson_scraper._is_cache_valid(
        metadata.get("last_decklist_fetch", 0)
    )
    
    if cache_is_valid:
        # Fast path: use cache
        decks = self.mtgjson_scraper.fetch_deck_list(force_refresh=False)
    else:
        # Update path: fetch fresh data  
        decks = self.mtgjson_scraper.fetch_deck_list(force_refresh=True)
```

#### **Performance Characteristics**
- **Cache Hit**: ~0.5s load time, no network usage
- **Cache Miss**: ~3-5s load time, 2MB download
- **Offline Mode**: Uses stale cache with warning message

### Format-Aware Deck Handling

#### **Commander Deck Processing**
```python
# Special handling for Commander decks
if deck_format == "commander" or universal_deck.commanders:
    # Extract commanders from MTGJSON data
    commanders = [cmd.get('name') for cmd in data.get('commander', [])]
    
    # Place in sideboard for Cockatrice compatibility
    for commander in commanders:
        side_entries.append(CardEntry(number=1, name=commander))
    
    # Set first commander as banner card
    if commanders:
        banner_card = commanders[0]
```

#### **Non-Commander Processing**  
```python
# Standard deck handling
if not commanders:
    # All cards go to main deck
    main_entries = convert_cards(universal_deck.mainboard)
    
    # Random banner selection for visual appeal
    if universal_deck.mainboard:
        random_card = random.choice(universal_deck.mainboard)
        banner_card = clean_card_name(random_card.get('name'))
```

### GUI State Management

#### **Threaded Operations**
```python
def operation_with_threading(self):
    # Disable UI elements
    self.button.config(state="disabled")
    self.status_bar.config(text="Processing...")
    
    def background_work():
        try:
            # Heavy lifting here
            result = expensive_operation()
            
            # Update GUI in main thread
            self.root.after(0, lambda: self.update_gui(result))
        except Exception as e:
            self.root.after(0, lambda: self.handle_error(e))
        finally:
            # Re-enable UI
            self.root.after(0, lambda: self.button.config(state="normal"))
    
    threading.Thread(target=background_work, daemon=True).start()
```

#### **Search Implementation**
```python
def on_search_changed(self, event=None):
    """Real-time search as user types"""
    self.apply_mtgjson_filters()  # Triggers immediate re-filtering

def apply_mtgjson_filters(self):
    """Combine format filter + search"""
    filtered_decks = self.precon_decks.copy()
    
    # Format filtering
    format_filter = self.format_var.get()
    if format_filter != "All Formats":
        filtered_decks = [d for d in filtered_decks 
                         if self.deck_filters.infer_format(d._data) == format_filter]
    
    # Text search  
    search_term = self.search_var.get().strip().lower()
    if search_term:
        filtered_decks = [d for d in filtered_decks if 
                         search_term in d.name.lower() or
                         search_term in d.code.lower() or  
                         search_term in d.type.lower()]
    
    self._display_filtered_decks(filtered_decks)
```

---

## API Integration

### MTGJSON API Details

#### **Endpoints Used**
- **DeckList.json**: Complete catalog (~2MB, 2,571 decks)
- **decks/{filename}.json**: Individual deck details (~50-100KB each)

#### **Rate Limiting**
- No explicit rate limits documented
- Conservative approach: batch requests, cache aggressively
- Exponential backoff on failures

#### **Error Handling**
```python
def _fetch_url(self, url: str) -> Dict[str, Any]:
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed to fetch data from {url}: {e}")
            time.sleep(retry_delay * (2**attempt))  # Exponential backoff
```

### Universal Import System

#### **Multi-Site Support**
```python
class DeckImportManager:
    def __init__(self):
        self.scrapers = []  # Pluggable scraper architecture
    
    def register_scraper(self, scraper: DeckScraper):
        # Add new site support dynamically
    
    def fetch_deck(self, url: str) -> Optional[UniversalDeck]:
        scraper = self.get_scraper_for_url(url)
        return scraper.fetch_deck(url) if scraper else None
```

#### **Site Integration Examples**
```python
# Moxfield integration
class MoxfieldScraper(DeckScraper):
    def can_handle_url(self, url: str) -> bool:
        return "moxfield.com" in url
    
    def fetch_deck(self, url: str) -> UniversalDeck:
        # Moxfield-specific parsing logic
        
# MTGGoldfish integration  
class MTGGoldfishScraper(DeckScraper):
    def can_handle_url(self, url: str) -> bool:
        return "mtggoldfish.com" in url
```

---

## Configuration and Customization

### Application Settings

#### **Default Paths**
```python
# Auto-detection logic for Cockatrice paths
def get_default_cockatrice_decks_path():
    user_home = Path.home()
    possible_paths = [
        user_home / "AppData/Local/Cockatrice/Cockatrice/decks",  # Windows
        user_home / ".local/share/Cockatrice/decks",              # Linux
        user_home / "Library/Application Support/Cockatrice/decks"  # macOS
    ]
```

#### **Cache Configuration**
```python
class MTGJsonScraper:
    def __init__(self, cache_dir="cache"):
        self.cache_duration = 86400  # 24 hours in seconds
        self.cache_dir = Path(cache_dir)
        # Configurable cache location and duration
```

### Theme System

#### **Curated Themes**
```python
# Remote theme management
CURATED_THEMES_URL = "https://gist.githubusercontent.com/.../themes.json"

def get_curated_themes() -> List[CockatriceTheme]:
    # Fetch, parse, and validate theme definitions
    # Handle versioning and update detection
```

#### **Custom Theme Installation**
```python
def download_and_install_theme(theme: CockatriceTheme, themes_folder: str):
    # Download ZIP from URL
    # Extract to themes folder  
    # Validate theme structure
    # Handle conflicts and updates
```

---

## Testing and Quality Assurance

### Test Coverage Areas

#### **Core Functionality**
- MTGJSON API integration and parsing
- Deck conversion accuracy (Commander vs non-Commander)
- Cache validity and management
- Format detection and filtering
- Search functionality

#### **Integration Testing**  
- GUI thread safety and responsiveness
- File I/O operations and permissions
- Network failure handling and fallbacks
- Cross-platform path handling

#### **Performance Testing**
- Cache hit/miss performance
- Large dataset filtering speed  
- Memory usage with many decks
- GUI responsiveness during operations

### Development Tools

#### **Manual Testing Scripts**
```python
# Test deck conversion
def test_commander_conversion():
    scraper = MTGJsonScraper()
    decks = scraper.fetch_deck_list()
    commander_deck = next(d for d in decks if d.type == 'Commander Deck')
    
    cockatrice_deck = commander_deck.to_cockatrice()
    
    assert cockatrice_deck.banner_card  # Banner card set
    assert len(cockatrice_deck.zone_side) > 0  # Commander in sideboard
    assert cockatrice_deck.banner_card in [c.name for c in cockatrice_deck.zone_side]
```

#### **Performance Profiling**
```python
import time
import cProfile

def profile_cache_performance():
    scraper = MTGJsonScraper()
    
    # Cold start (no cache)
    start = time.time()
    decks = scraper.fetch_deck_list(force_refresh=True)
    cold_time = time.time() - start
    
    # Warm start (with cache)
    start = time.time()
    decks = scraper.fetch_deck_list(force_refresh=False)  
    warm_time = time.time() - start
    
    print(f"Cold start: {cold_time:.2f}s, Warm start: {warm_time:.2f}s")
```

---

## Deployment and Distribution

### Build System

#### **PyInstaller Configuration**
```python
# main.spec for executable generation
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('src', 'src')],  # Include source in bundle
    hiddenimports=['tkinter', 'lxml'],
    hookspath=[],
    runtime_hooks=[], 
    excludes=[],
)
```

#### **Release Process**
1. Update version in `src/core/version.py`
2. Generate executable with PyInstaller
3. Create GitHub release with changelog
4. Update auto-updater endpoint
5. Test update mechanism

### Auto-Update System

#### **Update Detection**
```python
def check_for_updates(use_cache=True) -> Dict:
    # GitHub API integration for release checking
    # Version comparison logic
    # Download URL discovery
    # Release notes extraction
```

#### **Update Installation**
```python
def install_update(update_path: Path, install_dir: Path) -> bool:
    # Backup current installation
    # Extract new version
    # Replace executable
    # Restart application
```

---

## Future Architecture Considerations

### Scalability Improvements

#### **Database Integration**
- Consider SQLite for complex filtering operations
- Improve search performance with indexed fields
- Enable offline advanced queries

#### **Plugin Architecture**  
- Modular scraper system for new deck sources
- User-defined filter plugins
- Custom export format plugins

### Performance Optimizations

#### **Lazy Loading**
- Load deck details only when needed
- Progressive UI updates for large datasets
- Background detail pre-fetching

#### **Caching Enhancements**
- Intelligent cache warming
- Partial cache updates
- Cache compression for storage efficiency

### User Experience Improvements

#### **Advanced Features**
- Deck comparison tools
- Collection management  
- Wishlist and favorites
- Deck statistics and analysis

#### **Integration Opportunities**
- Scryfall API for card images and prices
- EDHRec integration for Commander recommendations  
- Direct Cockatrice integration via automation

---

*Last updated: November 2025*