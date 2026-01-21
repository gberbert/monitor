Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "ffmpeg" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "go2rtc" -Force -ErrorAction SilentlyContinue
Write-Host "Processos finalizados."
Start-Sleep -Seconds 2
$wrong_storage = "C:\Users\K\OneDrive\Documentos\PROJETOS ANTIGRAVITY\monitor\storage"
$dest = "C:\Users\K\OneDrive\Documentos\PROJETOS ANTIGRAVITY\monitor\storage_OLD_ZOMBIE"
if (Test-Path $wrong_storage) {
    Move-Item -Path $wrong_storage -Destination $dest -Force
    Write-Host "Pasta Storage errada movida para segurança."
}
Write-Host "Limpeza Concluída."
