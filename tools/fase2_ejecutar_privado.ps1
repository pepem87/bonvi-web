# Fase 2: generacion privada del catalogo, sin cambios en GitHub ni Streamlit.
# Requiere Python y las dependencias del generador previamente instaladas.
param(
    [Parameter(Mandatory=$true)][string]$StreamlitDir,
    [Parameter(Mandatory=$true)][string]$AprobadoHtml,
    [Parameter(Mandatory=$true)][string]$AprobadoPdf,
    [Parameter(Mandatory=$true)][string]$SalidaRaiz,
    [string]$Snapshot = ""
)
$ErrorActionPreference = 'Stop'
$RepoWeb = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Generator = Join-Path $RepoWeb 'tools/fase2_generar_paquete_privado.py'
if (-not (Test-Path $AprobadoHtml -PathType Leaf)) { throw 'No se encuentra el HTML aprobado.' }
if (-not (Test-Path $AprobadoPdf -PathType Leaf)) { throw 'No se encuentra el PDF aprobado.' }
if (-not (Test-Path $StreamlitDir -PathType Container)) { throw 'No se encuentra la copia local original de Streamlit.' }
if ($Snapshot -eq '' -and [string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
    throw 'No hay conexion privada de solo lectura en DATABASE_URL. La sincronizacion NO se ejecuta.'
}
New-Item -ItemType Directory -Path $SalidaRaiz -Force | Out-Null
$argsPython = @(
    $Generator, '--aprobado-html', $AprobadoHtml,
    '--aprobado-pdf', $AprobadoPdf,
    '--streamlit-dir', $StreamlitDir,
    '--salida-raiz', $SalidaRaiz
)
if ($Snapshot -ne '') { $argsPython += @('--snapshot', $Snapshot) }
# Sin shell intermedio, para evitar interpretar credenciales u otros caracteres.
& python @argsPython
if ($LASTEXITCODE -ne 0) { throw "La auditoria privada fallo (codigo $LASTEXITCODE). No hubo publicacion." }
Write-Host 'BON VI: generacion privada verificada. La publicacion permanece deshabilitada.'
