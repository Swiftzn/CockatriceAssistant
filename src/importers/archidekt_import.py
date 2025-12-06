"""archidekt_import.py

Module to import decks from Archidekt.com using their API.
Supports importing public decks by URL.
"""

import requests
import json
import re
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from importers.deck_import import DeckScraper, UniversalDeck


class ArchidektImportScraper(DeckScraper):
    """Archidekt scraper that implements the universal deck import interface."""

    def can_handle_url(self, url: str) -> bool:
        """Check if this scraper can handle the given URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower() in ["archidekt.com", "www.archidekt.com"]
        except Exception:
            return False

    def get_site_name(self) -> str:
        """Get the display name of this site."""
        return "Archidekt"

    def fetch_deck(self, url: str) -> Optional[UniversalDeck]:
        """Fetch deck data from Archidekt URL."""
        try:
            # Extract deck ID from URL
            deck_id = self._extract_deck_id(url)
            if not deck_id:
                raise ValueError("Could not extract deck ID from URL")

            # Fetch deck data from Archidekt API
            api_url = f"https://archidekt.com/api/decks/{deck_id}/"
            deck_data = self._fetch_deck_data(api_url)

            if not deck_data:
                raise ValueError("Failed to fetch deck data from Archidekt API")

            # Parse the deck data
            universal_deck = self._parse_deck_data(deck_data, url)
            return universal_deck

        except Exception as e:
            print(f"Error fetching Archidekt deck: {e}")
            return None

    def _extract_deck_id(self, url: str) -> Optional[str]:
        """Extract deck ID from Archidekt URL."""
        try:
            # Archidekt URLs format: https://archidekt.com/decks/10029246/shanna_lifegain_v2
            # We need to extract the numeric ID (10029246)
            pattern = r"archidekt\.com/decks/(\d+)"
            match = re.search(pattern, url)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            print(f"Error extracting deck ID: {e}")
            return None

    def _fetch_deck_data(self, api_url: str) -> Optional[Dict[str, Any]]:
        """Fetch deck data from Archidekt API."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://archidekt.com/",
            }

            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()

            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"HTTP error fetching deck data: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching deck data: {e}")
            return None

    def _parse_deck_data(
        self, deck_data: Dict[str, Any], original_url: str
    ) -> UniversalDeck:
        """Parse Archidekt deck data into UniversalDeck format."""
        try:
            # Extract basic deck information
            deck_name = deck_data.get("name", "Unnamed Archidekt Deck")
            deck_description = deck_data.get("description", "")

            # Parse cards from the top-level cards array
            mainboard = []
            sideboard = []
            commanders = []

            # Get categories that are included in the deck
            included_categories = set()
            for category in deck_data.get("categories", []):
                if category.get("includedInDeck", False):
                    included_categories.add(category["name"])

            # Get cards from the top-level cards array
            cards = deck_data.get("cards", [])

            for card_entry in cards:
                # Extract card information from nested structure
                card_data = card_entry.get("card", {})
                oracle_card = card_data.get("oracleCard", {})
                card_name = oracle_card.get("name", "")
                quantity = card_entry.get("quantity", 1)

                if not card_name:
                    continue

                # Check if this card is in any included category
                card_categories = card_entry.get("categories", [])
                if not any(cat in included_categories for cat in card_categories):
                    continue  # Skip cards not in included categories                # Extract layout for Adventure card handling
                layout = oracle_card.get("layout", "normal")

                # Create card entry
                card_info = {
                    "name": card_name,
                    "quantity": quantity,
                    "set": card_data.get("edition", {}).get("editioncode", ""),
                    "collector_number": card_data.get("collectorNumber", ""),
                    "scryfall_id": card_data.get("uid", ""),
                    "layout": layout,
                }

                # Determine deck section based on categories
                is_commander = any(
                    "commander" in cat.lower() for cat in card_categories
                )
                is_sideboard = any(
                    "sideboard" in cat.lower() or "maybe" in cat.lower()
                    for cat in card_categories
                )

                if is_commander:
                    commanders.append(card_name)
                    # Commanders are stored separately, not in sideboard
                elif is_sideboard:
                    sideboard.append(card_info)
                else:
                    mainboard.append(card_info)

            # Determine deck format based on commanders or card count
            deck_format = "commander" if commanders else "casual"

            # Create UniversalDeck
            universal_deck = UniversalDeck(
                name=deck_name,
                url=original_url,
                format=deck_format,
                description=deck_description,
                mainboard=mainboard,
                sideboard=sideboard,
                commanders=commanders,
            )

            return universal_deck

        except Exception as e:
            raise ValueError(f"Error parsing Archidekt deck data: {e}")

    def _clean_card_name(self, name: str) -> str:
        """Clean card name for Cockatrice compatibility."""
        if not name:
            return ""

        # Handle dual-faced cards - take the first name before '//'
        # Note: This doesn't handle Adventure cards correctly like the updated version
        # in deck_import.py, but Archidekt might provide layout info to fix this later
        if "//" in name:
            return name.split("//")[0].strip()

        return name.strip()


def main():
    """Test the Archidekt importer."""
    scraper = ArchidektImportScraper()

    # Test URL
    test_url = "https://archidekt.com/decks/10029246/shanna_lifegain_v2"

    print(f"Testing Archidekt importer with URL: {test_url}")
    print(f"Can handle URL: {scraper.can_handle_url(test_url)}")

    if scraper.can_handle_url(test_url):
        print("Fetching deck...")
        deck = scraper.fetch_deck(test_url)

        if deck:
            print(f"✅ Successfully imported: {deck.name}")
            print(f"Format: {deck.format}")

            # Calculate actual card counts by quantity
            mainboard_total = sum(card.get("quantity", 1) for card in deck.mainboard)
            sideboard_total = sum(card.get("quantity", 1) for card in deck.sideboard)
            commander_total = len(deck.commanders)

            print(
                f"Mainboard cards: {mainboard_total} (from {len(deck.mainboard)} unique cards)"
            )
            print(
                f"Sideboard cards: {sideboard_total} (from {len(deck.sideboard)} unique cards)"
            )
            print(f"Commanders: {commander_total} - {deck.commanders}")

            # Calculate total cards
            total_cards = mainboard_total + sideboard_total + commander_total
            print(f"Total cards: {total_cards} (should be 100 for Commander)")

            # Show first few cards
            if deck.mainboard:
                print("\nFirst few mainboard cards:")
                for i, card in enumerate(deck.mainboard[:5]):
                    print(f"  {card.get('quantity', 1)}x {card.get('name', 'Unknown')}")
                if len(deck.mainboard) > 5:
                    print(f"  ... and {len(deck.mainboard) - 5} more")
        else:
            print("❌ Failed to import deck")


if __name__ == "__main__":
    main()
