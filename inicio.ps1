# Ejecutar al EMPEZAR a trabajar:  .\inicio.ps1
# Trae lo último de GitHub, instala dependencias nuevas y comprueba que todo pasa.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = ".\.venv\Scripts\python.exe"

Write-Host "`n== Trayendo cambios de GitHub ==" -ForegroundColor Cyan
git pull
if ($LASTEXITCODE -ne 0) {
    Write-Host "git pull ha fallado. Revisa el mensaje de arriba antes de seguir." -ForegroundColor Red
    exit 1
}

Write-Host "`n== Instalando dependencias (si hay nuevas) ==" -ForegroundColor Cyan
& $python -m pip install -r requirements.txt -q
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`n== Ejecutando tests ==" -ForegroundColor Cyan
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "Hay tests fallando: arréglalos antes de añadir código nuevo." -ForegroundColor Yellow
    exit 1
}

Write-Host "`nTodo al día. A trabajar." -ForegroundColor Green
