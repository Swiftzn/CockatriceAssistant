@echo off
echo Building Cockatrice Assistant Windows Executable...
echo.
python build_executable.py
echo.
if exist release\CockatriceAssistant.exe (
    echo ✅ Build completed successfully!
    echo Executable location: release\CockatriceAssistant.exe
    echo File size: 
    dir /s release\CockatriceAssistant.exe | find "CockatriceAssistant.exe"
    echo.
    echo The executable is ready for distribution in the release folder!
) else (
    echo ❌ Build failed - executable not found
)
pause