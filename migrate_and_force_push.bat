@echo off
set "SOURCE=%~dp0"
set "DEST=C:\Dev\ANTIGRAVITY\monitor"

echo [ANTIGRAVITY] STARTING MIGRATION TO: %DEST%
echo.

:: 1. Create Destination
if not exist "%DEST%" mkdir "%DEST%"

:: 2. Copy Files (Robocopy)
echo [1/5] Copying files...
robocopy "%SOURCE%." "%DEST%" /MIR /XD node_modules archive .git .vs .vscode bin obj client\node_modules server\node_modules go2rtc_bin\storage /XJ /R:1 /W:1 /NFL /NDL

:: 3. Re-initialize Git in Destination
echo.
echo [2/5] Re-initializing Git in new location...
cd /d "%DEST%"
if exist .git rmdir /s /q .git
git init
git branch -M main

:: 4. Add Files and Commit
echo.
echo [3/5] Committing files...
git add .
git commit -m "refactor: migration from onedrive to safe folder"

:: 5. Force Push
echo.
echo [4/5] Force Pushing to GitHub...
git remote add origin https://github.com/gberbert/monitor.git
git push -u origin main --force

echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================================
    echo   MIGRATION SUCCESSFUL!
    echo ========================================================
    echo   Your project is now located at:
    echo   %DEST%
    echo.
    
    :: 6. Optional Install
    echo.
    echo   [INFO] Skipping automatic 'npm install'.
    echo   Please run 'npm install' manually in:
    echo   - Root
    echo   - server/
    echo   - client/
    echo.

    echo.
    echo   Please open this new folder in VS Code to continue working.
    echo   You can delete the old OneDrive folder later.
    echo ========================================================
) else (
    echo [ERROR] Push failed. Check your internet connection or permissions.
)
:: End of script
