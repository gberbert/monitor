@echo off
echo [ANTIGRAVITY] Starting Repository Reorganization (Final Fix)...

:: 0. Cleanup accidental files (if they are not directories)
if exist "tools" (
    if not exist "tools\*" (
        echo Deleting file 'tools' to create directory...
        del /F /Q tools
    )
)
if exist "docs" (
    if not exist "docs\*" (
        echo Deleting file 'docs' to create directory...
        del /F /Q docs
    )
)
if exist "scripts" (
    if not exist "scripts\*" (
        echo Deleting file 'scripts' to create directory...
        del /F /Q scripts
    )
)

:: 1. Create Directories
if not exist "tools" mkdir tools
if not exist "docs" mkdir docs
if not exist "scripts" mkdir scripts
if not exist "archive" mkdir archive

:: 2. Move Tools
echo Moving Tools...
move /Y apply_config_live.py tools\
move /Y check_go2rtc.py tools\
move /Y check_streams.py tools\
move /Y debug_*.py tools\
move /Y diagnostico*.py tools\
move /Y fix_*.py tools\
move /Y force_update_portao.py tools\
move /Y hot_reload_simple.py tools\
move /Y hotfix_v2.py tools\
move /Y migrate_storage.py tools\
move /Y scanner_teste_icsee.py tools\
move /Y seed_events.py tools\

:: 3. Move Docs
echo Moving Docs...
move /Y COMO_INTEGRAR_HOME_ASSISTANT.md docs\
move /Y procedimento_cloudflare_fixo.txt docs\
move /Y "prompt inicial.txt" docs\
move /Y viabilidade_acesso_remoto.md docs\
move /Y "exemplo imagem GEMINI" docs\

:: 4. Move Scripts (Aggressive Cleanup)
echo Moving Scripts...
move /Y FIX_GIT_MMAP.bat scripts\
move /Y FORCE_ZOMBIE_KILL.ps1 scripts\
move /Y INSTALAR_AGENDAMENTO.bat scripts\
move /Y UNLOCK_GIT.bat scripts\
move /Y instalar_auto_start.ps1 scripts\
move /Y prepare_storage.bat scripts\
move /Y setup_nova_maquina.bat scripts\
move /Y KILL_AND_CLEAN.bat scripts\
move /Y KILL_ROGUE.bat scripts\
move /Y LIBERAR_FIREWALL_ADMIN.bat scripts\
move /Y RESTART_FULL.bat scripts\
move /Y RESTART_PROD.bat scripts\
move /Y RESTART_SILENT.bat scripts\
move /Y restart_recorder.bat scripts\
move /Y restart_recorder_only.bat scripts\
move /Y start_full_system.bat scripts\
move /Y start_nvr_native.bat scripts\
move /Y start_system.bat scripts\
move /Y stop_all_services.bat scripts\
move /Y Abrir_App_Desktop.bat scripts\
move /Y App_Antigravity.bat scripts\
move /Y release.js scripts\

:: 5. Archive
echo Archiving...
move /Y test_lab_hd archive\
move /Y archive_debug archive\
move /Y storage_OLD_DO_NOT_USE archive\
move /Y bkp_rollback archive\

:: 6. Cleanup
echo Cleaning up...
if exist "Cameras)" del /Q "Cameras)"
if exist recorder.err del /Q recorder.err
if exist recorder.log del /Q recorder.log
if exist api_debug.log del /Q api_debug.log
if exist organize_repo.ps1 del /Q organize_repo.ps1

echo [ANTIGRAVITY] Reorganization Complete!
