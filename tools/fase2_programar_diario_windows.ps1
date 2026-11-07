# Registro opcional de ejecucion diaria en Windows, solo para el catalogo de pruebas.
# No cambia GitHub, Supabase, Streamlit ni bonvimercat.com.ar.
# Solo ejecutar en una maquina donde DATABASE_URL de lectura ya este configurada
# de forma segura en el perfil del usuario que ejecutara la tarea.
param(
    [Parameter(Mandatory=$true)][string]$StreamlitDir,
    [Parameter(Mandatory=$true)][string]$AprobadoHtml,
    [Parameter(Mandatory=$true)][string]$AprobadoPdf,
    [Parameter(Mandatory=$true)][string]$SalidaRaiz,
    [string]$Hora = '09:15',
    [switch]$ReemplazarTareaExistente
)
$ErrorActionPreference = 'Stop'
$TaskName = 'BON VI - Actualizar catalogo PRIVADO'
$Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($Existing -and -not $ReemplazarTareaExistente) {
    throw 'La tarea ya existe. No se modifica sin -ReemplazarTareaExistente.'
}
foreach ($path in @($StreamlitDir,$AprobadoHtml,$AprobadoPdf)) {
    if (-not (Test-Path $path)) { throw "Falta archivo o carpeta: $path" }
}
$Runner = (Resolve-Path (Join-Path $PSScriptRoot 'fase2_ejecutar_privado.ps1')).Path
$at = [DateTime]::ParseExact($Hora, 'HH:mm', [System.Globalization.CultureInfo]::InvariantCulture)
$escape = { param($s) '"' + $s.Replace('"','\"') + '"' }
$Command = @(
    '-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
    '-File', (& $escape $Runner),
    '-StreamlitDir', (& $escape $StreamlitDir),
    '-AprobadoHtml', (& $escape $AprobadoHtml),
    '-AprobadoPdf', (& $escape $AprobadoPdf),
    '-SalidaRaiz', (& $escape $SalidaRaiz)
) -join ' '
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $Command
$trigger = New-ScheduledTaskTrigger -Daily -At $at
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 35)
# La tarea solo se ejecuta con la sesion iniciada del usuario para no
# almacenar contrasenas de Windows en el programador.
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
if ($Existing) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Genera un ZIP privado del catalogo; nunca publica la web ni escribe en Supabase.' | Out-Null
Write-Host "Tarea '$TaskName' creada para las $Hora (hora local de Windows)."
Write-Host 'Debe quedar iniciada la sesion, con acceso a los datos de lectura de Supabase.'
