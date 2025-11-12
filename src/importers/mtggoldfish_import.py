"""mtggoldfish_import.py

MTGGoldfish scraper for the universal deck import system.
Supports both archetype pages and individual deck pages.
"""

import re
import requests
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from importers.deck_import import DeckScraper, UniversalDeck


class MTGGoldfishImportScraper(DeckScraper):
    """MTGGoldfish scraper that implements the universal deck import interface."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0",
            }
        )

    def can_handle_url(self, url: str) -> bool:
        """Check if this scraper can handle the given URL."""
        return "mtggoldfish.com" in url.lower()

    def get_site_name(self) -> str:
        """Get the display name of this site."""
        return "MTGGoldfish"

    def fetch_deck(self, url: str) -> Optional[UniversalDeck]:
        """Fetch deck data from an MTGGoldfish URL using Arena export format."""
        try:
            print(f"Fetching MTGGoldfish deck from: {url}")

            # Extract deck ID from the URL and construct Arena download URL
            deck_id = self._extract_deck_id(url)
            if not deck_id:
                print("Could not extract deck ID from URL")
                return self._create_placeholder_deck(url)

            arena_url = f"https://www.mtggoldfish.com/deck/arena_download/{deck_id}"
            print(f"Using Arena download URL: {arena_url}")

            # Fetch the Arena export page
            response = self.session.get(arena_url, timeout=30)
            if response.status_code != 200:
                print(f"Failed to fetch Arena export page: {response.status_code}")
                return self._create_placeholder_deck(url)

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract deck content from textarea
            textarea = soup.find("textarea")
            if not textarea:
                print("No textarea found in Arena export page")
                return self._create_placeholder_deck(url)

            deck_content = textarea.get_text().strip()
            if not deck_content:
                print("Empty deck content in textarea")
                return self._create_placeholder_deck(url)

            # Parse the Arena format deck content
            return self._parse_arena_format(deck_content, url)

        except Exception as e:
            print(f"Error fetching MTGGoldfish deck: {e}")
            return self._create_placeholder_deck(url)

    def _extract_deck_info(
        self, soup: BeautifulSoup, url: str
    ) -> Optional[Dict[str, str]]:
        """Extract basic deck information from the page."""
        try:
            # Try to find deck name from various possible locations
            deck_name = ""

            # Method 1: Look for page title or deck title
            title_tag = soup.find("title")
            if title_tag:
                title_text = title_tag.get_text().strip()
                # Clean up MTGGoldfish title format
                if " - " in title_text:
                    deck_name = title_text.split(" - ")[0].strip()
                else:
                    deck_name = title_text.strip()

            # Method 2: Look for specific deck name elements
            if not deck_name:
                # Try h1 or h2 tags
                for tag in soup.find_all(["h1", "h2"]):
                    text = tag.get_text().strip()
                    if text and len(text) < 100:  # Reasonable deck name length
                        deck_name = text
                        break

            # Method 3: Extract from URL if needed
            if not deck_name:
                if "/deck/" in url:
                    deck_name = (
                        url.split("/deck/")[-1].split("#")[0].replace("-", " ").title()
                    )
                elif "/archetype/" in url:
                    deck_name = (
                        url.split("/archetype/")[-1]
                        .split("#")[0]
                        .replace("-", " ")
                        .title()
                    )

            # Detect format from URL or page content
            deck_format = self._detect_format(soup, url)

            return {
                "name": deck_name or "MTGGoldfish Deck",
                "format": deck_format,
                "description": f"Imported from MTGGoldfish",
                "year": self._extract_year(soup),
            }

        except Exception as e:
            print(f"Error extracting deck info: {e}")
            return None

    def _detect_format(self, soup: BeautifulSoup, url: str) -> str:
        """Detect the deck format from URL or page content."""
        url_lower = url.lower()

        # Check URL for format indicators
        if "commander" in url_lower or "edh" in url_lower:
            return "commander"
        elif "standard" in url_lower:
            return "standard"
        elif "modern" in url_lower:
            return "modern"
        elif "legacy" in url_lower:
            return "legacy"
        elif "vintage" in url_lower:
            return "vintage"
        elif "pioneer" in url_lower:
            return "pioneer"

        # Check page content for format indicators
        page_text = soup.get_text().lower()
        if "commander" in page_text or "edh" in page_text:
            return "commander"
        elif "standard" in page_text:
            return "standard"

        return "unknown"

    def _extract_year(self, soup: BeautifulSoup) -> str:
        """Extract year from page content if available."""
        page_text = soup.get_text()
        year_match = re.search(r"20\d{2}", page_text)
        return year_match.group() if year_match else ""

    def _extract_card_lists(
        self, soup: BeautifulSoup
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Extract mainboard and sideboard card lists from the page."""
        mainboard = []
        sideboard = []

        try:
            # MTGGoldfish may use JavaScript to load content, so we need to be more aggressive in parsing

            # Method 1: Look for any table rows or structured data
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 2:  # Quantity and card name
                        try:
                            # First cell might be quantity, second might be card name
                            first_cell = cells[0].get_text().strip()
                            second_cell = cells[1].get_text().strip()

                            # Try parsing quantity from first cell
                            if first_cell.isdigit():
                                quantity = int(first_cell)
                                card_name = self._clean_mtggoldfish_card_name(
                                    second_cell
                                )

                                if card_name and 1 <= quantity <= 20:
                                    card_entry = {
                                        "quantity": quantity,
                                        "name": card_name,
                                        "set": "",
                                        "collector_number": "",
                                        "scryfall_id": "",
                                    }
                                    mainboard.append(card_entry)
                        except (ValueError, AttributeError):
                            continue

            # Method 2: Look for specific MTGGoldfish classes or IDs
            deck_sections = soup.find_all(
                ["div", "span", "p"], class_=re.compile(r"deck|card|main|side", re.I)
            )
            for section in deck_sections:
                cards = self._parse_card_container(section)

                section_text = section.get_text().lower()
                is_sideboard = any(
                    term in section_text for term in ["sideboard", "side board", "sb"]
                )

                if is_sideboard:
                    sideboard.extend(cards)
                else:
                    mainboard.extend(cards)

            # Method 3: Fallback to text parsing if structured methods didn't work
            if not mainboard:
                mainboard, sideboard = self._fallback_card_extraction(soup)

            # Method 4: If still no cards, try a more aggressive text search
            if not mainboard:
                mainboard = self._aggressive_card_extraction(soup)

        except Exception as e:
            print(f"Error extracting card lists: {e}")

        return mainboard, sideboard

    def _parse_card_container(self, container) -> List[Dict[str, Any]]:
        """Parse individual card container for card entries."""
        cards = []

        try:
            # Look for rows or individual card elements
            card_elements = container.find_all(["tr", "div", "li"])

            for element in card_elements:
                card_text = element.get_text().strip()
                if not card_text:
                    continue

                # Parse card line format: "4 Lightning Bolt" or "4x Lightning Bolt"
                card_match = re.match(r"(\d+)x?\s+(.+)", card_text)
                if card_match:
                    quantity = int(card_match.group(1))
                    card_name = card_match.group(2).strip()

                    # Clean up card name (remove set info, etc.)
                    card_name = self._clean_mtggoldfish_card_name(card_name)

                    if card_name:
                        cards.append(
                            {
                                "quantity": quantity,
                                "name": card_name,
                                "set": "",
                                "collector_number": "",
                                "scryfall_id": "",
                            }
                        )

        except Exception as e:
            print(f"Error parsing card container: {e}")

        return cards

    def _fallback_card_extraction(
        self, soup: BeautifulSoup
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Fallback method to extract cards by parsing page text."""
        mainboard = []
        sideboard = []

        try:
            # Get all text and look for card patterns
            page_text = soup.get_text()
            lines = page_text.split("\n")

            current_section = "mainboard"

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check for sideboard indicators
                if re.search(r"sideboard|side\s*board|sb:", line.lower()):
                    current_section = "sideboard"
                    continue

                # Look for card patterns
                card_match = re.match(r"(\d+)x?\s+(.+)", line)
                if card_match:
                    quantity = int(card_match.group(1))
                    card_name = card_match.group(2).strip()
                    card_name = self._clean_mtggoldfish_card_name(card_name)

                    if card_name and quantity <= 20:  # Reasonable quantity limit
                        card_entry = {
                            "quantity": quantity,
                            "name": card_name,
                            "set": "",
                            "collector_number": "",
                            "scryfall_id": "",
                        }

                        if current_section == "sideboard":
                            sideboard.append(card_entry)
                        else:
                            mainboard.append(card_entry)

        except Exception as e:
            print(f"Error in fallback card extraction: {e}")

        return mainboard, sideboard

    def _clean_mtggoldfish_card_name(self, name: str) -> str:
        """Clean card name from MTGGoldfish format."""
        if not name:
            return ""

        # Remove common suffixes and formatting
        name = re.sub(r"\s*\([^)]*\)\s*$", "", name)  # Remove parenthetical info
        name = re.sub(r"\s*\[[^\]]*\]\s*$", "", name)  # Remove bracket info
        name = name.strip()

        # Handle dual-faced cards
        if "//" in name:
            name = name.split("//")[0].strip()

        # Filter out obvious non-card text
        excluded_terms = [
            "tix",
            "tickets",
            "price",
            "cost",
            "budget",
            "estimated",
            "bracket",
            "mainboard",
            "sideboard",
            "commander",
            "total",
            "deck",
            "archetype",
            "meta",
            "format",
            "legal",
            "banned",
            "restricted",
            "$",
            "€",
            "¢",
        ]

        name_lower = name.lower()
        if any(term in name_lower for term in excluded_terms):
            return ""

        # Card names should have reasonable length and contain mostly letters
        if len(name) < 2 or len(name) > 50:
            return ""

        # Should contain at least some letters
        if not any(c.isalpha() for c in name):
            return ""

        # Should not be all numbers or symbols
        if (
            name.replace(" ", "")
            .replace(",", "")
            .replace("'", "")
            .replace("-", "")
            .isdigit()
        ):
            return ""

        return name

    def _detect_commanders(self, soup: BeautifulSoup, deck_format: str) -> List[str]:
        """Detect commanders from the page content."""
        commanders = []

        if deck_format.lower() != "commander":
            return commanders

        try:
            # Look for commander sections or indicators
            page_text = soup.get_text()
            lines = page_text.split("\n")

            for line in lines:
                line = line.strip()
                line_lower = line.lower()

                # Look for explicit commander indicators
                if any(
                    term in line_lower
                    for term in ["commander:", "general:", "commander deck"]
                ):
                    # Try to extract commander name from the same line or nearby
                    commander_match = re.search(r"commander:?\s*(.+)", line, re.I)
                    if commander_match:
                        potential_name = commander_match.group(1).strip()
                        potential_name = self._clean_mtggoldfish_card_name(
                            potential_name
                        )

                        # Validate commander name (should be reasonable length and contain letters)
                        if (
                            potential_name
                            and 3 <= len(potential_name) <= 50
                            and any(c.isalpha() for c in potential_name)
                        ):
                            # Make sure it's not generic text
                            if not any(
                                word in potential_name.lower()
                                for word in [
                                    "deck",
                                    "list",
                                    "budget",
                                    "estimated",
                                    "bracket",
                                ]
                            ):
                                commanders.append(potential_name)

                # Look for "1 [Card Name]" patterns that might be commanders
                single_card_match = re.match(
                    r"^1\s+([A-Z][A-Za-z\s\',\-]+)$", line.strip()
                )
                if single_card_match:
                    card_name = single_card_match.group(1).strip()
                    card_name = self._clean_mtggoldfish_card_name(card_name)

                    # Only add if it looks like a proper card name
                    if card_name and 3 <= len(card_name) <= 50:
                        # Make sure it's not generic text or common non-commander cards
                        excluded_words = [
                            "land",
                            "mountain",
                            "island",
                            "forest",
                            "plains",
                            "swamp",
                            "sol ring",
                            "command tower",
                        ]
                        if not any(
                            word in card_name.lower() for word in excluded_words
                        ):
                            commanders.append(card_name)

        except Exception as e:
            print(f"Error detecting commanders: {e}")

        return commanders

    def _aggressive_card_extraction(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Aggressively extract cards from any text content on the page."""
        cards = []

        try:
            # Get all text and split into words
            all_text = soup.get_text()

            # Look for patterns like "4 Lightning Bolt", "1 Sol Ring", etc.
            # This is more liberal and might catch some false positives
            import re

            card_pattern = r"(\d+)\s+([A-Z][A-Za-z\s\',\-/]+?)(?=\s+\d+|\s*$|\n)"
            matches = re.findall(card_pattern, all_text, re.MULTILINE)

            for quantity_str, card_name in matches:
                try:
                    quantity = int(quantity_str)
                    if 1 <= quantity <= 20:  # Reasonable limits
                        clean_name = self._clean_mtggoldfish_card_name(card_name)
                        if clean_name and len(clean_name) > 2:  # Not too short
                            # Additional validation - card names usually have capital letters
                            if any(c.isupper() for c in clean_name):
                                cards.append(
                                    {
                                        "quantity": quantity,
                                        "name": clean_name,
                                        "set": "",
                                        "collector_number": "",
                                        "scryfall_id": "",
                                    }
                                )
                except (ValueError, AttributeError):
                    continue

            # Remove duplicates
            seen_cards = set()
            unique_cards = []
            for card in cards:
                card_key = (card["name"], card["quantity"])
                if card_key not in seen_cards:
                    seen_cards.add(card_key)
                    unique_cards.append(card)

            print(f"Aggressive extraction found {len(unique_cards)} unique cards")
            return unique_cards[:100]  # Limit to reasonable number

        except Exception as e:
            print(f"Error in aggressive card extraction: {e}")
            return []

    def _create_placeholder_deck(self, url: str) -> UniversalDeck:
        """Create a placeholder deck when scraping fails."""
        deck_name = "MTGGoldfish Deck (Import Failed)"
        if "/deck/" in url:
            deck_name = (
                url.split("/deck/")[-1].split("#")[0].replace("-", " ").title()
                + " (Import Failed)"
            )
        elif "/archetype/" in url:
            deck_name = (
                url.split("/archetype/")[-1].split("#")[0].replace("-", " ").title()
                + " (Import Failed)"
            )

        return UniversalDeck(
            name=deck_name,
            url=url,
            format="unknown",
            description="This is a placeholder deck. MTGGoldfish scraping encountered issues.",
            mainboard=self._create_sample_cards("standard"),
            sideboard=[],
            commanders=[],
        )

    def _create_sample_cards(self, deck_format: str) -> List[Dict[str, Any]]:
        """Create sample cards for demonstration purposes."""
        if deck_format.lower() == "commander":
            return [
                {
                    "quantity": 1,
                    "name": "Sol Ring",
                    "set": "",
                    "collector_number": "",
                    "scryfall_id": "",
                },
                {
                    "quantity": 1,
                    "name": "Command Tower",
                    "set": "",
                    "collector_number": "",
                    "scryfall_id": "",
                },
                {
                    "quantity": 1,
                    "name": "Lightning Bolt",
                    "set": "",
                    "collector_number": "",
                    "scryfall_id": "",
                },
                {
                    "quantity": 1,
                    "name": "Counterspell",
                    "set": "",
                    "collector_number": "",
                    "scryfall_id": "",
                },
                {
                    "quantity": 36,
                    "name": "Basic Land (Mixed)",
                    "set": "",
                    "collector_number": "",
                    "scryfall_id": "",
                },
            ]
        else:
            return [
                {
                    "quantity": 4,
                    "name": "Lightning Bolt",
                    "set": "",
                    "collector_number": "",
                    "scryfall_id": "",
                },
                {
                    "quantity": 4,
                    "name": "Counterspell",
                    "set": "",
                    "collector_number": "",
                    "scryfall_id": "",
                },
                {
                    "quantity": 4,
                    "name": "Brainstorm",
                    "set": "",
                    "collector_number": "",
                    "scryfall_id": "",
                },
                {
                    "quantity": 24,
                    "name": "Basic Land (Mixed)",
                    "set": "",
                    "collector_number": "",
                    "scryfall_id": "",
                },
            ]

    def _extract_deck_id(self, url: str) -> Optional[str]:
        """Extract deck ID from MTGGoldfish URL."""
        try:
            # Handle different URL formats:
            # https://www.mtggoldfish.com/deck/300499#paper
            # https://www.mtggoldfish.com/archetype/standard-izzet-cauldron-woe#paper

            if "/deck/" in url:
                # Direct deck URL
                deck_part = url.split("/deck/")[-1]
                deck_id = deck_part.split("#")[0].split("?")[0]
                if deck_id.isdigit():
                    return deck_id
            elif "/archetype/" in url:
                # Archetype URL - need to find the first deck link on the page
                print("Archetype URL detected - finding first deck on the page...")
                return self._extract_deck_from_archetype(url)

            return None
        except Exception as e:
            print(f"Error extracting deck ID: {e}")
            return None

    def _parse_arena_format(self, content: str, original_url: str) -> UniversalDeck:
        """Parse MTGGoldfish Arena export format."""
        try:
            lines = content.split("\n")

            # Initialize deck data
            deck_name = "MTGGoldfish Deck"
            commanders = []
            mainboard = []
            sideboard = []
            current_section = "mainboard"

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Parse header information
                if line.startswith("Name "):
                    deck_name = line[5:].strip()  # Remove "Name " prefix
                    continue

                # Section headers
                if line.lower() == "commander":
                    current_section = "commander"
                    continue
                elif line.lower() == "deck":
                    current_section = "mainboard"
                    continue
                elif line.lower() == "sideboard":
                    current_section = "sideboard"
                    continue

                # Parse card lines (format: "4 Lightning Bolt")
                card_match = re.match(r"(\d+)\s+(.+)", line)
                if card_match:
                    quantity = int(card_match.group(1))
                    card_name = card_match.group(2).strip()

                    # Clean the card name
                    clean_name = self._clean_arena_card_name(card_name)
                    if not clean_name:
                        continue

                    card_entry = {
                        "quantity": quantity,
                        "name": clean_name,
                        "set": "",
                        "collector_number": "",
                        "scryfall_id": "",
                    }

                    if current_section == "commander":
                        commanders.append(clean_name)
                    elif current_section == "sideboard":
                        sideboard.append(card_entry)
                    else:  # mainboard
                        mainboard.append(card_entry)

            # Detect format based on content
            deck_format = "commander" if commanders else "standard"

            print(
                f"Parsed Arena format: {len(mainboard)} mainboard, {len(sideboard)} sideboard, {len(commanders)} commanders"
            )

            return UniversalDeck(
                name=deck_name,
                url=original_url,
                format=deck_format,
                description="Imported from MTGGoldfish using Arena format",
                year="",
                mainboard=mainboard,
                sideboard=sideboard,
                commanders=commanders,
            )

        except Exception as e:
            print(f"Error parsing Arena format: {e}")
            return self._create_placeholder_deck(original_url)

    def _clean_arena_card_name(self, name: str) -> str:
        """Clean card name from Arena export format."""
        if not name:
            return ""

        # Remove any trailing parentheses or set info
        name = re.sub(r"\s*\([^)]*\)\s*$", "", name)
        name = name.strip()

        # Handle dual-faced cards
        if "//" in name:
            name = name.split("//")[0].strip()

        # Basic validation
        if len(name) < 2 or len(name) > 50:
            return ""

        return name

    def _extract_deck_from_archetype(self, archetype_url: str) -> Optional[str]:
        """Extract the first deck ID from an MTGGoldfish archetype page."""
        try:
            print(f"Fetching archetype page: {archetype_url}")
            response = self.session.get(archetype_url, timeout=30)

            if response.status_code != 200:
                print(f"Failed to fetch archetype page: {response.status_code}")
                return None

            soup = BeautifulSoup(response.content, "html.parser")

            # Look for deck links in the format /deck/NUMBER
            deck_links = []
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")

                # Look for deck links like /deck/7432842
                if re.match(r"/deck/\d+$", href):
                    deck_id = href.split("/deck/")[-1]
                    if deck_id not in deck_links:  # Avoid duplicates
                        deck_links.append(deck_id)

            if deck_links:
                first_deck_id = deck_links[0]
                print(
                    f"Found {len(deck_links)} deck(s) on archetype page, using first deck: {first_deck_id}"
                )
                return first_deck_id
            else:
                print("No deck links found on archetype page")
                return None

        except Exception as e:
            print(f"Error extracting deck from archetype: {e}")
            return None
