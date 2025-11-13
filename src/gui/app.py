"""Cockatrice Assistant - Precon Deck Importer

Features implemented:
- Fetch commander precon decklists from curated sources
- Convert precons to Cockatrice .cod format with commanders in sideboard
- Save decks to Cockatrice deck folder or custom location
- Template download placeholder
"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
import os
import webbrowser
import winreg
import sys
import os
from pathlib import Path

# Add src directory to path for imports when run via main.py
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.deck_parser import write_cod, CockatriceDeck
from utils.templates import (
    download_template,
    get_curated_themes,
    download_and_install_theme,
    get_default_themes_folder,
    get_installed_theme_info,
    clear_remote_themes_cache,
)
from importers.mtgjson_scraper import MTGJsonScraper
from utils.deck_filters import AdvancedDeckFilter, DeckFilters
import threading
from core.updater import update_manager, check_for_updates, get_current_version
from core.version import APP_NAME, APP_DESCRIPTION, GITHUB_REPO_URL

# Import universal deck import system
from importers.deck_import import deck_import_manager, convert_universal_to_cockatrice
import importers.deck_import_init  # This initializes all scrapers


def detect_cockatrice_installation():
    """Detect if Cockatrice is installed on Windows."""
    # Common installation paths
    common_paths = [
        Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Cockatrice",
        Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"))
        / "Cockatrice",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Cockatrice",
        Path(os.environ.get("APPDATA", "")) / "Cockatrice",
    ]

    # Check for Cockatrice executable
    for base_path in common_paths:
        if base_path.exists():
            exe_path = base_path / "cockatrice.exe"
            if exe_path.exists():
                return True, str(base_path)

    # Check Windows registry for installation info
    try:
        import winreg

        registry_keys = [
            (
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            ),
        ]

        for hkey, reg_path in registry_keys:
            try:
                with winreg.OpenKey(hkey, reg_path) as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display_name = winreg.QueryValueEx(
                                        subkey, "DisplayName"
                                    )[0]
                                    if "cockatrice" in display_name.lower():
                                        install_location = winreg.QueryValueEx(
                                            subkey, "InstallLocation"
                                        )[0]
                                        if Path(install_location).exists():
                                            return True, install_location
                                except FileNotFoundError:
                                    pass
                            i += 1
                        except OSError:
                            break
            except (OSError, FileNotFoundError):
                continue
    except ImportError:
        pass  # winreg not available (non-Windows)

    return False, None


def get_cockatrice_download_info():
    """Get information about downloading Cockatrice."""
    return {
        "official_site": "https://cockatrice.github.io/",
    }


def get_default_cockatrice_decks_path():
    """Get the default Cockatrice decks path for the current user."""
    try:
        # Try to use user's home directory
        user_home = Path.home()

        # Common Cockatrice deck paths
        possible_paths = [
            user_home / "AppData" / "Local" / "Cockatrice" / "Cockatrice" / "decks",
            user_home / ".local" / "share" / "Cockatrice" / "decks",  # Linux
            user_home
            / "Library"
            / "Application Support"
            / "Cockatrice"
            / "decks",  # macOS
            user_home / "Documents" / "Cockatrice Decks",  # Fallback
            Path.cwd() / "decks",  # Current directory fallback
        ]

        # Return the first path that exists, or create the first one if none exist
        for path in possible_paths:
            if path.exists():
                return str(path)

        # If none exist, try to create the first Windows path or fallback to Documents
        try:
            default_path = (
                possible_paths[0]
                if os.name == "nt"
                else user_home / "Documents" / "Cockatrice Decks"
            )
            default_path.mkdir(parents=True, exist_ok=True)
            return str(default_path)
        except (OSError, PermissionError):
            # Final fallback to current directory
            fallback_path = Path.cwd() / "decks"
            fallback_path.mkdir(exist_ok=True)
            return str(fallback_path)

    except Exception as e:
        print(f"Error determining default decks path: {e}")
        # Ultimate fallback
        return str(Path.cwd() / "decks")


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Cockatrice Assistant v{get_current_version()}")
        self.root.geometry("1000x700")

        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Deck import tab
        deck_frame = ttk.Frame(notebook)
        notebook.add(deck_frame, text="Decks")

        # Button frame
        btn_frame = ttk.Frame(deck_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        self.import_url_btn = ttk.Button(
            btn_frame, text="Import from URL", command=self.import_from_url
        )
        self.import_url_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Cache status label
        self.cache_status_label = ttk.Label(btn_frame, text="", foreground="gray")
        self.cache_status_label.pack(side=tk.RIGHT, padx=(5, 0))

        self.select_all_btn = ttk.Button(
            btn_frame, text="Select All", command=self.select_all
        )
        self.select_all_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.export_btn = ttk.Button(
            btn_frame, text="Import Selected", command=self.export_selected
        )
        self.export_btn.pack(side=tk.LEFT)

        # Filtering frame
        filter_frame = ttk.LabelFrame(deck_frame, text="Filters")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        # Format filter frame
        source_frame = ttk.Frame(filter_frame)
        source_frame.pack(fill=tk.X, padx=5, pady=2)

        # Format filter
        ttk.Label(source_frame, text="Format:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="All Formats")
        self.format_combo = ttk.Combobox(
            source_frame,
            textvariable=self.format_var,
            values=["All Formats"],  # Will be populated later
            state="readonly",
            width=20,
        )
        self.format_combo.pack(side=tk.LEFT, padx=(5, 15))
        self.format_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)

        # Search functionality
        ttk.Label(source_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            source_frame,
            textvariable=self.search_var,
            width=25,
        )
        self.search_entry.pack(side=tk.LEFT, padx=(5, 10))
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)

        # Clear search button
        self.clear_search_btn = ttk.Button(
            source_frame,
            text="Clear",
            command=self.clear_search,
            width=8,
        )
        self.clear_search_btn.pack(side=tk.LEFT, padx=(5, 0))

        # Save path frame
        save_frame = ttk.Frame(deck_frame)
        save_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(save_frame, text="Save to:").pack(side=tk.LEFT)
        self.save_path = ttk.Entry(save_frame)
        self.save_path.insert(0, get_default_cockatrice_decks_path())
        self.save_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))

        self.browse_btn = ttk.Button(
            save_frame, text="Browse", command=self.browse_save_path
        )
        self.browse_btn.pack(side=tk.RIGHT)

        # Cockatrice status frame
        cockatrice_frame = ttk.LabelFrame(deck_frame, text="Cockatrice Installation")
        cockatrice_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        cockatrice_info_frame = ttk.Frame(cockatrice_frame)
        cockatrice_info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.cockatrice_status_label = ttk.Label(
            cockatrice_info_frame, text="Checking Cockatrice installation..."
        )
        self.cockatrice_status_label.pack(side=tk.LEFT)

        self.get_cockatrice_btn = ttk.Button(
            cockatrice_info_frame,
            text="Get Cockatrice",
            command=self.open_cockatrice_download,
            state="disabled",
        )
        self.get_cockatrice_btn.pack(side=tk.RIGHT, padx=(5, 0))

        self.refresh_cockatrice_btn = ttk.Button(
            cockatrice_info_frame,
            text="Refresh",
            command=self.check_cockatrice_installation,
        )
        self.refresh_cockatrice_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # List frame with scrollbar
        list_frame = ttk.Frame(deck_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(
            list_frame,
            columns=("deck_type", "release_date", "format"),
            show="tree headings",
        )
        self.tree.heading(
            "#0", text="Deck Name", command=lambda: self.sort_column("#0", False)
        )
        self.tree.heading(
            "deck_type",
            text="Deck Type",
            command=lambda: self.sort_column("deck_type", False),
        )
        self.tree.heading(
            "release_date",
            text="Release Date",
            command=lambda: self.sort_column("release_date", False),
        )
        self.tree.heading(
            "format", text="Format", command=lambda: self.sort_column("format", False)
        )

        # Set column widths
        self.tree.column("#0", width=400, minwidth=250)
        self.tree.column("deck_type", width=150, minwidth=120)
        self.tree.column("release_date", width=120, minwidth=100)
        self.tree.column("format", width=120, minwidth=100)

        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Themes tab
        themes_frame = ttk.Frame(notebook)
        notebook.add(themes_frame, text="Themes")

        # Themes folder setting
        themes_folder_frame = ttk.Frame(themes_frame)
        themes_folder_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(themes_folder_frame, text="Cockatrice Themes Folder:").pack(
            anchor=tk.W
        )

        themes_path_frame = ttk.Frame(themes_folder_frame)
        themes_path_frame.pack(fill=tk.X, pady=(2, 0))

        self.themes_path = ttk.Entry(themes_path_frame)
        self.themes_path.insert(0, get_default_themes_folder())
        self.themes_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            themes_path_frame, text="Browse", command=self.browse_themes_folder
        ).pack(side=tk.RIGHT, padx=(5, 0))

        # Curated themes section
        curated_frame = ttk.LabelFrame(themes_frame, text="Curated Themes")
        curated_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(10, 5))

        # Themes list
        themes_list_frame = ttk.Frame(curated_frame)
        themes_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.themes_tree = ttk.Treeview(
            themes_list_frame,
            columns=("version", "author", "description"),
            show="tree headings",
        )
        self.themes_tree.heading("#0", text="Theme Name")
        self.themes_tree.heading("version", text="Version")
        self.themes_tree.heading("author", text="Author")
        self.themes_tree.heading("description", text="Description")

        # Set column widths
        self.themes_tree.column("#0", width=120, minwidth=100)
        self.themes_tree.column("version", width=80, minwidth=60)
        self.themes_tree.column("author", width=100, minwidth=80)
        self.themes_tree.column("description", width=300, minwidth=200)

        themes_scrollbar = ttk.Scrollbar(
            themes_list_frame, orient=tk.VERTICAL, command=self.themes_tree.yview
        )
        self.themes_tree.configure(yscrollcommand=themes_scrollbar.set)

        self.themes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        themes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons frame
        themes_btn_frame = ttk.Frame(curated_frame)
        themes_btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.install_theme_btn = ttk.Button(
            themes_btn_frame,
            text="Install Selected Theme",
            command=self.install_selected_theme,
        )
        self.install_theme_btn.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            themes_btn_frame,
            text="Refresh Themes List",
            command=self.refresh_themes_list,
        ).pack(side=tk.LEFT)

        # Custom theme section
        custom_frame = ttk.LabelFrame(themes_frame, text="Custom Theme URL")
        custom_frame.pack(fill=tk.X, padx=5, pady=(5, 5))

        custom_url_frame = ttk.Frame(custom_frame)
        custom_url_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(custom_url_frame, text="Theme ZIP URL:").pack(anchor=tk.W)
        self.custom_theme_url = ttk.Entry(custom_url_frame)
        self.custom_theme_url.pack(fill=tk.X, pady=(2, 5))

        ttk.Label(custom_url_frame, text="Theme Name:").pack(anchor=tk.W)
        self.custom_theme_name = ttk.Entry(custom_url_frame)
        self.custom_theme_name.pack(fill=tk.X, pady=(2, 5))

        ttk.Button(
            custom_url_frame,
            text="Install Custom Theme",
            command=self.install_custom_theme,
        ).pack(pady=(5, 0))

        # Load curated themes
        self.refresh_themes_list()

        # About tab
        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="About")

        # Application info section
        app_info_frame = ttk.LabelFrame(about_frame, text="Application Information")
        app_info_frame.pack(fill=tk.X, padx=5, pady=5)

        info_content_frame = ttk.Frame(app_info_frame)
        info_content_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(
            info_content_frame,
            text=APP_NAME,
            font=("TkDefaultFont", 12, "bold"),
        ).pack(anchor=tk.W)

        ttk.Label(
            info_content_frame,
            text=f"Version: {get_current_version()}",
            font=("TkDefaultFont", 10),
        ).pack(anchor=tk.W, pady=(2, 0))

        ttk.Label(
            info_content_frame,
            text=APP_DESCRIPTION,
            font=("TkDefaultFont", 9),
        ).pack(anchor=tk.W, pady=(5, 0))

        # Links frame
        links_frame = ttk.Frame(info_content_frame)
        links_frame.pack(anchor=tk.W, pady=(10, 0))

        ttk.Button(
            links_frame,
            text="View on GitHub",
            command=lambda: webbrowser.open(GITHUB_REPO_URL),
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            links_frame,
            text="Report Issues",
            command=lambda: webbrowser.open(f"{GITHUB_REPO_URL}/issues"),
        ).pack(side=tk.LEFT)

        # Update section
        update_info_frame = ttk.LabelFrame(about_frame, text="Updates")
        update_info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 5))

        update_content_frame = ttk.Frame(update_info_frame)
        update_content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Update status label
        self.update_status_label = ttk.Label(
            update_content_frame,
            text="Checking for updates...",
            font=("TkDefaultFont", 9),
        )
        self.update_status_label.pack(anchor=tk.W, pady=(0, 10))

        # Update buttons frame
        update_buttons_frame = ttk.Frame(update_content_frame)
        update_buttons_frame.pack(anchor=tk.W, pady=(5, 0))

        self.check_updates_btn = ttk.Button(
            update_buttons_frame,
            text="Check for Updates",
            command=self.check_for_updates,
        )
        self.check_updates_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.download_update_btn = ttk.Button(
            update_buttons_frame,
            text="Download Update",
            command=self.download_update,
            state="disabled",
        )
        self.download_update_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.view_releases_btn = ttk.Button(
            update_buttons_frame,
            text="View All Releases",
            command=lambda: update_manager.open_releases_page(),
        )
        self.view_releases_btn.pack(side=tk.LEFT)

        # Release notes frame
        notes_frame = ttk.LabelFrame(update_content_frame, text="Release Notes")
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Release notes text widget with scrollbar
        notes_text_frame = ttk.Frame(notes_frame)
        notes_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.release_notes_text = tk.Text(
            notes_text_frame,
            wrap=tk.WORD,
            height=8,
            state=tk.DISABLED,
            font=("TkDefaultFont", 8),
        )

        notes_scrollbar = ttk.Scrollbar(
            notes_text_frame, orient=tk.VERTICAL, command=self.release_notes_text.yview
        )
        self.release_notes_text.configure(yscrollcommand=notes_scrollbar.set)

        self.release_notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        notes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Store update information
        self.update_info = None

        # Status bar
        self.status_bar = ttk.Label(
            self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.card_items = []  # Track card items for selection
        self.mtgjson_scraper = MTGJsonScraper()
        self.deck_filters = DeckFilters()
        self.precon_decks = []  # List of MTGJSON precon decks
        self.sort_reverse = {}  # Track sort direction for each column

        # Check Cockatrice installation on startup
        self.root.after(100, self.check_cockatrice_installation)

        # Load cached decks on startup
        self.root.after(200, self.load_initial_decks)

    def sort_column(self, column, reverse):
        """Sort TreeView contents by the specified column."""
        # Get all items with their values
        items = [
            (
                (
                    self.tree.set(k, column)
                    if column != "#0"
                    else self.tree.item(k, "text")
                ),
                k,
            )
            for k in self.tree.get_children("")
        ]

        # Handle sorting for different column types
        if column == "release_date":
            # Sort dates properly
            items.sort(key=lambda x: x[0] if x[0] else "", reverse=reverse)
        else:
            # Sort text normally
            items.sort(key=lambda x: x[0].lower() if x[0] else "", reverse=reverse)

        # Rearrange items in sorted positions
        for index, (val, k) in enumerate(items):
            self.tree.move(k, "", index)

        # Update sort direction for next click
        self.sort_reverse[column] = not reverse

        # Update heading to show sort direction
        for col in ["#0", "deck_type", "release_date", "format"]:
            if col == column:
                direction = " ↓" if reverse else " ↑"
                current_text = self.tree.heading(col)["text"]
                # Remove existing arrows
                clean_text = current_text.replace(" ↑", "").replace(" ↓", "")
                self.tree.heading(col, text=clean_text + direction)
                # Update command for next click
                self.tree.heading(
                    col,
                    command=lambda c=col: self.sort_column(
                        c, self.sort_reverse.get(c, False)
                    ),
                )
            else:
                # Remove arrows from other columns
                current_text = self.tree.heading(col)["text"]
                clean_text = current_text.replace(" ↑", "").replace(" ↓", "")
                self.tree.heading(col, text=clean_text)
                self.tree.heading(col, command=lambda c=col: self.sort_column(c, False))

    def on_filter_changed(self, event=None):
        """Handle filter changes for MTGJSON."""
        self.apply_mtgjson_filters()

    def on_search_changed(self, event=None):
        """Handle search text changes."""
        self.apply_mtgjson_filters()

    def clear_search(self):
        """Clear the search field and refresh the list."""
        self.search_var.set("")
        self.apply_mtgjson_filters()

    def update_mtgjson_formats(self):
        """Update format combobox with available MTGJSON formats."""
        try:
            # Get formats from the currently loaded decks
            if not self.precon_decks:
                return

            formats = {}
            for deck in self.precon_decks:
                format_name = self.deck_filters.infer_format(deck._data)
                formats[format_name] = formats.get(format_name, 0) + 1

            # Sort formats by popularity (most decks first)
            sorted_formats = sorted(formats.items(), key=lambda x: x[1], reverse=True)
            format_names = [f[0] for f in sorted_formats]

            # Add "All Formats" option
            values = ["All Formats"] + format_names
            self.format_combo["values"] = values
        except Exception as e:
            print(f"Error updating formats: {e}")

    def apply_mtgjson_filters(self):
        """Apply current filters to MTGJSON deck list."""
        if not self.precon_decks:
            return

        try:
            # Start with all precon decks (already excludes Secret Lair Drop)
            filtered_decks = self.precon_decks.copy()

            # Filter by format if specified
            format_filter = self.format_var.get()
            if format_filter != "All Formats":
                filtered_decks = [
                    deck
                    for deck in filtered_decks
                    if self.deck_filters.infer_format(deck._data) == format_filter
                ]

            # Filter by search term if specified
            search_term = self.search_var.get().strip().lower()
            if search_term:
                filtered_decks = [
                    deck
                    for deck in filtered_decks
                    if search_term in getattr(deck, "name", "").lower()
                    or search_term in getattr(deck, "code", "").lower()
                    or search_term in getattr(deck, "type", "").lower()
                ]

            # Update display
            self._display_filtered_decks(filtered_decks)

        except Exception as e:
            self.status_bar.config(text=f"Error applying filters: {e}")

    def _update_mtgjson_list(self, decks):
        """Update UI with filtered MTGJSON decks."""
        # Filter out Secret Lair Drop decks by default
        filtered_decks = [
            deck for deck in decks if getattr(deck, "type", "") != "Secret Lair Drop"
        ]

        # Store decks and sort by release date (newest first)
        self.precon_decks = sorted(
            filtered_decks, key=lambda x: getattr(x, "releaseDate", ""), reverse=True
        )

        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.card_items.clear()

        # Add MTGJSON decks to tree
        for i, deck in enumerate(self.precon_decks):
            deck_name = getattr(deck, "name", "Unknown Deck")
            deck_type = getattr(deck, "type", "Unknown")
            release_date = getattr(deck, "releaseDate", "")
            code = getattr(deck, "code", "")

            # Infer format
            format_name = self.deck_filters.infer_format(deck._data)

            # Build display text
            deck_text = deck_name
            if code:
                deck_text += f" ({code})"

            item_id = self.tree.insert(
                "",
                "end",
                text=deck_text,
                values=(deck_type, release_date, format_name),
            )
            self.card_items.append((item_id, "precon", i))

        self._reset_precon_buttons()
        count = len(decks)
        self.status_bar.config(
            text=f"Loaded {count} MTGJSON decks with current filters"
        )

        # Update formats dropdown after loading decks
        self.update_mtgjson_formats()

        # Check for updates on startup (silent check using cache)
        self.root.after(500, self.check_for_updates_silent)

    def load_initial_decks(self):
        """Load decks on app startup, updating cache only if needed."""
        self.import_url_btn.config(state="disabled")

        def load_in_thread():
            try:
                # Check if cache needs updating
                metadata = self.mtgjson_scraper._load_cache_metadata()
                cache_is_valid = self.mtgjson_scraper._is_cache_valid(
                    metadata.get("last_decklist_fetch", 0)
                )

                if cache_is_valid:
                    # Cache is still fresh, use it
                    self.root.after(
                        0, lambda: self.status_bar.config(text="Loading from cache...")
                    )
                    decks = self.mtgjson_scraper.fetch_deck_list(force_refresh=False)
                    cache_age_hours = (
                        __import__("time").time()
                        - metadata.get("last_decklist_fetch", 0)
                    ) / 3600
                    status_msg = f"Loaded {len(decks)} decks from cache (cache age: {cache_age_hours:.1f}h)"
                else:
                    # Cache is stale or missing, update it
                    self.root.after(
                        0, lambda: self.status_bar.config(text="Updating deck list...")
                    )
                    decks = self.mtgjson_scraper.fetch_deck_list(force_refresh=True)
                    status_msg = f"Updated and loaded {len(decks)} decks from MTGJSON"

                if decks:
                    # Update UI in main thread
                    self.root.after(0, lambda: self._update_mtgjson_list(decks))
                    self.root.after(100, self.update_mtgjson_formats)
                    self.root.after(0, lambda: self.status_bar.config(text=status_msg))
                else:
                    # No decks loaded - this shouldn't happen with valid cache
                    self.root.after(
                        0,
                        lambda: self._set_status_message(
                            "Failed to load deck data. Please check your internet connection.",
                            "error",
                        ),
                    )

            except Exception as e:
                # Error occurred - try to fall back to cache
                try:
                    cached_decks = self.mtgjson_scraper.fetch_deck_list(
                        force_refresh=False
                    )
                    if cached_decks:
                        self.root.after(
                            0, lambda: self._update_mtgjson_list(cached_decks)
                        )
                        self.root.after(
                            0,
                            lambda: self._set_status_message(
                                f"Using cached data due to error: {e}",
                                "warning",
                            ),
                        )
                    else:
                        self.root.after(
                            0,
                            lambda: self._set_status_message(
                                f"Could not load decks: {e}",
                                "error",
                            ),
                        )
                except Exception as cache_error:
                    self.root.after(
                        0,
                        lambda: self._set_status_message(
                            f"Failed to load any deck data: {cache_error}",
                            "error",
                        ),
                    )
            finally:
                # Re-enable buttons
                self.root.after(0, lambda: self.import_url_btn.config(state="normal"))

        threading.Thread(target=load_in_thread, daemon=True).start()

    def _display_filtered_decks(self, decks):
        """Display a filtered list of decks in the TreeView."""
        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.card_items.clear()

        # Add filtered decks to tree
        for i, deck in enumerate(decks):
            deck_name = getattr(deck, "name", "Unknown Deck")
            deck_type = getattr(deck, "type", "Unknown")
            release_date = getattr(deck, "releaseDate", "")
            code = getattr(deck, "code", "")

            # Infer format
            format_name = self.deck_filters.infer_format(deck._data)

            # Build display text
            deck_text = deck_name
            if code:
                deck_text += f" ({code})"

            item_id = self.tree.insert(
                "",
                "end",
                text=deck_text,
                values=(deck_type, release_date, format_name),
            )
            # Find the original index in precon_decks for this deck
            original_index = next(
                (
                    j
                    for j, original_deck in enumerate(self.precon_decks)
                    if original_deck == deck
                ),
                i,
            )
            self.card_items.append((item_id, "precon", original_index))

        self._reset_precon_buttons()
        count = len(decks)
        total_count = len(self.precon_decks)
        if count == total_count:
            self.status_bar.config(text=f"Showing all {count} decks")
        else:
            self.status_bar.config(text=f"Showing {count} of {total_count} decks")

    def import_from_url(self):
        """Import a deck from any supported deck list website."""
        # Create a dialog to get the URL
        dialog = tk.Toplevel(self.root)
        dialog.title("Import from URL")
        dialog.geometry("500x250")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.geometry(
            "+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50)
        )

        ttk.Label(
            dialog, text="Import Deck from URL", font=("TkDefaultFont", 12, "bold")
        ).pack(pady=10)

        # Show supported sites
        supported_sites = deck_import_manager.get_supported_sites()
        sites_text = f"Supported sites: {', '.join(supported_sites)}"
        ttk.Label(dialog, text=sites_text, font=("TkDefaultFont", 9)).pack(pady=(0, 5))

        ttk.Label(dialog, text="Enter a deck URL:").pack(pady=5)

        url_entry = ttk.Entry(dialog, width=60)
        url_entry.pack(pady=5, padx=20, fill="x")
        url_entry.focus()

        # Buttons frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)

        def import_deck():
            url = url_entry.get().strip()
            if not url:
                self._set_status_message("Please enter a URL", "warning")
                return

            # Check if URL is supported
            is_supported, site_name = deck_import_manager.is_supported_url(url)
            if not is_supported:
                supported_sites = deck_import_manager.get_supported_sites()
                self._set_status_message(
                    f"URL not supported. Supported sites: {', '.join(supported_sites)}",
                    "warning",
                )
                return

            dialog.destroy()
            self._import_deck_from_url(url, site_name)

        ttk.Button(btn_frame, text="Import", command=import_deck).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(
            side="left", padx=5
        )

    def _import_deck_from_url(self, url, site_name):
        """Import a single deck from URL using universal import system."""
        self.import_url_btn.config(text="Importing...", state="disabled")
        self.status_bar.config(text=f"Importing deck from {site_name}...")

        def import_in_thread():
            try:
                # Fetch deck using universal import system
                deck = deck_import_manager.fetch_deck(url)
                if not deck:
                    self.root.after(
                        0,
                        lambda: self._set_status_message(
                            f"Failed to fetch deck from {site_name}", "error"
                        ),
                    )
                    return

                # Convert to Cockatrice format
                cockatrice_deck = convert_universal_to_cockatrice(deck)

                # Get and validate save directory
                save_path_str = self.save_path.get().strip()
                if not save_path_str:
                    error_msg = (
                        "Save directory is empty. Please select a valid directory."
                    )
                    self.root.after(
                        0, lambda: self._set_status_message(error_msg, "error")
                    )
                    return

                save_dir = Path(save_path_str)
                print(f"Attempting to create directory: {save_dir}")
                save_dir.mkdir(parents=True, exist_ok=True)

                # Clean up filename - remove "Decklist", parentheses, and replace spaces with underscores
                clean_name = (
                    cockatrice_deck.deckname.replace("Decklist", "")
                    .replace("(", "")
                    .replace(")", "")
                    .replace(" ", "_")
                    .strip("_")
                )
                # Remove any double underscores
                while "__" in clean_name:
                    clean_name = clean_name.replace("__", "_")

                # Sanitize filename for file system safety
                import re

                # Remove invalid filename characters
                clean_name = re.sub(r'[<>:"/\\|?*]', "", clean_name)
                # Limit length to prevent path too long errors
                if len(clean_name) > 100:
                    clean_name = clean_name[:100]
                # Ensure it's not empty
                if not clean_name or clean_name.isspace():
                    clean_name = "imported_deck"

                filename = f"{clean_name}.cod"
                out_path = save_dir / filename

                print(f"Attempting to write file: {out_path}")
                write_cod(cockatrice_deck, str(out_path))
                print(f"Successfully wrote file: {out_path}")

                self.root.after(
                    0,
                    lambda: self._set_status_message(
                        f"Successfully imported '{deck.name}' from {site_name} to {out_path}",
                        "success",
                    ),
                )

            except Exception as e:
                import traceback

                # Get more detailed error information
                error_details = traceback.format_exc()
                print(f"Import error details:\n{error_details}")

                # Create user-friendly error message
                if (
                    "errno 2" in str(e).lower()
                    or "no such file or directory" in str(e).lower()
                ):
                    error_msg = f"Import failed: File or directory not found. Please check that the save directory exists and is writable. Error: {e}"
                elif "permission" in str(e).lower():
                    error_msg = f"Import failed: Permission denied. Please check that you have write access to the save directory. Error: {e}"
                else:
                    error_msg = f"Import failed: {e}"

                self.root.after(0, lambda: self._set_status_message(error_msg, "error"))
            finally:
                self.root.after(
                    0,
                    lambda: self.import_url_btn.config(
                        text="Import from URL", state="normal"
                    ),
                )

        threading.Thread(target=import_in_thread, daemon=True).start()

    def check_cockatrice_installation(self):
        """Check if Cockatrice is installed and update the UI accordingly."""
        try:
            is_installed, install_path = detect_cockatrice_installation()

            if is_installed:
                self.cockatrice_status_label.config(
                    text=f"✓ Cockatrice found: {install_path}", foreground="green"
                )
                self.get_cockatrice_btn.config(
                    state="disabled", text="Cockatrice Found"
                )
            else:
                self.cockatrice_status_label.config(
                    text="⚠ Cockatrice not detected", foreground="orange"
                )
                self.get_cockatrice_btn.config(state="normal", text="Get Cockatrice")
        except Exception as e:
            self.cockatrice_status_label.config(
                text="? Unable to check Cockatrice installation", foreground="gray"
            )
            self.get_cockatrice_btn.config(state="normal", text="Get Cockatrice")

    def open_cockatrice_download(self):
        """Open Cockatrice download page in browser."""
        try:
            download_info = get_cockatrice_download_info()

            # Create a simple dialog with download information
            dialog = tk.Toplevel(self.root)
            dialog.title("Get Cockatrice")
            dialog.geometry("450x320")
            dialog.transient(self.root)
            dialog.grab_set()

            # Center the dialog
            dialog.geometry(
                "+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50)
            )

            # Content
            ttk.Label(
                dialog,
                text="Cockatrice - Magic: The Gathering Game Client",
                font=("TkDefaultFont", 12, "bold"),
            ).pack(pady=15)

            info_text = """Cockatrice is a free, open-source Magic: The Gathering game client.
You need Cockatrice installed to use the decks imported by this assistant.

Click below to visit the official Cockatrice website where you can:
• Download the latest version for Windows
• Find installation instructions and guides
• Access documentation and support"""

            ttk.Label(dialog, text=info_text, justify="left", wraplength=400).pack(
                pady=15, padx=20
            )

            # Buttons frame
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(pady=15)

            def open_official():
                webbrowser.open(download_info["official_site"])
                self._set_status_message("Opened official Cockatrice website", "info")
                dialog.destroy()

            ttk.Button(
                btn_frame,
                text="Visit Cockatrice Website",
                command=open_official,
            ).pack(pady=5)

            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(
                pady=(10, 0)
            )

        except Exception as e:
            self._set_status_message(f"Failed to open download page: {e}", "error")

    def _reset_update_buttons(self):
        """Reset update buttons to normal state."""
        self.import_url_btn.config(state="normal")

    def _reset_precon_buttons(self):
        """Reset precon buttons to normal state (legacy method for compatibility)."""
        self._reset_update_buttons()

    def _update_cache_status(self):
        """Update the cache status display."""
        try:
            cache_file = self.mtgjson_scraper.decklist_cache
            if cache_file.exists():
                from datetime import datetime

                cache_modified = datetime.fromtimestamp(cache_file.stat().st_mtime)
                age_hours = (datetime.now() - cache_modified).total_seconds() / 3600

                if age_hours < 1:
                    status = f"Cache: {age_hours*60:.0f}m old"
                elif age_hours < 24:
                    status = f"Cache: {age_hours:.1f}h old"
                else:
                    status = f"Cache: {age_hours/24:.1f}d old"

                self.cache_status_label.config(text=status)
            else:
                self.cache_status_label.config(text="No cache")
        except Exception:
            self.cache_status_label.config(text="")

    def check_for_updates(self):
        """Check for application updates in background thread."""
        self.check_updates_btn.config(text="Checking...", state="disabled")
        self.update_status_label.config(text="Checking for updates...")
        self.download_update_btn.config(state="disabled")

        def check_in_thread():
            try:
                # Force fresh check (don't use cache)
                update_info = check_for_updates(use_cache=False)
                # Update UI in main thread
                self.root.after(0, self._handle_update_check_result, update_info)
            except Exception as e:
                self.root.after(0, self._handle_update_check_error, str(e))

        threading.Thread(target=check_in_thread, daemon=True).start()

    def _handle_update_check_result(self, update_info):
        """Handle update check results in main thread."""
        self.update_info = update_info
        self.check_updates_btn.config(text="Check for Updates", state="normal")

        if update_info.get("error"):
            self.update_status_label.config(
                text=f"Update check failed: {update_info['error']}", foreground="red"
            )
            self.release_notes_text.config(state=tk.NORMAL)
            self.release_notes_text.delete(1.0, tk.END)
            self.release_notes_text.insert(tk.END, "Failed to check for updates.")
            self.release_notes_text.config(state=tk.DISABLED)
            return

        if update_info.get("update_available"):
            current = update_info.get("current_version", "unknown")
            latest = update_info.get("latest_version", "unknown")
            self.update_status_label.config(
                text=f"🎉 Update available! {current} → {latest}",
                foreground="green",
            )
            self.download_update_btn.config(state="normal")
        else:
            current = update_info.get("current_version", "unknown")
            self.update_status_label.config(
                text=f"✅ You have the latest version ({current})",
                foreground="blue",
            )

        # Show release notes
        notes = update_info.get("release_notes", "")
        if notes:
            self.release_notes_text.config(state=tk.NORMAL)
            self.release_notes_text.delete(1.0, tk.END)

            # Clean up markdown formatting for display
            clean_notes = notes.replace("##", "").replace("**", "").replace("*", "")
            self.release_notes_text.insert(tk.END, clean_notes)
            self.release_notes_text.config(state=tk.DISABLED)
        else:
            self.release_notes_text.config(state=tk.NORMAL)
            self.release_notes_text.delete(1.0, tk.END)
            self.release_notes_text.insert(tk.END, "No release notes available.")
            self.release_notes_text.config(state=tk.DISABLED)

    def _handle_update_check_error(self, error_msg):
        """Handle update check errors in main thread."""
        self.check_updates_btn.config(text="Check for Updates", state="normal")
        self.update_status_label.config(
            text=f"Update check failed: {error_msg}", foreground="red"
        )

    def check_for_updates_silent(self):
        """Silently check for updates on startup (using cache)."""

        def check_in_thread():
            try:
                # Use cached results for startup check
                update_info = check_for_updates(use_cache=True)

                if update_info.get("update_available") and not update_info.get("error"):
                    # Update available - update UI in main thread
                    self.root.after(
                        0, self._handle_silent_update_available, update_info
                    )
                else:
                    # No update or error - just set default status
                    self.root.after(0, self._handle_silent_no_update, update_info)
            except Exception:
                # Ignore errors in silent check
                pass

        threading.Thread(target=check_in_thread, daemon=True).start()

    def _handle_silent_update_available(self, update_info):
        """Handle silent update check when update is available."""
        self.update_info = update_info
        current = update_info.get("current_version", "unknown")
        latest = update_info.get("latest_version", "unknown")

        # Update the status in About tab
        self.update_status_label.config(
            text=f"🎉 Update available! {current} → {latest} (Click 'Check for Updates' for details)",
            foreground="green",
        )

        # Show notification in status bar
        self._set_status_message(
            f"Update available: v{latest}. Check the About tab for details.",
            "info",
            duration=8000,
        )

    def _handle_silent_no_update(self, update_info):
        """Handle silent update check when no update is available."""
        if update_info.get("error"):
            # Error occurred - show minimal info
            self.update_status_label.config(
                text="Click 'Check for Updates' to check for new versions",
                foreground="gray",
            )
        else:
            # Up to date
            current = update_info.get("current_version", "unknown")
            self.update_status_label.config(
                text=f"Up to date (v{current})",
                foreground="blue",
            )

    def download_update(self):
        """Download and install update."""
        if not self.update_info or not self.update_info.get("download_url"):
            self._set_status_message("No update download URL available", "error")
            return

        download_url = self.update_info["download_url"]
        latest_version = self.update_info.get("latest_version", "unknown")

        self.download_update_btn.config(text="Downloading...", state="disabled")
        self._set_status_message(f"Downloading update v{latest_version}...", "info")

        def download_in_thread():
            try:

                def progress_callback(progress, downloaded, total):
                    # Update status with progress
                    mb_downloaded = downloaded / (1024 * 1024)
                    mb_total = total / (1024 * 1024)
                    self.root.after(
                        0,
                        lambda: self._set_status_message(
                            f"Downloading: {progress:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)",
                            "info",
                            duration=0,  # Don't auto-clear
                        ),
                    )

                # Download the update
                update_path = update_manager.download_update(
                    download_url, progress_callback
                )

                if update_path:
                    self.root.after(0, self._handle_download_success, update_path)
                else:
                    self.root.after(
                        0, lambda: self._handle_download_error("Download failed")
                    )

            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self._handle_download_error(error_msg))

        threading.Thread(target=download_in_thread, daemon=True).start()

    def _handle_download_success(self, update_path):
        """Handle successful update download."""
        self.download_update_btn.config(text="Download Update", state="normal")

        # Show installation dialog
        self._show_install_dialog(update_path)

    def _handle_download_error(self, error_msg):
        """Handle update download error."""
        self.download_update_btn.config(text="Download Update", state="normal")
        self._set_status_message(f"Download failed: {error_msg}", "error")

    def _show_install_dialog(self, update_path):
        """Show dialog to confirm update installation."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Install Update")
        dialog.geometry("500x350")  # Increased size to accommodate all content
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)  # Prevent resizing to maintain layout

        # Center the dialog properly
        dialog.update_idletasks()  # Ensure geometry is calculated
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (350 // 2)
        dialog.geometry(f"500x350+{x}+{y}")

        # Header with icon/title
        header_frame = ttk.Frame(dialog)
        header_frame.pack(pady=20, padx=20, fill="x")

        ttk.Label(
            header_frame,
            text="🎉 Update Ready to Install",
            font=("TkDefaultFont", 14, "bold"),
            anchor="center",
        ).pack()

        # Version info frame
        version_frame = ttk.Frame(dialog)
        version_frame.pack(pady=10, padx=20, fill="x")

        latest_version = self.update_info.get("latest_version", "unknown")
        current_version = get_current_version()

        ttk.Label(
            version_frame,
            text=f"Update: v{current_version} → v{latest_version}",
            font=("TkDefaultFont", 11, "bold"),
            anchor="center",
        ).pack()

        # Description frame
        desc_frame = ttk.Frame(dialog)
        desc_frame.pack(pady=15, padx=20, fill="both", expand=True)

        desc_text = """The update has been downloaded successfully and is ready to install.

This will:
• Replace the current application with the new version
• Close the current application
• Start the updated application automatically

Click 'Install Update' to proceed, or 'Cancel' to install later."""

        desc_label = ttk.Label(
            desc_frame,
            text=desc_text,
            justify="center",
            font=("TkDefaultFont", 9),
            anchor="center",
        )
        desc_label.pack(expand=True)

        # File info frame
        info_frame = ttk.Frame(dialog)
        info_frame.pack(pady=(0, 15), padx=20, fill="x")

        file_size_mb = update_path.stat().st_size / (1024 * 1024)
        file_info = f"Downloaded file size: {file_size_mb:.1f} MB"
        ttk.Label(
            info_frame,
            text=file_info,
            font=("TkDefaultFont", 8),
            foreground="gray",
            anchor="center",
        ).pack()

        # Buttons frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20, padx=20, fill="x")

        def install_now():
            dialog.destroy()
            # Get the current executable directory for installation
            current_exe_dir = self._get_current_exe_directory()
            if update_manager.install_update(update_path, current_exe_dir):
                self._set_status_message("Installing update...", "success")
                # Give a moment for the message to display
                self.root.after(1500, self.root.quit)
            else:
                self._set_status_message("Failed to install update", "error")

        def cancel_install():
            dialog.destroy()
            self._set_status_message(
                "Update cancelled. File saved in temporary location.", "info"
            )

        # Center the buttons horizontally
        button_container = ttk.Frame(btn_frame)
        button_container.pack(expand=True)

        install_btn = ttk.Button(
            button_container, text="Install Update", command=install_now, width=15
        )
        install_btn.pack(side="left", padx=10)

        cancel_btn = ttk.Button(
            button_container, text="Cancel", command=cancel_install, width=15
        )
        cancel_btn.pack(side="left", padx=10)

        # Set focus to Install button and make it the default
        install_btn.focus_set()
        dialog.bind("<Return>", lambda e: install_now())

    def _get_current_exe_directory(self):
        """Get the directory where the current executable is located."""
        try:
            import sys

            if getattr(sys, "frozen", False):
                # Running as PyInstaller executable
                return Path(sys.executable).parent
            else:
                # Running as Python script - use current directory
                return Path.cwd()
        except Exception:
            return Path.cwd()

    def run(self):
        self.root.mainloop()

    def select_all(self):
        # Toggle selection for all items
        for item_id, item_type, idx in self.card_items:
            self.tree.selection_add(item_id)

    def export_selected(self):
        """Import selected precon decks to .cod files."""
        self.export_precons()

    def browse_save_path(self):
        """Open directory browser to select save path."""
        path = filedialog.askdirectory(
            title="Select save directory", initialdir=self.save_path.get()
        )
        if path:
            self.save_path.delete(0, tk.END)
            self.save_path.insert(0, path)

    def export_precons(self):
        """Import selected precon decks to .cod files."""
        if not self.precon_decks:
            self.status_bar.config(
                text="No precon decks loaded. Please restart the application to reload."
            )
            return

        save_dir = Path(self.save_path.get())
        if not save_dir.exists():
            try:
                save_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.status_bar.config(text=f"Cannot create save directory: {e}")
                return

        selected_items = self.tree.selection()
        if not selected_items:
            self.status_bar.config(text="Please select precon decks to import.")
            return

        imported_count = 0

        # Process each selected precon deck
        for item_id, deck_type, idx in self.card_items:
            if item_id in selected_items and deck_type == "precon":
                deck = self.precon_decks[idx]

                # For MTGJSON decks, convert to Cockatrice format
                cockatrice_deck = deck.to_cockatrice()

                # Save as .cod file - remove "Decklist", parentheses, and replace spaces with underscores
                clean_name = (
                    cockatrice_deck.deckname.replace("Decklist", "")
                    .replace("(", "")
                    .replace(")", "")
                    .replace(" ", "_")
                    .strip("_")
                )
                # Remove any double underscores
                while "__" in clean_name:
                    clean_name = clean_name.replace("__", "_")
                filename = f"{clean_name}.cod"
                out_path = save_dir / filename

                try:
                    write_cod(cockatrice_deck, str(out_path))
                    imported_count += 1
                except Exception as e:
                    self.status_bar.config(text=f"Failed to write {filename}: {e}")
                    continue

        if imported_count > 0:
            self._set_status_message(
                f"Successfully imported {imported_count} deck(s) to {save_dir}",
                "success",
            )
        else:
            self._set_status_message("No decks were successfully imported.", "warning")

    def browse_themes_folder(self):
        """Browse for Cockatrice themes folder."""
        folder = filedialog.askdirectory(
            title="Select Cockatrice Themes Folder", initialdir=self.themes_path.get()
        )
        if folder:
            self.themes_path.delete(0, tk.END)
            self.themes_path.insert(0, folder)

    def refresh_themes_list(self):
        """Refresh the curated themes list by clearing cache and fetching fresh data."""
        # Clear the remote themes cache to force fresh fetch
        clear_remote_themes_cache()

        # Clear existing items
        for item in self.themes_tree.get_children():
            self.themes_tree.delete(item)

        # Load curated themes (will fetch fresh data)
        themes = get_curated_themes()
        for theme in themes:
            self.themes_tree.insert(
                "",
                "end",
                text=theme.name,
                values=(theme.version, theme.author, theme.description),
                tags=(theme.download_url,),  # Store URL in tags for later use
            )

    def install_selected_theme(self):
        """Install the selected curated theme."""
        selection = self.themes_tree.selection()
        if not selection:
            self.status_bar.config(text="Please select a theme to install.")
            return

        # Get selected theme info
        item = selection[0]
        theme_name = self.themes_tree.item(item, "text")
        theme_url = self.themes_tree.item(item, "tags")[0]

        # Find the theme object
        themes = get_curated_themes()
        selected_theme = next((t for t in themes if t.name == theme_name), None)

        if not selected_theme:
            self.status_bar.config(text="Could not find theme information.")
            return

        self._install_theme_async(selected_theme)

    def install_custom_theme(self):
        """Install a custom theme from URL."""
        url = self.custom_theme_url.get().strip()
        name = self.custom_theme_name.get().strip()

        if not url:
            self.status_bar.config(text="Please enter a theme ZIP URL.")
            return

        if not name:
            self.status_bar.config(text="Please enter a theme name.")
            return

        # Create a custom theme object
        from utils.templates import CockatriceTheme

        custom_theme = CockatriceTheme(
            name=name,
            download_url=url,
            description="Custom theme",
            version="Custom",
            author="Unknown",
        )

        self._install_theme_async(custom_theme)

    def _install_theme_async(self, theme):
        """Install theme in a background thread."""
        import threading

        themes_folder = self.themes_path.get().strip()
        if not themes_folder:
            self.status_bar.config(text="Please set the Cockatrice themes folder.")
            return

        # Disable install button
        self.install_theme_btn.config(state="disabled", text="Installing...")
        self.status_bar.config(text=f"Installing theme: {theme.name}...")

        def install_in_thread():
            try:
                installed_path = download_and_install_theme(theme, themes_folder)
                # Update UI in main thread
                self.root.after(0, self._theme_install_success, theme, installed_path)
            except Exception as e:
                # Update UI in main thread
                self.root.after(0, self._theme_install_error, str(e))

        threading.Thread(target=install_in_thread, daemon=True).start()

    def _theme_install_success(self, theme, installed_path):
        """Handle successful theme installation."""
        self.install_theme_btn.config(state="normal", text="Install Selected Theme")

        theme_info = get_installed_theme_info(installed_path)
        if theme_info and "version" in theme_info:
            theme_name_with_version = f"{theme.name} v{theme_info['version']}"
        else:
            theme_name_with_version = f"{theme.name} v{theme.version}"

        self._set_status_message(
            f"Theme '{theme_name_with_version}' installed successfully! Restart Cockatrice to use the theme.",
            "success",
        )

    def _theme_install_error(self, error_msg):
        """Handle theme installation error."""
        self.install_theme_btn.config(state="normal", text="Install Selected Theme")
        self._set_status_message(f"Theme installation failed: {error_msg}", "error")

    def _set_status_message(self, message, message_type="info", duration=5000):
        """Set status bar message with optional highlighting and auto-clear.

        Args:
            message: The message to display
            message_type: 'info', 'success', 'warning', 'error'
            duration: Time in ms before reverting to default status
        """
        # Color coding for different message types
        colors = {
            "info": "blue",
            "success": "green",
            "warning": "orange",
            "error": "red",
        }

        # Set the message with color
        self.status_bar.config(
            text=message, foreground=colors.get(message_type, "black")
        )

        # Auto-revert to default after duration
        if duration > 0:
            self.root.after(
                duration,
                lambda: self.status_bar.config(text="Ready", foreground="black"),
            )


def main():
    """Main entry point for the application."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
