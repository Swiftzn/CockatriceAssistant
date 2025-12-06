# Update System Testing Guide

This directory contains test scripts to verify the auto-update functionality.

## Prerequisites

1. Build the application first:
   ```powershell
   cd build
   python build_executable.py
   ```

## Test Methods

### Method 1: Quick Script Verification (Safest)

Tests that the PowerShell script is generated correctly without running it:

```powershell
python test_script_generation.py
```

**What it does:**
- Generates the PowerShell update script
- Displays the script contents
- Verifies the script syntax
- Does NOT run any update or launch anything

**Use when:** You want to verify the script logic without affecting files

---

### Method 2: Full Update Simulation (Recommended)

Simulates the complete update process with real files:

```powershell
python test_update_installer.py
```

**What it does:**
1. Creates a `test_update/` directory
2. Copies the current build as a "fake old version"
3. Simulates downloading the new version
4. Runs the actual update installer (PowerShell script)
5. Watches the update process in action

**Use when:** You want to test the full update flow end-to-end

**What you'll see:**
- PowerShell window opens with colored output
- Old version backed up
- New version installed
- Application auto-launches
- Backup cleaned up

---

### Method 3: Manual PowerShell Test

Sets up test files for manual testing:

```powershell
.\test_update.ps1
cd test_update
.\test_manual_update.ps1
```

**What it does:**
1. `test_update.ps1` - Creates test directory and files
2. `test_manual_update.ps1` - Manually runs the update steps

**Use when:** You want complete control over each step

---

## Understanding the Update Flow

The update system works in these steps:

```
1. User clicks "Install Update"
   └─> Downloads: CockatriceAssistant-v1.2.3.exe

2. GUI closes and launches PowerShell script
   └─> Script waits for app to close completely

3. PowerShell performs update:
   ├─> Backup: CockatriceAssistant.exe → CockatriceAssistant.exe.old
   ├─> Install: v1.2.3.exe → CockatriceAssistant.exe
   ├─> Launch: CockatriceAssistant.exe
   └─> Cleanup: Remove .old and temp files

4. Application restarts automatically
```

## Expected Results

After running any test, you should see:

✅ **In test_update/ directory:**
- `CockatriceAssistant.exe` (updated version)
- No `.old` files (cleaned up)
- No versioned files (moved/renamed)

✅ **PowerShell window shows:**
- Green success messages
- Clear progress indicators
- Application launched message
- Auto-closes after 3 seconds

✅ **Application:**
- Launches automatically
- Shows new version in title/about
- No errors or crashes

## Troubleshooting

### Script doesn't run
- Check PowerShell execution policy: `Get-ExecutionPolicy`
- The script uses `-ExecutionPolicy Bypass` so it should work
- Try running PowerShell as Administrator

### Application doesn't launch
- Check if PowerShell script ran completely
- Look for error messages in PowerShell window
- Verify the .exe file exists in target directory

### Files not updated
- Ensure old version isn't still running (check Task Manager)
- Verify you have write permissions to the directory
- Check if antivirus is blocking the update

## Cleanup

Remove test files after testing:

```powershell
Remove-Item test_update -Recurse -Force
```

## Notes

- Test scripts use the SAME executable file for "old" and "new" versions
- This is safe - just tests the update mechanism, not version differences
- Real updates will download actual new versions from GitHub
- Always test in a separate directory (test_update/) to avoid affecting real installation
