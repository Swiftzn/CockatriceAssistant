"""
Deck filtering utilities for MTGJSON integration.

Provides advanced filtering capabilities for deck selection and categorization.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from importers.mtgjson_scraper import MTGDeck


class DeckFilters:
    """Utility class for filtering and categorizing MTG decks."""

    # Predefined deck type categories for easier filtering
    COMPETITIVE_TYPES = {
        "Challenger Deck",
        "Pro Tour Deck",
        "World Championship Deck",
        "Modern Event Deck",
        "Pioneer Challenger Deck",
    }

    CASUAL_TYPES = {
        "Commander Deck",
        "Theme Deck",
        "Intro Pack",
        "Starter Deck",
        "Planechase Deck",
        "Archenemy Deck",
        "Brawl Deck",
    }

    PREMIUM_TYPES = {
        "Premium Deck",
        "Box Set",
        "From the Vault",
        "Secret Lair Drop",
        "Signature Spellbook",
        "Spellbook",
    }

    DUEL_TYPES = {"Duel Deck", "Duel Of The Planeswalkers Deck"}

    LIMITED_TYPES = {"Jumpstart", "Welcome Deck", "Sample Deck", "Demo Deck"}

    # Format associations based on deck types and naming patterns
    FORMAT_INDICATORS = {
        "Standard": ["Standard", "Challenger Deck", "Intro Pack"],
        "Modern": ["Modern Event Deck", "Modern"],
        "Legacy": ["Legacy", "Premium Deck"],
        "Vintage": ["Vintage"],
        "Commander": ["Commander Deck", "Commander"],
        "Pioneer": ["Pioneer Challenger Deck"],
        "Historic": ["Historic", "Arena"],
        "Limited": ["Jumpstart", "Cube", "Draft"],
    }

    @classmethod
    def categorize_deck_type(cls, deck_type: str) -> str:
        """
        Categorize a deck type into a broader category.

        Args:
            deck_type: The specific deck type from MTGJSON

        Returns:
            Category name (Competitive, Casual, Premium, Duel, Limited, Other)
        """
        if deck_type in cls.COMPETITIVE_TYPES:
            return "Competitive"
        elif deck_type in cls.CASUAL_TYPES:
            return "Casual"
        elif deck_type in cls.PREMIUM_TYPES:
            return "Premium"
        elif deck_type in cls.DUEL_TYPES:
            return "Duel"
        elif deck_type in cls.LIMITED_TYPES:
            return "Limited"
        else:
            return "Other"

    @classmethod
    def infer_format(cls, deck_data: Dict[str, Any]) -> str:
        """
        Infer the likely format of a deck based on type and naming patterns.

        Args:
            deck_data: Deck metadata dictionary

        Returns:
            Inferred format name or "Unknown"
        """
        deck_type = deck_data.get("type", "")
        deck_name = deck_data.get("name", "")
        set_code = deck_data.get("code", "")

        # Check format indicators
        for format_name, indicators in cls.FORMAT_INDICATORS.items():
            for indicator in indicators:
                if indicator.lower() in deck_type.lower():
                    return format_name

        # Special cases based on naming patterns
        if "Commander" in deck_name or set_code.startswith("C"):
            return "Commander"
        elif "Standard" in deck_name:
            return "Standard"
        elif "Modern" in deck_name:
            return "Modern"
        elif "Legacy" in deck_name:
            return "Legacy"
        elif "Pioneer" in deck_name:
            return "Pioneer"

        return "Unknown"

    @classmethod
    def extract_color_identity(
        cls, deck_details: Optional[Dict[str, Any]]
    ) -> List[str]:
        """
        Extract color identity from deck details.

        Args:
            deck_details: Full deck data with commander and mainBoard info

        Returns:
            List of colors in the deck's identity (W, U, B, R, G)
        """
        if not deck_details:
            return []

        colors = set()

        # Check commander colors first
        commanders = deck_details.get("commander", [])
        for commander in commanders:
            commander_colors = commander.get("colorIdentity", [])
            colors.update(commander_colors)

        # If no commander colors, analyze mainboard (basic approach)
        if not colors:
            mainboard = deck_details.get("mainBoard", [])
            for card in mainboard[:20]:  # Sample first 20 cards for performance
                card_colors = card.get("colorIdentity", [])
                colors.update(card_colors)

        return sorted(list(colors))

    @classmethod
    def is_secret_lair(cls, deck_data: Dict[str, Any]) -> bool:
        """Check if deck is a Secret Lair product."""
        filename = deck_data.get("fileName", "")
        deck_type = deck_data.get("type", "")
        return filename.endswith("_SLD") or "Secret Lair" in deck_type

    @classmethod
    def is_commander_product(cls, deck_data: Dict[str, Any]) -> bool:
        """Check if deck is a Commander product."""
        deck_type = deck_data.get("type", "")
        set_code = deck_data.get("code", "")
        filename = deck_data.get("fileName", "")

        return (
            deck_type == "Commander Deck"
            or set_code.startswith("C")
            or "_CMD" in filename
            or "_CMR" in filename
            or "_AFC" in filename
        )

    @classmethod
    def get_era_from_date(cls, release_date: str) -> str:
        """
        Categorize deck by MTG era based on release date.

        Args:
            release_date: Release date in YYYY-MM-DD format

        Returns:
            Era name (Classic, Modern Era, New Era, Current)
        """
        if not release_date:
            return "Unknown"

        try:
            date = datetime.strptime(release_date, "%Y-%m-%d")
            year = date.year

            if year < 2003:
                return "Classic (1993-2002)"
            elif year < 2009:
                return "Modern Era (2003-2008)"
            elif year < 2019:
                return "New Era (2009-2018)"
            else:
                return "Current (2019+)"
        except ValueError:
            return "Unknown"

    @classmethod
    def filter_by_power_level(cls, deck_data: Dict[str, Any]) -> str:
        """
        Estimate power level based on deck type and product line.

        Args:
            deck_data: Deck metadata

        Returns:
            Power level category (Casual, Focused, Optimized, High Power)
        """
        deck_type = deck_data.get("type", "")
        deck_name = deck_data.get("name", "")

        # High power indicators
        if any(
            keyword in deck_type
            for keyword in ["Pro Tour", "World Championship", "Modern Event"]
        ):
            return "High Power"

        # Optimized indicators
        if any(keyword in deck_type for keyword in ["Challenger Deck", "Event Deck"]):
            return "Optimized"

        # Focused indicators
        if any(keyword in deck_type for keyword in ["Premium Deck", "Commander Deck"]):
            return "Focused"

        # Casual indicators
        if any(
            keyword in deck_type
            for keyword in ["Intro Pack", "Theme Deck", "Starter", "Welcome"]
        ):
            return "Casual"

        return "Unknown"


class AdvancedDeckFilter:
    """Advanced filtering functionality for complex deck queries."""

    def __init__(self, deck_list: List["MTGDeck"]):
        """
        Initialize with a deck list.

        Args:
            deck_list: List of MTGDeck objects
        """
        self.deck_list = deck_list
        self.filters = DeckFilters()

    def multi_filter(
        self,
        categories: Optional[List[str]] = None,
        formats: Optional[List[str]] = None,
        eras: Optional[List[str]] = None,
        power_levels: Optional[List[str]] = None,
        color_requirements: Optional[Dict[str, Any]] = None,
        text_search: Optional[str] = None,
        exclude_secret_lair: bool = False,
        commander_only: bool = False,
    ) -> List["MTGDeck"]:
        """
        Apply multiple filters simultaneously.

        Args:
            categories: List of deck categories to include
            formats: List of formats to include
            eras: List of eras to include
            power_levels: List of power levels to include
            color_requirements: Color filtering requirements
            text_search: Text to search in deck names
            exclude_secret_lair: Exclude Secret Lair products
            commander_only: Only include Commander products

        Returns:
            Filtered deck list
        """
        filtered = self.deck_list.copy()

        # Category filter
        if categories:
            filtered = [
                deck
                for deck in filtered
                if self.filters.categorize_deck_type(getattr(deck, "type", ""))
                in categories
            ]

        # Format filter (requires inference)
        if formats:
            filtered = [
                deck
                for deck in filtered
                if self.filters.infer_format(deck._data) in formats
            ]

        # Era filter
        if eras:
            filtered = [
                deck
                for deck in filtered
                if self.filters.get_era_from_date(getattr(deck, "releaseDate", ""))
                in eras
            ]

        # Power level filter
        if power_levels:
            filtered = [
                deck
                for deck in filtered
                if self.filters.filter_by_power_level(deck._data) in power_levels
            ]

        # Text search
        if text_search:
            search_lower = text_search.lower()
            filtered = [
                deck
                for deck in filtered
                if search_lower in getattr(deck, "name", "").lower()
            ]

        # Secret Lair exclusion
        if exclude_secret_lair:
            filtered = [
                deck for deck in filtered if not self.filters.is_secret_lair(deck._data)
            ]

        # Commander only
        if commander_only:
            filtered = [
                deck
                for deck in filtered
                if self.filters.is_commander_product(deck._data)
            ]

        return filtered

    def get_filter_statistics(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics about the deck list for filter UI population.

        Returns:
            Dictionary with counts for each filter category
        """
        stats = {
            "categories": {},
            "formats": {},
            "eras": {},
            "power_levels": {},
            "types": {},
        }

        for deck in self.deck_list:
            # Category stats
            category = self.filters.categorize_deck_type(getattr(deck, "type", ""))
            stats["categories"][category] = stats["categories"].get(category, 0) + 1

            # Format stats
            format_name = self.filters.infer_format(deck._data)
            stats["formats"][format_name] = stats["formats"].get(format_name, 0) + 1

            # Era stats
            era = self.filters.get_era_from_date(getattr(deck, "releaseDate", ""))
            stats["eras"][era] = stats["eras"].get(era, 0) + 1

            # Power level stats
            power = self.filters.filter_by_power_level(deck._data)
            stats["power_levels"][power] = stats["power_levels"].get(power, 0) + 1

            # Type stats
            deck_type = getattr(deck, "type", "Unknown")
            stats["types"][deck_type] = stats["types"].get(deck_type, 0) + 1

        return stats

    def search_decks(
        self, query: str, search_fields: Optional[List[str]] = None
    ) -> List["MTGDeck"]:
        """
        Search decks using a text query across multiple fields.

        Args:
            query: Search query string
            search_fields: List of fields to search in (default: name, type, code)

        Returns:
            List of matching decks
        """
        if search_fields is None:
            search_fields = ["name", "type", "code"]

        query_lower = query.lower()
        results = []

        for deck in self.deck_list:
            match = False
            for field in search_fields:
                field_value = str(getattr(deck, field, "")).lower()
                if query_lower in field_value:
                    match = True
                    break

            if match:
                results.append(deck)

        return results

    def get_recent_decks(self, limit: int = 50, days: int = 365) -> List["MTGDeck"]:
        """
        Get recently released decks.

        Args:
            limit: Maximum number of decks to return
            days: Number of days back to consider "recent"

        Returns:
            List of recent decks sorted by release date
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_decks = []
        for deck in self.deck_list:
            release_date_str = getattr(deck, "releaseDate", "")
            if release_date_str:
                try:
                    release_date = datetime.strptime(release_date_str, "%Y-%m-%d")
                    if release_date >= cutoff_date:
                        recent_decks.append(deck)
                except ValueError:
                    continue

        # Sort by release date (newest first)
        recent_decks.sort(key=lambda x: getattr(x, "releaseDate", ""), reverse=True)

        return recent_decks[:limit]


# Convenience functions for common filtering operations
def get_commander_decks(deck_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter for Commander decks only."""
    return [deck for deck in deck_list if DeckFilters.is_commander_product(deck)]


def get_standard_legal_decks(deck_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter for Standard-legal deck products."""
    filter_obj = AdvancedDeckFilter(deck_list)
    return filter_obj.multi_filter(formats=["Standard"])


def get_premium_products(deck_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter for premium/collector products."""
    filter_obj = AdvancedDeckFilter(deck_list)
    return filter_obj.multi_filter(categories=["Premium"])


def search_by_theme(
    deck_list: List[Dict[str, Any]], theme: str
) -> List[Dict[str, Any]]:
    """Search decks by theme/archetype name."""
    filter_obj = AdvancedDeckFilter(deck_list)
    return filter_obj.search_decks(theme, search_fields=["name"])


if __name__ == "__main__":
    # Example usage
    print("Testing deck filters...")

    # Mock deck data for testing
    sample_decks = [
        {
            "name": "Adaptive Enchantment",
            "type": "Commander Deck",
            "code": "C18",
            "releaseDate": "2018-08-10",
            "fileName": "AdaptiveEnchantment_C18",
        },
        {
            "name": "Lightning Aggro",
            "type": "Challenger Deck",
            "code": "Q02",
            "releaseDate": "2019-04-12",
            "fileName": "LightningAggro_Q02",
        },
        {
            "name": "Hidden Pathways",
            "type": "Secret Lair Drop",
            "code": "SLD",
            "releaseDate": "2021-05-07",
            "fileName": "HiddenPathways_SLD",
        },
    ]

    # Test categorization
    filters = DeckFilters()
    for deck in sample_decks:
        category = filters.categorize_deck_type(deck["type"])
        format_name = filters.infer_format(deck)
        era = filters.get_era_from_date(deck["releaseDate"])
        power = filters.filter_by_power_level(deck)

        print(f"{deck['name']}: {category}, {format_name}, {era}, {power}")

    # Test advanced filtering
    advanced_filter = AdvancedDeckFilter(sample_decks)
    commander_only = advanced_filter.multi_filter(commander_only=True)
    print(f"\nCommander decks: {len(commander_only)}")

    no_secret_lair = advanced_filter.multi_filter(exclude_secret_lair=True)
    print(f"Non-Secret Lair decks: {len(no_secret_lair)}")

    stats = advanced_filter.get_filter_statistics()
    print(f"\nFilter statistics: {stats}")
