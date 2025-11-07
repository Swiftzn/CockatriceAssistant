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
from deck_parser import write_cod, CockatriceDeck
from templates import (
    download_template,
    get_curated_themes,
    download_and_install_theme,
    get_default_themes_folder,
    get_installed_theme_info,
)
from moxfield_scraper import MoxfieldScraper, convert_moxfield_to_cockatrice
import threading
from updater import update_manager, check_for_updates, get_current_version
from version import APP_NAME, APP_DESCRIPTION, GITHUB_REPO_URL


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


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cockatrice Assistant")
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

        self.update_list_btn = ttk.Button(
            btn_frame, text="Update List", command=self.update_deck_list
        )
        self.update_list_btn.pack(side=tk.LEFT, padx=(0, 5))

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

        # Save path frame
        save_frame = ttk.Frame(deck_frame)
        save_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(save_frame, text="Save to:").pack(side=tk.LEFT)
        self.save_path = ttk.Entry(save_frame)
        self.save_path.insert(
            0, r"C:\Users\dalle\AppData\Local\Cockatrice\Cockatrice\decks"
        )
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

        self.tree = ttk.Treeview(list_frame, columns=("type",), show="tree headings")
        self.tree.heading("#0", text="Deck Name")
        self.tree.heading("type", text="Type")

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
        self.moxfield_scraper = MoxfieldScraper()
        self.precon_decks = []  # List of DeckCheck precon decks

        # Check Cockatrice installation on startup
        self.root.after(100, self.check_cockatrice_installation)

        # Load cached decks on startup
        self.root.after(200, self.load_initial_decks)

        # Check for updates on startup (silent check using cache)
        self.root.after(500, self.check_for_updates_silent)

    def load_initial_decks(self):
        """Load decks from cache on app startup."""

        def load_in_thread():
            try:
                # Try to load from cache first (don't force refresh)
                decks = self.moxfield_scraper.fetch_all_precons(force_refresh=False)
                if decks:
                    # Update UI in main thread
                    self.root.after(0, self._update_precon_list_silent, decks)
                else:
                    # No cache available
                    self.root.after(
                        0,
                        lambda: self._set_status_message(
                            "No cached decks found. Click 'Update List' to fetch deck data.",
                            "info",
                        ),
                    )
            except Exception as e:
                # Error loading cache
                self.root.after(
                    0,
                    lambda: self._set_status_message(
                        f"Could not load cached decks: {e}. Click 'Update List' to fetch.",
                        "warning",
                    ),
                )

        threading.Thread(target=load_in_thread, daemon=True).start()

    def update_deck_list(self):
        """Update the deck list by fetching and refreshing cache."""
        self.update_list_btn.config(text="Updating...", state="disabled")
        self.import_url_btn.config(state="disabled")
        self.status_bar.config(text="Updating deck list...")

        def update_in_thread():
            try:
                # Force refresh to get latest data
                decks = self.moxfield_scraper.fetch_all_precons(force_refresh=True)
                # Update UI in main thread
                self.root.after(0, self._update_precon_list, decks)
            except Exception as e:
                self.root.after(
                    0,
                    lambda: self._set_status_message(
                        f"Error updating deck list: {e}", "error"
                    ),
                )
                self.root.after(
                    0,
                    lambda: self._reset_update_buttons(),
                )

        threading.Thread(target=update_in_thread, daemon=True).start()

    def import_from_url(self):
        """Import a deck from a Moxfield URL."""
        # Create a dialog to get the URL
        dialog = tk.Toplevel(self.root)
        dialog.title("Import from URL")
        dialog.geometry("500x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.geometry(
            "+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50)
        )

        ttk.Label(
            dialog, text="Import Deck from URL", font=("TkDefaultFont", 12, "bold")
        ).pack(pady=10)

        ttk.Label(dialog, text="Enter a Moxfield deck URL:").pack(pady=5)

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

            if "moxfield.com" not in url.lower():
                self._set_status_message(
                    "Currently only Moxfield URLs are supported", "warning"
                )
                return

            dialog.destroy()
            self._import_deck_from_url(url)

        ttk.Button(btn_frame, text="Import", command=import_deck).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(
            side="left", padx=5
        )

    def _import_deck_from_url(self, url):
        """Import a single deck from URL in background thread."""
        self.import_url_btn.config(text="Importing...", state="disabled")
        self.status_bar.config(text="Importing deck from URL...")

        def import_in_thread():
            try:
                # Extract deck ID from URL
                deck_id = url.split("/")[-1].split("?")[0]  # Handle query params

                # Fetch deck details
                deck = self.moxfield_scraper.fetch_deck_details(deck_id)
                if not deck:
                    self.root.after(
                        0,
                        lambda: self._set_status_message(
                            "Failed to fetch deck from URL", "error"
                        ),
                    )
                    return

                # Convert and save
                cockatrice_deck = convert_moxfield_to_cockatrice(deck)
                save_dir = Path(self.save_path.get())
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
                filename = f"{clean_name}.cod"
                out_path = save_dir / filename

                write_cod(cockatrice_deck, str(out_path))

                self.root.after(
                    0,
                    lambda: self._set_status_message(
                        f"Successfully imported '{deck.name}' to {out_path}", "success"
                    ),
                )

            except Exception as e:
                self.root.after(
                    0, lambda: self._set_status_message(f"Import failed: {e}", "error")
                )
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
        self.update_list_btn.config(text="Update List", state="normal")
        self.import_url_btn.config(state="normal")

    def _reset_precon_buttons(self):
        """Reset precon buttons to normal state (legacy method for compatibility)."""
        self._reset_update_buttons()

    def _update_cache_status(self):
        """Update the cache status display."""
        try:
            cache_file = self.moxfield_scraper.cache_file
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
                self.root.after(0, lambda: self._handle_download_error(str(e)))

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
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.geometry(
            "+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100)
        )

        ttk.Label(
            dialog,
            text="Update Downloaded Successfully!",
            font=("TkDefaultFont", 12, "bold"),
        ).pack(pady=15)

        ttk.Label(
            dialog,
            text="The update has been downloaded and is ready to install.\nThis will close the current application and start the new version.",
            justify="center",
        ).pack(pady=10, padx=20)

        # Buttons frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)

        def install_now():
            dialog.destroy()
            if update_manager.install_update(update_path):
                self._set_status_message("Installing update...", "success")
                # Give a moment for the message to display
                self.root.after(1000, self.root.quit)
            else:
                self._set_status_message("Failed to install update", "error")

        def install_later():
            dialog.destroy()
            self._set_status_message(
                f"Update saved to {update_path}. Run manually to install.", "info"
            )

        ttk.Button(btn_frame, text="Install Now", command=install_now).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Install Later", command=install_later).pack(
            side="left", padx=5
        )

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

    def _update_precon_list(self, decks):
        """Update the UI with loaded precon decks."""
        self.precon_decks = decks

        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.card_items.clear()

        # Add precon decks to tree with commander info
        for i, deck in enumerate(decks):
            # Build deck display text with optional components
            deck_text = deck.name

            # Add commanders if available
            if deck.commanders:
                commanders_str = ", ".join(deck.commanders)
                deck_text += f" [{commanders_str}]"

            # Add year if available
            if deck.year:
                deck_text += f" ({deck.year})"

            item_id = self.tree.insert("", "end", text=deck_text, values=("precon",))
            self.card_items.append((item_id, "precon", i))

        self._reset_precon_buttons()
        self._set_status_message(
            f"Successfully loaded {len(decks)} precon decks!", "success"
        )

    def _update_precon_list_silent(self, decks):
        """Update the UI with loaded precon decks without showing message box."""
        self.precon_decks = decks

        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.card_items.clear()

        # Add precon decks to tree with commander info
        for i, deck in enumerate(decks):
            # Build deck display text with optional components
            deck_text = deck.name

            # Add commanders if available
            if deck.commanders:
                commanders_str = ", ".join(deck.commanders)
                deck_text += f" [{commanders_str}]"

            # Add year if available
            if deck.year:
                deck_text += f" ({deck.year})"

            item_id = self.tree.insert("", "end", text=deck_text, values=("precon",))
            self.card_items.append((item_id, "precon", i))

        self._reset_precon_buttons()
        self.status_bar.config(text=f"Loaded {len(decks)} precon decks")

        # Update cache status
        self._update_cache_status()

    def export_precons(self):
        """Import selected precon decks to .cod files."""
        if not self.precon_decks:
            self.status_bar.config(
                text="No precon decks loaded. Please use 'Update List' first."
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

                # Extract deck ID from URL for Moxfield API
                deck_id = deck.url.split("/")[-1] if deck.url else ""

                # Fetch detailed deck data (includes full card list)
                detailed_deck = self.moxfield_scraper.fetch_deck_details(deck_id)
                if not detailed_deck:
                    continue

                # Convert to Cockatrice format
                cockatrice_deck = convert_moxfield_to_cockatrice(detailed_deck)

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
        """Refresh the curated themes list."""
        # Clear existing items
        for item in self.themes_tree.get_children():
            self.themes_tree.delete(item)

        # Load curated themes
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
        from templates import CockatriceTheme

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


if __name__ == "__main__":
    app = MainWindow()
    app.run()
