"""moxfield_scraper.py

Module to fetch commander precon decklists from Moxfield's official WotC account and parse deck data.
Includes smart caching to speed up subsequent loads.
"""

import requests
import json
import time
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import sys
from pathlib import Path

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.deck_parser import CockatriceDeck, CardEntry
import os
from datetime import datetime, timedelta


@dataclass
class MoxfieldDeck:
    """Represents a precon deck from Moxfield with metadata and card list."""

    name: str
    url: str
    commanders: List[str] = None
    description: str = ""
    year: str = ""
    format: str = ""
    mainboard: List[Dict[str, Any]] = None
    sideboard: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.commanders is None:
            self.commanders = []
        if self.mainboard is None:
            self.mainboard = []
        if self.sideboard is None:
            self.sideboard = []


class MoxfieldScraper:
    """Scraper to fetch precon deck lists from Moxfield's official WotC account with smart caching."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
            }
        )
        self.wotc_username = "WizardsOfTheCoast"
        self.base_url = f"https://api2.moxfield.com/v2/users/{self.wotc_username}/decks"

        # Cache configuration
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".cockatrice_assistant_cache"

        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "precons_metadata.json"
        self.cache_max_age_hours = 24  # Refresh cache every 24 hours

    def _is_cache_valid(self) -> bool:
        """Check if the cached data is still valid (not expired)."""
        if not self.cache_file.exists():
            return False

        try:
            cache_modified = datetime.fromtimestamp(self.cache_file.stat().st_mtime)
            age_limit = datetime.now() - timedelta(hours=self.cache_max_age_hours)
            return cache_modified > age_limit
        except (OSError, ValueError):
            return False

    def _load_cache(self) -> Optional[List[MoxfieldDeck]]:
        """Load precon metadata from cache file."""
        if not self._is_cache_valid():
            return None

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # Convert dict data back to MoxfieldDeck objects
            decks = []
            for deck_data in cache_data["decks"]:
                deck = MoxfieldDeck(**deck_data)
                decks.append(deck)

            print(
                f"Loaded {len(decks)} precons from cache (cached {cache_data.get('cached_at', 'unknown')})"
            )
            return decks

        except (json.JSONDecodeError, KeyError, TypeError, FileNotFoundError) as e:
            print(f"Cache file corrupted, will refresh: {e}")
            return None

    def _save_cache(self, decks: List[MoxfieldDeck]) -> None:
        """Save precon metadata to cache file."""
        try:
            cache_data = {
                "cached_at": datetime.now().isoformat(),
                "cache_version": "1.0",
                "total_decks": len(decks),
                "decks": [asdict(deck) for deck in decks],
            }

            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            print(f"Cached {len(decks)} precons to {self.cache_file}")

        except (OSError, TypeError) as e:
            print(f"Failed to save cache: {e}")

    def fetch_all_precons(self, force_refresh: bool = False) -> List[MoxfieldDeck]:
        """Fetch all commander precon decks from Moxfield's WotC account with caching.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data
        """
        # Try to load from cache first (unless forced refresh)
        if not force_refresh:
            cached_decks = self._load_cache()
            if cached_decks is not None:
                return cached_decks

        # Cache miss or forced refresh - fetch from API
        try:
            print("Fetching precons from Moxfield WotC account...")

            all_decks = []
            page = 1
            page_size = 100

            while True:
                print(f"Fetching page {page}...")

                # Get all decks from this page, then filter for Commander Precons
                params = {
                    "pageNumber": page,
                    "pageSize": page_size,
                    "sortType": "updated",
                    "sortDirection": "Descending",
                }

                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                if not data.get("data") or len(data["data"]) == 0:
                    print(f"No more decks found on page {page}")
                    break

                decks_on_page = data["data"]

                # Filter for Commander Precons on this page
                precons_on_page = []
                for deck_data in decks_on_page:
                    format_name = deck_data.get("format", "").lower()
                    if "commanderprecon" in format_name:
                        precons_on_page.append(deck_data)

                print(
                    f"Found {len(precons_on_page)} Commander Precons on page {page} (out of {len(decks_on_page)} total decks)"
                )

                for deck_data in precons_on_page:
                    try:
                        deck_name = deck_data.get("name", "")

                        # Skip collector's edition decks if requested
                        if any(
                            term in deck_name.lower()
                            for term in ["collector's edition"]
                        ):
                            print(f"  Skipping collector's edition: {deck_name}")
                            continue

                        # Extract basic info
                        deck_url = f"https://moxfield.com/decks/{deck_data.get('publicId', '')}"
                        format_name = deck_data.get("format", "")

                        # Try to extract year from name
                        year_match = re.search(r"20\d{2}", deck_name)
                        year = year_match.group() if year_match else ""

                        # Extract commander from deck data
                        commanders = []
                        if "commanders" in deck_data and deck_data["commanders"]:
                            for commander_data in deck_data["commanders"]:
                                commander_name = commander_data.get("card", {}).get(
                                    "name", ""
                                )
                                if commander_name:
                                    commanders.append(commander_name)

                        deck = MoxfieldDeck(
                            name=deck_name,
                            url=deck_url,
                            commanders=commanders,
                            description=deck_data.get("description", ""),
                            year=year,
                            format=format_name,
                            mainboard=[],  # Will be populated when fetching details
                            sideboard=[],  # Will be populated when fetching details
                        )

                        all_decks.append(deck)

                    except Exception as e:
                        print(f"Error parsing deck: {e}")
                        continue

                # Check if we should continue to next page
                if len(decks_on_page) < page_size:
                    print(
                        f"Reached end of results (got {len(decks_on_page)} < {page_size})"
                    )
                    break

                page += 1
                time.sleep(0.5)  # Be respectful to the API

            print(
                f"Successfully found {len(all_decks)} Commander Precons from Moxfield WotC account"
            )

            # Save to cache for future use
            self._save_cache(all_decks)

            return all_decks

        except Exception as e:
            print(f"Error fetching precons from Moxfield: {e}")
            # Try to return cached data as fallback if available
            cached_decks = self._load_cache()
            if cached_decks is not None:
                print("Returning cached data as fallback due to API error")
                return cached_decks
            return []

    def fetch_deck_details(self, deck_id: str) -> MoxfieldDeck | None:
        """Fetch detailed card list from a specific Moxfield deck ID."""
        try:
            if not deck_id:
                return None

            print(f"Fetching deck details for: {deck_id}")

            # Use Moxfield API to get deck details
            api_url = f"https://api2.moxfield.com/v2/decks/all/{deck_id}"
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Extract basic info
            name = data.get("name", "Unknown Deck")
            description = data.get("description", "")
            format_name = data.get("format", "")

            # Extract year from name
            year_match = re.search(r"20\d{2}", name)
            year = year_match.group() if year_match else ""

            # Extract commanders
            commanders = []
            if "commanders" in data and data["commanders"]:
                commanders_dict = data["commanders"]
                if isinstance(commanders_dict, dict):
                    for commander_name, commander_data in commanders_dict.items():
                        if commander_name:
                            commanders.append(commander_name)

            # Extract mainboard cards
            mainboard = []
            if "mainboard" in data and data["mainboard"]:
                mainboard_dict = data["mainboard"]
                if isinstance(mainboard_dict, dict):
                    for card_id, card_info in mainboard_dict.items():
                        if isinstance(card_info, dict):
                            card_data = card_info.get("card", {})
                            if isinstance(card_data, dict):
                                mainboard.append(
                                    {
                                        "quantity": card_info.get("quantity", 1),
                                        "name": card_data.get("name", ""),
                                        "set": card_data.get("set", ""),
                                        "collector_number": card_data.get("cn", ""),
                                        "scryfall_id": card_data.get("scryfall_id", ""),
                                    }
                                )

            # Extract sideboard cards
            sideboard = []
            if "sideboard" in data and data["sideboard"]:
                sideboard_dict = data["sideboard"]
                if isinstance(sideboard_dict, dict):
                    for card_id, card_info in sideboard_dict.items():
                        if isinstance(card_info, dict):
                            card_data = card_info.get("card", {})
                            if isinstance(card_data, dict):
                                sideboard.append(
                                    {
                                        "quantity": card_info.get("quantity", 1),
                                        "name": card_data.get("name", ""),
                                        "set": card_data.get("set", ""),
                                        "collector_number": card_data.get("cn", ""),
                                        "scryfall_id": card_data.get("scryfall_id", ""),
                                    }
                                )

            return MoxfieldDeck(
                name=name,
                url=f"https://moxfield.com/decks/{deck_id}",
                commanders=commanders,
                year=year,
                format=format_name,
                mainboard=mainboard,
                sideboard=sideboard,
                description=description,
            )

        except Exception as e:
            print(f"Error fetching deck details: {e}")
            return None


def clean_card_name(name: str) -> str:
    """Clean card name for Cockatrice compatibility.

    Handles dual-faced cards by taking the first name before '//'

    Args:
        name: Raw card name from Moxfield

    Returns:
        Cleaned card name suitable for Cockatrice
    """
    if not name:
        return ""

    # Handle dual-faced cards - take the first name before '//'
    if "//" in name:
        return name.split("//")[0].strip()

    return name.strip()


def convert_moxfield_to_cockatrice(moxfield_deck: MoxfieldDeck) -> CockatriceDeck:
    """Convert a MoxfieldDeck to a CockatriceDeck for .cod export."""

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

    def is_likely_creature(card_name: str) -> bool:
        """Determine if a card is likely to be a creature based on its name."""
        if not card_name:
            return False

        card_lower = card_name.lower()

        # Cards that are definitely not creatures (check first for higher confidence)
        non_creature_indicators = [
            # Spells and effects
            "lightning bolt",
            "counterspell",
            "dispel",
            "cancel",
            "negate",
            "shock",
            "path to exile",
            "swords to plowshares",
            "wrath",
            "damnation",
            "brainstorm",
            "force of will",
            "dark ritual",
            "bolt",
            # Planeswalkers (usually have comma in name)
            "jace,",
            "elspeth,",
            "chandra,",
            "garruk,",
            "liliana,",
            "ajani,",
            "nissa,",
            "gideon,",
            "vraska,",
            "teferi,",
            "karn,",
            "ugin,",
            # Artifacts and enchantments
            "sol ring",
            "mana",
            "signet",
            "talisman",
            "medallion",
            "crypt",
            "vault",
            "temple",
            "sanctum",
            "citadel",
            "tower",
            "spire",
            # Lands
            "plains",
            "island",
            "swamp",
            "mountain",
            "forest",
            "wastes",
            "command tower",
            "reliquary tower",
            "terramorphic expanse",
            # Common spell words
            "burn",
            "draw",
            "tutor",
            "search",
            "fetch",
            "ramp",
            "removal",
            "exile",
            "destroy",
            "sacrifice",
            "board wipe",
            "instant",
            "sorcery",
        ]

        # Check for specific non-creature cards first
        for indicator in non_creature_indicators:
            if indicator in card_lower:
                return False

        # Planeswalker detection (they have comma and titles)
        if "," in card_name and any(
            title in card_lower
            for title in [
                "the mind sculptor",
                "knight-errant",
                "guildpact",
                "worldwaker",
                "voice of zendikar",
                "chainer of the dead",
                "unraveler of secrets",
            ]
        ):
            return False

        # Common creature type words that appear in creature names
        creature_indicators = [
            # Creature types
            "warrior",
            "soldier",
            "knight",
            "wizard",
            "shaman",
            "druid",
            "priest",
            "vampire",
            "zombie",
            "spirit",
            "angel",
            "demon",
            "dragon",
            "beast",
            "goblin",
            "orc",
            "elf",
            "dwarf",
            "human",
            "giant",
            "troll",
            "ogre",
            "elemental",
            "construct",
            "golem",
            "spider",
            "wolf",
            "bear",
            "cat",
            "dog",
            "bird",
            "snake",
            "lizard",
            "fish",
            "whale",
            "kraken",
            "horror",
            "nightmare",
            "shade",
            "wraith",
            "skeleton",
            "rat",
            "insect",
            "bat",
            "avatar",
            "incarnation",
            "titan",
            "hydra",
            "wurm",
            "minotaur",
            "sphinx",
            "phoenix",
            "griffin",
            "pegasus",
            "unicorn",
            "centaur",
            "satyr",
            "faerie",
            # Common creature name patterns and titles
            " lord",
            " master",
            " champion",
            " guardian",
            " keeper",
            " warden",
            " sentinel",
            " protector",
            " hunter",
            " seeker",
            " caller",
            " summoner",
            " wielder",
            " bearer",
            " rider",
            " walker",
            " guide",
            " scout",
            # Descriptive creature words
            "king ",
            "queen ",
            "prince ",
            "princess ",
            "emperor ",
            "empress ",
            "general ",
            "captain ",
            "archon",
            "elder ",
            "ancient ",
            "primarch",
            "khan ",
            "baron",
            "young ",
            "veteran",
            "seasoned",
            "mighty",
            "fierce",
            "savage",
            "noble",
            "bloodthirsty",
            "ferocious",
            "mage",
            "adept",
            # Creature name endings that are common
            "mancer",
            "bringer",
            "caller",
            "seeker",
            "slayer",
            "ranger",
        ]

        # Check for creature indicators
        for indicator in creature_indicators:
            if indicator in card_lower:
                return True

        # Special cases for known creature names that don't follow patterns
        known_creatures = [
            "tarmogoyf",
            "snapcaster mage",
            "lightning dragon",
            "primeval titan",
            "serra angel",
            "llanowar elves",
            "vampire nighthawk",
            "goblin guide",
            "young pyromancer",
        ]

        if card_lower in known_creatures:
            return True

        # Check for specific creature name patterns that might be missed
        if "dragon" in card_lower and "lightning" in card_lower:
            return True

        # Additional heuristics for creature-like names
        words = card_name.split()
        if len(words) >= 2:
            # Creatures often have proper noun patterns (capitalized words)
            capitalized_count = sum(1 for word in words if word and word[0].isupper())

            # If most words are capitalized and it's not a known non-creature type, likely a creature
            if capitalized_count >= 2 and len(words) <= 4:
                # Additional check: avoid planeswalker-like patterns
                if not ("," in card_name and len(words) > 3):
                    return True

        return False

    # Determine deck type and handle banner card accordingly
    is_commander_deck = (
        bool(moxfield_deck.commanders) or moxfield_deck.format.lower() == "commander"
    )

    if is_commander_deck:
        # Commander deck logic - commanders go in sideboard
        commander_entries = []
        banner_card = ""
        for commander in moxfield_deck.commanders:
            if commander.strip():
                # Clean the commander name to handle dual-faced commanders
                commander_name = clean_card_name(commander)
                entry = CardEntry(
                    number=1,
                    name=commander_name,
                    setShortName="",
                    collectorNumber="",
                    uuid="",
                )
                commander_entries.append(entry)

                # Set the first commander as the banner card
                if not banner_card:
                    banner_card = commander_name

        cockatrice_deck = CockatriceDeck(
            deckname=moxfield_deck.name,
            zone_main=make_card_entries(moxfield_deck.mainboard),
            zone_side=commander_entries,  # Commanders go in sideboard
            banner_card=banner_card,  # Set banner card to first commander
        )
    else:
        # Non-commander deck logic - set banner card to a random card from mainboard
        banner_card = ""
        if moxfield_deck.mainboard:
            import random

            random_card = random.choice(moxfield_deck.mainboard)
            banner_card = clean_card_name(random_card.get("name", ""))

        cockatrice_deck = CockatriceDeck(
            deckname=moxfield_deck.name,
            zone_main=make_card_entries(moxfield_deck.mainboard),
            zone_side=make_card_entries(moxfield_deck.sideboard),
            banner_card=banner_card,  # Set banner card to first creature or first card
        )

    return cockatrice_deck


# Test function for development
def test_scraper():
    """Test the Moxfield scraper."""
    scraper = MoxfieldScraper()
    print("Fetching precons from Moxfield WotC account...")

    decks = scraper.fetch_all_precons()
    print(f"Found {len(decks)} decks")

    if decks:
        print("First few decks:")
        for deck in decks[:3]:
            print(f"  - {deck.name}: {deck.url}")
            print(f"    Format: {deck.format}, Year: {deck.year}")
            print(f"    Commanders: {deck.commanders}")


if __name__ == "__main__":
    test_scraper()
