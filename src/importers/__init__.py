"""Deck import modules for various websites."""

from .moxfield_scraper import MoxfieldScraper
from .mtgjson_scraper import MTGJsonScraper, get_mtgjson_precons

__all__ = ["MoxfieldScraper", "MTGJsonScraper", "get_mtgjson_precons"]
