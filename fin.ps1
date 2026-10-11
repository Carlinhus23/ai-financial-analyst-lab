# Ejecutar al TERMINAR de trabajar:  .\fin.ps1
# Comprueba tests y ruff, hace commit de todo y lo sube a GitHub.
# Si algo falla, se para y NO sube nada.
#
# Mensaje opcional:  .\fin.ps1 "Add cash flow ratios"
# Sin mensaje, lo pregunta; si pulsas Enter, pone uno automático.

param([string]$Mensaje)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = ".\.venv\Scripts\python.exe"

function Parar($texto) {
    Write-Host "`n$texto" -ForegroundColor Red
    Write-Host "No se ha subido nada." -ForegroundColor Red
    exit 1
}

$cambios = git status --porcelain
$sinSubir = git log --oneline "@{u}..HEAD"

if (-not $cambios -and -not $sinSubir) {
    Write-Host "No hay cambios ni commits pendientes. Nada que subir." -ForegroundColor Green
    exit 0
}

if ($cambios) {
    Write-Host "`n== Ejecutando tests ==" -ForegroundColor Cyan
    & $python -m pytest -q
    if ($LASTEXITCODE -ne 0) { Parar "Hay tests fallando." }

    Write-Host "`n== Revisando el código con ruff ==" -ForegroundColor Cyan
    & $python -m ruff check .
    if ($LASTEXITCODE -ne 0) { Parar "ruff ha encontrado problemas (prueba: ruff check . --fix)." }

    Write-Host "`n== Cambios que se van a guardar ==" -ForegroundColor Cyan
    git status --short

    if (-not $Mensaje) {
        $Mensaje = Read-Host "`nMensaje del commit en inglés (Enter = automático)"
    }
    if (-not $Mensaje) {
        $Mensaje = "Work session $(Get-Date -Format 'yyyy-MM-dd HH:mm') on $env:COMPUTERNAME"
    }

    git add -A
    git commit -m $Mensaje
    if ($LASTEXITCODE -ne 0) { Parar "El commit ha fallado." }
}

Write-Host "`n== Subiendo a GitHub ==" -ForegroundColor Cyan
git push
if ($LASTEXITCODE -ne 0) {
    Parar "git push ha fallado (¿hay cambios del otro ordenador? prueba: git pull)."
}

Write-Host "`nSubido a GitHub. Buen trabajo." -ForegroundColor Green
