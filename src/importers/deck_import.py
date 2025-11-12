"""deck_import.py

Universal deck import module that supports multiple deck list websites.
Automatically detects the source and applies the appropriate scraping logic.
"""

import re
from urllib.parse import urlparse
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import sys
from pathlib import Path

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.deck_parser import CockatriceDeck, CardEntry


@dataclass
class UniversalDeck:
    """Universal deck representation that can be converted to Cockatrice format."""

    name: str
    url: str
    format: str = ""  # commander, standard, modern, etc.
    description: str = ""
    year: str = ""
    mainboard: List[Dict[str, Any]] = None
    sideboard: List[Dict[str, Any]] = None
    commanders: List[str] = None

    def __post_init__(self):
        if self.mainboard is None:
            self.mainboard = []
        if self.sideboard is None:
            self.sideboard = []
        if self.commanders is None:
            self.commanders = []


class DeckScraper(ABC):
    """Abstract base class for deck scrapers."""

    @abstractmethod
    def can_handle_url(self, url: str) -> bool:
        """Check if this scraper can handle the given URL."""
        pass

    @abstractmethod
    def fetch_deck(self, url: str) -> Optional[UniversalDeck]:
        """Fetch deck data from the URL."""
        pass

    @abstractmethod
    def get_site_name(self) -> str:
        """Get the display name of this site."""
        pass


def clean_card_name(name: str) -> str:
    """Clean card name for Cockatrice compatibility.

    Handles dual-faced cards by taking the first name before '//'

    Args:
        name: Raw card name from any source

    Returns:
        Cleaned card name suitable for Cockatrice
    """
    if not name:
        return ""

    # Handle dual-faced cards - take the first name before '//'
    if "//" in name:
        return name.split("//")[0].strip()

    return name.strip()


def detect_deck_format(deck: UniversalDeck) -> str:
    """Detect deck format based on commanders and card count."""
    # If there are commanders, it's likely a commander deck
    if deck.commanders:
        return "commander"

    # Check mainboard size for other formats
    mainboard_count = sum(card.get("quantity", 1) for card in deck.mainboard)

    if mainboard_count == 60:
        return "standard"  # Could also be modern, legacy, etc.
    elif mainboard_count == 100:
        return "commander"  # EDH without explicit commanders

    # Default to the format specified in the deck
    return deck.format.lower() if deck.format else "unknown"


def convert_universal_to_cockatrice(universal_deck: UniversalDeck) -> CockatriceDeck:
    """Convert a UniversalDeck to a CockatriceDeck for .cod export."""

    def make_card_entries(card_list: List[Dict[str, Any]]) -> List[CardEntry]:
        entries = []
        for card in card_list:
            # Clean the card name to handle dual-faced cards
            raw_name = card.get("name", "")
            clean_name = clean_card_name(raw_name)

            entry = CardEntry(
                number=card.get("quantity", 1),
                name=clean_name,
                setShortName=card.get("set", ""),
                collectorNumber=card.get("collector_number", ""),
                uuid=card.get("scryfall_id", ""),
            )
            entries.append(entry)
        return entries

    # Detect format to determine sideboard handling
    deck_format = detect_deck_format(universal_deck)

    # Start with mainboard
    main_entries = make_card_entries(universal_deck.mainboard)
    side_entries = make_card_entries(universal_deck.sideboard)
    banner_card = ""

    # Handle commanders based on format
    if deck_format == "commander" or universal_deck.commanders:
        # For commander decks, put commanders in sideboard
        for commander in universal_deck.commanders:
            if commander.strip():
                commander_name = clean_card_name(commander)
                entry = CardEntry(
                    number=1,
                    name=commander_name,
                    setShortName="",
                    collectorNumber="",
                    uuid="",
                )
                side_entries.append(entry)

                # Set the first commander as the banner card
                if not banner_card:
                    banner_card = commander_name
    else:
        # For non-commander decks, set banner card to a random card from mainboard
        if universal_deck.mainboard:
            import random

            random_card = random.choice(universal_deck.mainboard)
            banner_card = clean_card_name(random_card.get("name", ""))

    cockatrice_deck = CockatriceDeck(
        deckname=universal_deck.name,
        zone_main=main_entries,
        zone_side=side_entries,
        banner_card=banner_card,
    )

    return cockatrice_deck


class DeckImportManager:
    """Manager class that coordinates different deck scrapers."""

    def __init__(self):
        self.scrapers: List[DeckScraper] = []

    def register_scraper(self, scraper: DeckScraper):
        """Register a new deck scraper."""
        self.scrapers.append(scraper)

    def get_scraper_for_url(self, url: str) -> Optional[DeckScraper]:
        """Find the appropriate scraper for a given URL."""
        for scraper in self.scrapers:
            if scraper.can_handle_url(url):
                return scraper
        return None

    def get_supported_sites(self) -> List[str]:
        """Get list of supported site names."""
        return [scraper.get_site_name() for scraper in self.scrapers]

    def fetch_deck(self, url: str) -> Optional[UniversalDeck]:
        """Fetch a deck from any supported URL."""
        scraper = self.get_scraper_for_url(url)
        if not scraper:
            return None

        return scraper.fetch_deck(url)

    def is_supported_url(self, url: str) -> Tuple[bool, str]:
        """Check if URL is supported and return the site name."""
        scraper = self.get_scraper_for_url(url)
        if scraper:
            return True, scraper.get_site_name()
        return False, ""


# Global instance
deck_import_manager = DeckImportManager()
