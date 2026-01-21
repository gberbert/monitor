@echo off
echo [ANTIGRAVITY] Fixing Git Index Lock...
echo.
echo 1. Attempting to kill Git processes...
taskkill /F /IM git.exe /T >nul 2>&1

echo 2. Attempting to delete .git\index...
del /F /Q .git\index
if exist .git\index (
    echo [ERROR] Could not delete .git\index. 
    echo It is likely locked by OneDrive or VS Code.
    echo.
    echo ACTION REQUIRED:
    echo 1. Close VS Code.
    echo 2. Pause OneDrive Syncing.
    echo 3. Run this script again.
    pause
    exit /b 1
)

echo 3. Rebuilding Git Index...
git reset

echo.
echo [SUCCESS] Git Index fixed! You can now run 'node release.js'.
pause
