# Test Update System
# This script simulates an update by creating a fake old version and testing the update flow

Write-Host "=== Cockatrice Assistant Update Test ===" -ForegroundColor Cyan
Write-Host ""

$releaseDir = Join-Path $PSScriptRoot "release"
$testDir = Join-Path $PSScriptRoot "test_update"

# Clean up any previous test
if (Test-Path $testDir) {
    Write-Host "Cleaning up previous test..." -ForegroundColor Yellow
    Remove-Item $testDir -Recurse -Force
}

# Create test directory
New-Item -ItemType Directory -Path $testDir -Force | Out-Null
Write-Host "Created test directory: $testDir" -ForegroundColor Green

# Copy current build as "old version"
$currentExe = Join-Path $releaseDir "CockatriceAssistant.exe"
$oldVersionExe = Join-Path $testDir "CockatriceAssistant.exe"

if (Test-Path $currentExe) {
    Copy-Item $currentExe $oldVersionExe
    Write-Host "Copied current version as 'old version'" -ForegroundColor Green
} else {
    Write-Host "ERROR: Current build not found at $currentExe" -ForegroundColor Red
    Write-Host "Please build the project first!" -ForegroundColor Yellow
    exit 1
}

# Create a fake "new version" (same file but with versioned name)
$versionedExe = Join-Path $releaseDir "CockatriceAssistant-v1.2.3.exe"
$fakeNewVersion = Join-Path $testDir "CockatriceAssistant-v1.2.3.exe"

if (Test-Path $versionedExe) {
    Copy-Item $versionedExe $fakeNewVersion
    Write-Host "Created fake 'new version' for testing" -ForegroundColor Green
} else {
    Write-Host "ERROR: Versioned build not found at $versionedExe" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Test Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Test Directory: $testDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "Files created:" -ForegroundColor Yellow
Write-Host "  - CockatriceAssistant.exe (old version - DO NOT RUN)"
Write-Host "  - CockatriceAssistant-v1.2.3.exe (new version - simulated download)"
Write-Host ""
Write-Host "To test the update:" -ForegroundColor Cyan
Write-Host "  1. Navigate to: $testDir"
Write-Host "  2. Run the manual update test script below"
Write-Host ""

# Create a manual test script
$manualTestScript = @"
# Manual Update Test Script
# Simulates the update process without running the app

`$oldExe = "$oldVersionExe"
`$newExe = "$fakeNewVersion"
`$backupExe = "$oldVersionExe.old"

Write-Host "Simulating update process..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Backup old version
Write-Host "1. Creating backup..." -ForegroundColor Yellow
if (Test-Path `$oldExe) {
    Move-Item `$oldExe `$backupExe -Force
    Write-Host "   ✓ Backed up: CockatriceAssistant.exe -> CockatriceAssistant.exe.old" -ForegroundColor Green
}

# Step 2: Install new version
Write-Host "2. Installing new version..." -ForegroundColor Yellow
if (Test-Path `$newExe) {
    Move-Item `$newExe `$oldExe -Force
    Write-Host "   ✓ Installed: CockatriceAssistant-v1.2.3.exe -> CockatriceAssistant.exe" -ForegroundColor Green
}

# Step 3: Launch new version
Write-Host "3. Launching application..." -ForegroundColor Yellow
if (Test-Path `$oldExe) {
    Start-Process -FilePath `$oldExe -WorkingDirectory "$testDir"
    Write-Host "   ✓ Application launched!" -ForegroundColor Green
}

# Step 4: Cleanup
Write-Host "4. Cleaning up..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
if (Test-Path `$backupExe) {
    Remove-Item `$backupExe -Force
    Write-Host "   ✓ Removed backup" -ForegroundColor Green
}

Write-Host ""
Write-Host "Update test complete!" -ForegroundColor Green
"@

$manualTestPath = Join-Path $testDir "test_manual_update.ps1"
$manualTestScript | Out-File -FilePath $manualTestPath -Encoding UTF8
Write-Host "Created manual test script: test_manual_update.ps1" -ForegroundColor Green
Write-Host ""
Write-Host "Run the test with:" -ForegroundColor Yellow
Write-Host "  cd $testDir" -ForegroundColor Cyan
Write-Host "  .\test_manual_update.ps1" -ForegroundColor Cyan
