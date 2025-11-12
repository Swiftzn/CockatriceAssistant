"""deck_import_init.py

Initialize and register all deck import scrapers.
"""

import sys
from pathlib import Path

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from importers.deck_import import deck_import_manager
from importers.moxfield_import import MoxfieldImportScraper
from importers.mtggoldfish_import import MTGGoldfishImportScraper


def initialize_deck_importers():
    """Register all available deck import scrapers."""
    # Register Moxfield scraper
    deck_import_manager.register_scraper(MoxfieldImportScraper())

    # Register MTGGoldfish scraper
    deck_import_manager.register_scraper(MTGGoldfishImportScraper())

    print(
        f"Initialized deck importers for: {', '.join(deck_import_manager.get_supported_sites())}"
    )


# Auto-initialize when imported
initialize_deck_importers()
