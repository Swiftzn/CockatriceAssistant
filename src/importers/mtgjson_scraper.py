"""
MTGJSON scraper for fetching preconstructed deck data.

This module provides functionality to fetch deck data from the MTGJSON API,
replacing the Moxfield-based system with a more comprehensive data source.
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import urllib.request
import urllib.error
from urllib.parse import urljoin


class MTGDeck:
    """Wrapper class for MTGJSON deck data to provide object-like access."""

    def __init__(self, deck_data: Dict[str, Any]):
        """Initialize from MTGJSON deck dictionary."""
        self._data = deck_data
        self.source = "MTGJSON"  # Mark as MTGJSON deck for GUI

    def __getattr__(self, name: str):
        """Allow attribute-style access to deck data."""
        if name in self._data:
            return self._data[name]
        # Map common attribute names
        attr_map = {
            "deckname": "name",
            "deck_name": "name",
        }
        if name in attr_map and attr_map[name] in self._data:
            return self._data[attr_map[name]]
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def to_cockatrice(self):
        """Convert MTGJSON deck to Cockatrice format."""
        from importers.deck_import import UniversalDeck, convert_universal_to_cockatrice
        from utils.deck_filters import DeckFilters

        # Get the scraper instance to fetch deck details
        scraper = MTGJsonScraper()

        # Fetch full deck details
        filename = getattr(self, "fileName", "") + ".json"
        deck_details = scraper.fetch_deck_details(filename)

        if not deck_details:
            # Raise an exception instead of creating empty deck
            raise Exception(
                f"Failed to fetch deck details from MTGJSON API for {self.name}. This may be due to a server outage or network issue. Please try again later."
            )

        data = deck_details.get("data", {})

        # Convert mainboard cards
        mainboard = []
        for card in data.get("mainBoard", []):
            mainboard.append(
                {
                    "name": card.get("name", ""),
                    "quantity": card.get("count", 1),
                    "set": card.get("setCode", ""),
                    "collector_number": card.get("number", ""),
                    "uuid": card.get("uuid", ""),
                }
            )

        # Convert sideboard cards
        sideboard = []
        for card in data.get("sideBoard", []):
            sideboard.append(
                {
                    "name": card.get("name", ""),
                    "quantity": card.get("count", 1),
                    "set": card.get("setCode", ""),
                    "collector_number": card.get("number", ""),
                    "uuid": card.get("uuid", ""),
                }
            )

        # Get commanders
        commanders = []
        for commander in data.get("commander", []):
            commanders.append(commander.get("name", ""))

        # Determine format
        filters = DeckFilters()
        deck_format = filters.infer_format(self._data).lower()

        # Create UniversalDeck
        universal_deck = UniversalDeck(
            name=self.name,
            url="",
            format=deck_format,
            description=f"MTGJSON deck from {self.code}",
            mainboard=mainboard,
            sideboard=sideboard,
            commanders=commanders,
        )

        # Convert to Cockatrice format
        return convert_universal_to_cockatrice(universal_deck)

    def __str__(self):
        return f"MTGDeck({self.name})"

    def __repr__(self):
        return f"MTGDeck(name='{self.name}', type='{self.type}', code='{self.code}')"


class MTGJsonScraper:
    """
    Scraper for fetching preconstructed deck data from MTGJSON API.

    Provides access to thousands of preconstructed decks across MTG history
    with comprehensive filtering and caching capabilities.
    """

    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize the MTGJSON scraper.

        Args:
            cache_dir: Directory to store cached data
        """
        self.base_url = "https://mtgjson.com/api/v5/"
        self.cache_dir = Path(cache_dir)
        self.cache_duration = 86400  # 24 hours in seconds

        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)
        (self.cache_dir / "deck_details").mkdir(exist_ok=True)

        # Cache file paths
        self.decklist_cache = self.cache_dir / "mtgjson_decklist.json"
        self.cache_metadata = self.cache_dir / "cache_metadata.json"

        # Initialize cache metadata
        self._init_cache_metadata()

    def _init_cache_metadata(self):
        """Initialize cache metadata file if it doesn't exist."""
        if not self.cache_metadata.exists():
            metadata = {
                "last_decklist_fetch": 0,
                "fetched_decks": {},
                "cache_version": "1.0",
            }
            with open(self.cache_metadata, "w") as f:
                json.dump(metadata, f, indent=2)

    def _load_cache_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from file."""
        try:
            with open(self.cache_metadata, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._init_cache_metadata()
            return self._load_cache_metadata()

    def _save_cache_metadata(self, metadata: Dict[str, Any]):
        """Save cache metadata to file."""
        with open(self.cache_metadata, "w") as f:
            json.dump(metadata, f, indent=2)

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cache timestamp is still valid."""
        return time.time() - timestamp < self.cache_duration

    def _fetch_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch JSON data from URL with error handling.

        Args:
            url: URL to fetch data from

        Returns:
            Parsed JSON data

        Raises:
            Exception: If fetch fails after retries
        """
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(url, timeout=30) as response:
                    data = response.read().decode("utf-8")
                    return json.loads(data)
            except (
                urllib.error.URLError,
                urllib.error.HTTPError,
                json.JSONDecodeError,
            ) as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to fetch data from {url}: {e}")
                time.sleep(retry_delay * (2**attempt))  # Exponential backoff

        raise Exception(f"Failed to fetch data from {url} after {max_retries} attempts")

    def fetch_deck_list(self, force_refresh: bool = False) -> List[MTGDeck]:
        """
        Fetch the complete deck catalog from MTGJSON.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            List of deck metadata dictionaries
        """
        metadata = self._load_cache_metadata()

        # Check if we need to fetch fresh data
        if not force_refresh and self._is_cache_valid(metadata["last_decklist_fetch"]):
            if self.decklist_cache.exists():
                try:
                    with open(self.decklist_cache, "r", encoding="utf-8") as f:
                        deck_data = json.load(f)
                        return [MTGDeck(deck) for deck in deck_data]
                except (FileNotFoundError, json.JSONDecodeError):
                    pass  # Fall through to fetch fresh data

        # Fetch fresh deck list
        print("Fetching deck list from MTGJSON...")
        url = urljoin(self.base_url, "DeckList.json")

        try:
            response_data = self._fetch_url(url)
            deck_list = response_data.get("data", [])

            # Cache the results
            with open(self.decklist_cache, "w", encoding="utf-8") as f:
                json.dump(deck_list, f, indent=2, ensure_ascii=False)

            # Update metadata
            metadata["last_decklist_fetch"] = time.time()
            self._save_cache_metadata(metadata)

            print(f"Successfully cached {len(deck_list)} decks")
            return [MTGDeck(deck) for deck in deck_list]

        except Exception as e:
            print(f"Error fetching deck list: {e}")
            # Try to return cached data if available
            if self.decklist_cache.exists():
                try:
                    with open(self.decklist_cache, "r", encoding="utf-8") as f:
                        print("Using cached deck list due to fetch error")
                        deck_data = json.load(f)
                        return [MTGDeck(deck) for deck in deck_data]
                except (FileNotFoundError, json.JSONDecodeError):
                    pass

            raise Exception(
                f"Failed to fetch deck list and no valid cache available: {e}"
            )

    def fetch_deck_details(
        self, deck_filename: str, force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific deck.

        Args:
            deck_filename: Filename of the deck (e.g., "AdaptiveEnchantment_C18.json")
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Deck details dictionary or None if not found
        """
        cache_file = self.cache_dir / "deck_details" / deck_filename
        metadata = self._load_cache_metadata()

        # Check cache first (deck details are cached indefinitely unless forced)
        if not force_refresh and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass  # Fall through to fetch fresh data

        # Fetch fresh deck details
        url = urljoin(self.base_url, f"decks/{deck_filename}")

        try:
            deck_data = self._fetch_url(url)

            # Cache the results
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(deck_data, f, indent=2, ensure_ascii=False)

            # Update metadata
            metadata["fetched_decks"][deck_filename] = time.time()
            self._save_cache_metadata(metadata)

            return deck_data

        except Exception as e:
            print(f"Error fetching deck details for {deck_filename}: {e}")
            return None

    def get_available_deck_types(self) -> List[str]:
        """
        Get list of all available deck types from the cached deck list.

        Returns:
            Sorted list of unique deck types
        """
        try:
            deck_list = self.fetch_deck_list()
            deck_types = set()

            for deck in deck_list:
                deck_type = getattr(deck, "type", "Unknown")
                deck_types.add(deck_type)

            return sorted(deck_types)

        except Exception as e:
            print(f"Error getting deck types: {e}")
            return []

    def filter_decks(
        self,
        deck_list: Optional[List[Dict[str, Any]]] = None,
        deck_types: Optional[List[str]] = None,
        date_range: Optional[Tuple[str, str]] = None,
        set_codes: Optional[List[str]] = None,
        name_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter decks based on various criteria.

        Args:
            deck_list: List of decks to filter (if None, fetches current list)
            deck_types: List of deck types to include (e.g., ["Commander Deck"])
            date_range: Tuple of (start_date, end_date) in YYYY-MM-DD format
            set_codes: List of set codes to include (e.g., ["C18", "C19"])
            name_filter: String to search for in deck names (case-insensitive)

        Returns:
            Filtered list of decks
        """
        if deck_list is None:
            deck_list = self.fetch_deck_list()

        filtered_decks = deck_list.copy()

        # Filter by deck types
        if deck_types:
            filtered_decks = [
                deck
                for deck in filtered_decks
                if getattr(deck, "type", "") in deck_types
            ]

        # Filter by date range
        if date_range:
            start_date, end_date = date_range
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")

                filtered_decks = [
                    deck
                    for deck in filtered_decks
                    if self._is_deck_in_date_range(deck, start_dt, end_dt)
                ]
            except ValueError as e:
                print(f"Invalid date format: {e}")

        # Filter by set codes
        if set_codes:
            filtered_decks = [
                deck
                for deck in filtered_decks
                if getattr(deck, "code", "") in set_codes
            ]

        # Filter by name
        if name_filter:
            name_filter_lower = name_filter.lower()
            filtered_decks = [
                deck
                for deck in filtered_decks
                if name_filter_lower in getattr(deck, "name", "").lower()
            ]

        return filtered_decks

    def _is_deck_in_date_range(
        self, deck: Dict[str, Any], start_date: datetime, end_date: datetime
    ) -> bool:
        """Check if deck release date falls within the specified range."""
        release_date_str = getattr(deck, "releaseDate", "")
        if not release_date_str:
            return False

        try:
            release_date = datetime.strptime(release_date_str, "%Y-%m-%d")
            return start_date <= release_date <= end_date
        except ValueError:
            return False

    def get_deck_summary(self, deck_metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert MTGJSON deck metadata to format expected by GUI.

        Args:
            deck_metadata: Deck metadata from MTGJSON

        Returns:
            Dictionary with standardized deck information for GUI display
        """
        return {
            "name": deck_metadata.get("name", "Unknown Deck"),
            "code": deck_metadata.get("code", ""),
            "type": deck_metadata.get("type", "Unknown"),
            "release_date": deck_metadata.get("releaseDate", ""),
            "filename": deck_metadata.get("fileName", "") + ".json",
        }

    def get_preconstructed_decks(
        self, deck_types: Optional[List[str]] = None, limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get a list of preconstructed decks with basic information.

        This method provides compatibility with the existing GUI interface
        while offering the enhanced filtering capabilities of MTGJSON.

        Args:
            deck_types: List of deck types to include (defaults to Commander Deck)
            limit: Maximum number of decks to return

        Returns:
            List of deck summaries compatible with existing GUI format
        """
        try:
            # Default to Commander Decks for backward compatibility
            if deck_types is None:
                deck_types = ["Commander Deck"]

            deck_list = self.fetch_deck_list()
            filtered_decks = self.filter_decks(deck_list, deck_types=deck_types)

            # Sort by release date (newest first)
            filtered_decks.sort(
                key=lambda x: getattr(x, "releaseDate", ""), reverse=True
            )

            # Apply limit if specified
            if limit:
                filtered_decks = filtered_decks[:limit]

            # Convert to GUI format
            return [self.get_deck_summary(deck._data) for deck in filtered_decks]

        except Exception as e:
            print(f"Error fetching preconstructed decks: {e}")
            return []

    def clear_cache(self):
        """Clear all cached data."""
        try:
            # Remove cached files
            if self.decklist_cache.exists():
                self.decklist_cache.unlink()

            # Clear deck details cache
            deck_details_dir = self.cache_dir / "deck_details"
            if deck_details_dir.exists():
                for file in deck_details_dir.glob("*.json"):
                    file.unlink()

            # Reset metadata
            self._init_cache_metadata()
            print("Cache cleared successfully")

        except Exception as e:
            print(f"Error clearing cache: {e}")


# Compatibility function for existing code
def get_mtgjson_precons(
    deck_types: Optional[List[str]] = None, limit: Optional[int] = None
) -> List[Dict[str, str]]:
    """
    Convenience function to get preconstructed decks from MTGJSON.

    Args:
        deck_types: List of deck types to include
        limit: Maximum number of decks to return

    Returns:
        List of deck summaries
    """
    scraper = MTGJsonScraper()
    return scraper.get_preconstructed_decks(deck_types=deck_types, limit=limit)


if __name__ == "__main__":
    # Basic testing functionality
    print("Testing MTGJSON Scraper...")

    scraper = MTGJsonScraper()

    # Test deck list fetching
    print("\n1. Fetching deck list...")
    deck_list = scraper.fetch_deck_list()
    print(f"Found {len(deck_list)} total decks")

    # Test deck type filtering
    print("\n2. Available deck types:")
    deck_types = scraper.get_available_deck_types()
    for deck_type in deck_types[:10]:  # Show first 10
        print(f"  - {deck_type}")
    if len(deck_types) > 10:
        print(f"  ... and {len(deck_types) - 10} more")

    # Test commander deck filtering
    print("\n3. Commander decks (last 10):")
    commander_decks = scraper.get_preconstructed_decks(
        deck_types=["Commander Deck"], limit=10
    )
    for deck in commander_decks:
        print(f"  - {deck['name']} ({deck['code']}) - {deck['release_date']}")

    # Test individual deck fetching
    if commander_decks:
        print(f"\n4. Fetching details for: {commander_decks[0]['name']}")
        details = scraper.fetch_deck_details(commander_decks[0]["filename"])
        if details:
            print(f"   Deck has {len(details.get('mainBoard', []))} cards in mainboard")
            commanders = details.get("commander", [])
            if commanders:
                print(f"   Commander: {commanders[0].get('name', 'Unknown')}")
        else:
            print("   Failed to fetch deck details")
