# MTGJSON Migration Implementation Plan

## Overview

This document outlines the migration strategy from the current Moxfield-based precon fetching system to MTGJSON API integration. This migration will expand deck support from ~50 commander precons to thousands of preconstructed decks across all MTG formats while maintaining existing performance and user experience.

## Current System Analysis

### Existing Architecture
- **Source**: `src/importers/moxfield_scraper.py` - MoxfieldScraper class
- **Data Source**: WotC's Moxfield account (api2.moxfield.com)
- **Filtering**: Limited to "commanderprecon" format only
- **Caching**: 24-hour JSON file cache system
- **Integration**: `src/gui/app.py` with TreeView display and threading

### Current Limitations
- Only commander precons supported
- Dependent on external Moxfield account maintenance
- Limited to recent releases (~2014-present)
- No filtering options for users
- Single deck type support

## MTGJSON API Advantages

### Comprehensive Data Coverage
- **Deck Count**: Thousands of preconstructed decks
- **Historical Range**: Complete MTG history (1993-present)
- **Deck Types**: Commander, Theme, Intro, Challenger, Planechase, Archenemy, Duel, Secret Lair, and more
- **Rich Metadata**: Complete card details, pricing URLs, rulings, multi-language support

### API Structure Analysis
```
https://mtgjson.com/api/v5/
├── DeckList.json                    # Complete deck catalog with metadata
├── decks/
│   ├── AdaptiveEnchantment_C18.json # Individual deck files
│   ├── NatureSVengeance_C18.json
│   └── ... (thousands of decks)
└── [format].json                    # Format aggregations
```

### Deck Data Format
```json
{
  "code": "C18",
  "name": "Adaptive Enchantment",
  "releaseDate": "2018-08-10",
  "type": "Commander Deck",
  "commander": [
    {
      "name": "Estrid, the Masked",
      "manaCost": "{1}{G}{W}{U}",
      "colors": ["G", "W", "U"],
      "colorIdentity": ["G", "U", "W"]
    }
  ],
  "mainBoard": [
    {"name": "Sol Ring", "count": 1},
    {"name": "Command Tower", "count": 1},
    // ... 98 more cards
  ]
}
```

## Implementation Strategy

### Phase 1: Core Infrastructure
**Objective**: Create new MTGJSON data fetching foundation

#### 1.1 Create MTGJsonScraper Class
**File**: `src/importers/mtgjson_scraper.py`

```python
class MTGJsonScraper:
    def __init__(self):
        self.base_url = "https://mtgjson.com/api/v5/"
        self.cache_dir = "cache"
        self.cache_duration = 86400  # 24 hours
    
    def fetch_deck_list(self):
        """Fetch complete deck catalog from DeckList.json"""
        
    def fetch_deck_details(self, deck_file_name):
        """Fetch individual deck data"""
        
    def get_available_deck_types(self):
        """Extract unique deck types for filtering"""
        
    def filter_decks(self, deck_type=None, date_range=None, set_codes=None):
        """Apply user-defined filters to deck list"""
```

#### 1.2 Data Structure Mapping
**Current Moxfield Format** → **MTGJSON Format**
- `deck_name` → `name`
- `commander_info` → `commander[0].name`
- `card_count` → `sum(mainBoard[].count)`
- `deck_url` → Generated from filename pattern

#### 1.3 Cache System Update
- **DeckList Cache**: Store complete catalog (refreshed daily)
- **Individual Deck Cache**: Store fetched deck details (persistent)
- **Cache Structure**: 
  ```
  cache/
  ├── mtgjson_decklist.json
  ├── deck_details/
  │   ├── AdaptiveEnchantment_C18.json
  │   └── NatureSVengeance_C18.json
  └── cache_metadata.json
  ```

### Phase 2: Enhanced Filtering System
**Objective**: Implement comprehensive deck filtering capabilities

#### 2.1 Filter Categories
1. **Deck Type Filter**
   - Commander Deck
   - Theme Deck  
   - Intro Pack
   - Challenger Deck
   - Planechase Deck
   - Archenemy Deck
   - Duel Deck
   - Secret Lair Drop
   - Premium Deck

2. **Format Filter**
   - Standard
   - Modern
   - Legacy
   - Vintage
   - Commander
   - Historic

3. **Temporal Filter**
   - Release date ranges
   - Set code groups (C14-C23 for Commander series)

4. **Content Filter**
   - Commander color identity
   - Deck themes/archetypes

#### 2.2 Naming Convention Analysis
**Pattern Recognition for Smart Filtering**:
- `*_SLD` → Secret Lair Drops
- `*_C##` → Commander series (C14, C15, etc.)
- `*_DD#` → Duel Decks
- Set codes → Format identification

### Phase 3: GUI Integration
**Objective**: Update interface to support enhanced filtering

#### 3.1 Filter Controls (src/gui/app.py)
```python
# Add to existing GUI
self.deck_type_var = tk.StringVar(value="All Types")
self.deck_type_combo = ttk.Combobox(...)

self.date_range_frame = tk.Frame(...)
self.start_date_var = tk.StringVar()
self.end_date_var = tk.StringVar()

self.format_filter_var = tk.StringVar(value="All Formats")
```

#### 3.2 TreeView Updates
**Maintain existing structure**, enhance with additional columns:
- Current: Name, Commander, Cards, Status
- Enhanced: Name, Commander, Cards, Type, Release Date, Status

#### 3.3 Threading Preservation
**Keep existing non-blocking patterns**:
- Background deck list fetching
- Individual deck detail loading
- Progress indication during operations

### Phase 4: Configuration Management
**Objective**: Persist user filter preferences

#### 4.1 Configuration File
**File**: `config/user_preferences.json`
```json
{
  "filters": {
    "preferred_deck_types": ["Commander Deck", "Theme Deck"],
    "date_range": {
      "start": "2020-01-01",
      "end": "2024-12-31"
    },
    "auto_refresh": true,
    "cache_retention_days": 7
  }
}
```

#### 4.2 Settings UI
- Filter preference dialog
- Cache management options
- Data source selection (fallback to Moxfield if needed)

### Phase 5: Error Handling & Fallbacks
**Objective**: Ensure robust operation with graceful degradation

#### 5.1 Network Error Handling
- Retry logic for failed requests
- Offline mode using cached data
- User notification for connectivity issues

#### 5.2 Data Validation
- JSON schema validation for fetched data
- Corrupt cache detection and recovery
- Missing deck file handling

#### 5.3 Fallback Strategy
- Maintain Moxfield scraper as backup option
- Automatic fallback on MTGJSON unavailability
- User preference for primary data source

## Implementation Timeline

### Week 1: Infrastructure
- [ ] Create `MTGJsonScraper` class
- [ ] Implement basic deck list fetching
- [ ] Set up enhanced cache system
- [ ] Unit tests for core functionality

### Week 2: Filtering System
- [ ] Implement deck type categorization
- [ ] Add temporal and format filters
- [ ] Create filter persistence layer
- [ ] Integration testing

### Week 3: GUI Integration
- [ ] Add filter controls to main interface
- [ ] Update TreeView for additional metadata
- [ ] Implement filter application logic
- [ ] User experience testing

### Week 4: Polish & Deployment
- [ ] Error handling and fallback systems
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] Release preparation

## File Changes Required

### New Files
- `src/importers/mtgjson_scraper.py` - New data source implementation
- `src/utils/deck_filters.py` - Filter logic and utilities
- `config/user_preferences.json` - User setting persistence
- `tests/test_mtgjson_integration.py` - Comprehensive test suite

### Modified Files
- `src/gui/app.py` - GUI updates for filtering interface
- `src/core/deck_manager.py` - Integration with new scraper
- `main.py` - Configuration loading updates
- `requirements.txt` - Any new dependencies

### Deprecated Files
- `src/importers/moxfield_scraper.py` - Keep as fallback option

## Benefits Summary

### User Experience
- **Expanded Selection**: From ~50 to thousands of preconstructed decks
- **Better Discovery**: Comprehensive filtering and search capabilities
- **Historical Access**: Complete MTG precon history
- **Reliability**: Reduced dependency on external account maintenance

### Technical Improvements
- **Data Quality**: Official MTGJSON project with consistent updates
- **Performance**: Direct JSON access vs. web scraping
- **Maintainability**: Cleaner data structure and API
- **Extensibility**: Foundation for future enhancements

### Long-term Value
- **Future-Proofing**: Sustainable data source
- **Community Alignment**: Integration with established MTG data ecosystem
- **Feature Expansion**: Potential for advanced deck analysis
- **Scalability**: Support for growing precon catalog

## Risk Mitigation

### Technical Risks
- **MTGJSON Availability**: Implement fallback to Moxfield
- **Data Format Changes**: Version handling and migration logic
- **Performance Impact**: Efficient caching and lazy loading

### User Experience Risks  
- **Interface Complexity**: Gradual feature introduction
- **Data Overwhelming**: Smart defaults and progressive disclosure
- **Migration Confusion**: Clear communication and help documentation

## Success Metrics

### Functional Metrics
- [ ] All existing commander precons accessible
- [ ] 10x increase in available deck selection
- [ ] Filter response time < 1 second
- [ ] 24-hour cache effectiveness > 95%

### User Experience Metrics
- [ ] No increase in application startup time
- [ ] Backward compatibility with existing workflows
- [ ] Intuitive filter interface (user testing)
- [ ] Stable performance with large datasets

## Conclusion

This migration represents a significant enhancement to the CockatriceAssistant application, transforming it from a specialized commander precon tool to a comprehensive MTG preconstructed deck browser. The phased implementation approach ensures minimal disruption to existing users while providing substantial new value through expanded deck access and filtering capabilities.

The integration with MTGJSON positions the application within the established MTG data ecosystem and provides a sustainable foundation for future feature development and community engagement.