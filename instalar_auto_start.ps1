####################################################
# INSTALADOR AUTOMATICO - ANTIGRAVITY VMS AUTO-START
####################################################

# 1. Self-Elevate (Pedir Admin)
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Solicitando Permissao de Administrador..."
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# 2. Identificar onde estamos
$ScriptPath = $PSScriptRoot
$BatFile = "$ScriptPath\iniciar_servidor_web.bat"
$TaskName = "Antigravity_VMS_Monitor"

Write-Host "--- CONFIGURANDO AUTO-START ---" -ForegroundColor Cyan
Write-Host "Pasta Atual: $ScriptPath"
Write-Host "Arquivo Alvo: $BatFile"

# Verificar se o .bat existe
if (-not (Test-Path $BatFile)) {
    Write-Error "ERRO: O arquivo 'iniciar_servidor_web.bat' nao foi encontrado nesta pasta!"
    Pause
    Exit
}

# 2. Remover tarefa antiga se existir (para evitar duplicatas ou erros)
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# 3. Criar a Açao (Rodar o .BAT)
# Truque: Rodamos via cmd.exe /c para garantir que ele abra a janela ou execute o batch corretamente
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatFile`"" -WorkingDirectory $ScriptPath

# 4. Criar o Gatilho (Ao Ligar o PC)
$Trigger = New-ScheduledTaskTrigger -AtStartup

# 5. Criar as Configurações (Rodar como SYSTEM/Elevado, sem parar se demorar)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0 -Priority 3

# 6. Registrar a Tarefa
# User "SYSTEM" garante que roda antes de qualquer login, mas janela fica invisivel (Background).
# Se quiser janela visivel, teria que rodar como usuario logado, mas exige senha.
# Vamos usar o modo SYSTEM para robustez de servidor.
Register-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -TaskName $TaskName -User "SYSTEM" -RunLevel Highest

Write-Host ""
Write-Host "SUCESSO! O sistema vai iniciar sozinho quando esta maquina ligar." -ForegroundColor Green
Write-Host "NOTA: Como roda como SYSTEM, a janela preta nao aparecera, mas o site estara online." -ForegroundColor Yellow
Write-Host "Pressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
