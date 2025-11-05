# Cockatrice Assistant

A desktop application for importing official Magic: The Gathering Commander Preconstructed decks into Cockatrice and managing themes with intelligent version control.

Built with Python + tkinter for maximum compatibility.

## Quick Start (Windows PowerShell)

1. Create a venv and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app:

```powershell
python app.py
```

## Features

### Decks Tab
- **Fetch Precons**: Downloads commander precon lists from Moxfield (currently uses drgualberto's collection of 11+ precons)
- **Load .cod file**: Import existing Cockatrice deck files for editing
- **Select All**: Select all available decks/cards for export
- **Export Selected**: Create .cod files from selected items
- **Save Path**: Defaults to `C:\Users\dalle\AppData\Local\Cockatrice\Cockatrice\decks` but can be customized

### Template Tab
- Placeholder for downloading Cockatrice themes/templates from URLs
- Enter template URL and destination folder
- Click "Download Template" to save locally

## How to Use

1. **For Precons from Moxfield**:
   - Click "Fetch Precons" to download the list of commander precons
   - Wait for the fetch to complete (shows success message)
   - Select the precon decks you want to import
   - Click "Export Selected" to create .cod files

2. **For Local .cod Files**:
   - Click "Load .cod file" to open an existing Cockatrice deck
   - Select individual cards or use "Select All"
   - Choose export destination and click "Export Selected"

3. **Customize Save Location**:
   - Edit the save path or click "Browse" to choose a different folder
   - The app creates the directory if it doesn't exist

## Technical Details
- Uses Moxfield's public API to fetch deck lists and detailed card data
- Converts Moxfield deck format to Cockatrice .cod XML format
- Preserves card quantities, set information, and collector numbers
- Handles both mainboard and sideboard cards
- Multi-threaded fetching to keep UI responsive

## Future Improvements
- Add more precon sources beyond drgualberto's collection
- Drag/drop support for .cod files
- Bulk operations on multiple files
- Better error handling and progress indicators
- Integration with official Cockatrice theme downloads
