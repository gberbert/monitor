
$ErrorActionPreference = "Stop"
$source = "C:\Users\K\OneDrive\Documentos\PROJETOS ANTIGRAVITY\monitor"
$dest = "C:\antigravity_temp\monitor"

Write-Host ">>> INICIANDO MIGRACAO TEMPORARIA PARA PUSH <<<" -ForegroundColor Cyan

# 1. Criar pasta temporaria
if (Test-Path $dest) {
    Write-Host "Limpar pasta temporaria antiga..." -ForegroundColor Yellow
    Remove-Item -Path $dest -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $dest | Out-Null

# 2. Copiar arquivos (Robocopy e mais robusto que Copy-Item)
Write-Host "Copiando arquivos (ignorando node_modules e archive)..." -ForegroundColor Yellow
# /MIR = Mirror (copia tudo)
# /XD = Exclude Directories
# /XJ = Exclude Junction points
# /R:0 /W:0 = Sem retry em caso de erro (rapidez)
$robocopyArgs = @(
    $source, $dest, "/MIR", "/XJ", "/R:1", "/W:1",
    "/XD", "node_modules", "archive", "client\node_modules", "go2rtc_bin\storage", ".vs", ".vscode", "bin", "obj"
)
Start-Process robocopy -ArgumentList $robocopyArgs -NoNewWindow -Wait

# Robocopy retorna exit codes nao-zero mesmo em sucesso (1=files copied). Ignoramos erro padrao.
Write-Host "Copia concluida." -ForegroundColor Green

# 3. Executar Git Push na nova pasta
Write-Host "Executando GIT PUSH na pasta temporaria..." -ForegroundColor Cyan
Set-Location $dest

# Tentar reparar index se necessario (ja que copiamos)
git reset
git add .
git commit -m "chore: migration push" --allow-empty

Write-Host "Enviando para GitHub..." -ForegroundColor Yellow
git push

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n>>> SUCESSO! O projeto foi enviado para o GitHub. <<<" -ForegroundColor Green
    Write-Host "Agora voce pode clonar em qualquer outro lugar." -ForegroundColor Green
}
else {
    Write-Host "`n>>> ERRO NO PUSH. Verifique as mensagens acima. <<<" -ForegroundColor Red
}
