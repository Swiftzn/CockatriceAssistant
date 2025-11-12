"""moxfield_import.py

Moxfield scraper adapter for the universal deck import system.
"""

import re
import sys
from pathlib import Path
from typing import Optional

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from importers.deck_import import DeckScraper, UniversalDeck
from importers.moxfield_scraper import MoxfieldScraper


class MoxfieldImportScraper(DeckScraper):
    """Moxfield scraper that implements the universal deck import interface."""

    def __init__(self):
        self.moxfield_scraper = MoxfieldScraper()

    def can_handle_url(self, url: str) -> bool:
        """Check if this scraper can handle the given URL."""
        return "moxfield.com" in url.lower()

    def get_site_name(self) -> str:
        """Get the display name of this site."""
        return "Moxfield"

    def fetch_deck(self, url: str) -> Optional[UniversalDeck]:
        """Fetch deck data from a Moxfield URL."""
        try:
            # Extract deck ID from URL
            deck_id = url.split("/")[-1].split("?")[0]  # Handle query params

            # Fetch deck using existing Moxfield scraper
            moxfield_deck = self.moxfield_scraper.fetch_deck_details(deck_id)
            if not moxfield_deck:
                return None

            # Convert to UniversalDeck format
            universal_deck = UniversalDeck(
                name=moxfield_deck.name,
                url=moxfield_deck.url,
                format=moxfield_deck.format,
                description=moxfield_deck.description,
                year=moxfield_deck.year,
                mainboard=moxfield_deck.mainboard,
                sideboard=moxfield_deck.sideboard,
                commanders=moxfield_deck.commanders,
            )

            return universal_deck

        except Exception as e:
            print(f"Error fetching Moxfield deck: {e}")
            return None
