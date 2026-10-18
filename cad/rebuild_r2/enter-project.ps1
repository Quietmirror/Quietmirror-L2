# Source this file after placing the documented portable tools in ../_support.
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ProjectSupport = Join-Path (Split-Path $ProjectRoot -Parent) '_support'
foreach ($Subdir in @('temp','cache\pip','cache\pycache','config\matplotlib','logs','work')) {
    [void](New-Item -ItemType Directory -Force -Path (Join-Path $ProjectSupport $Subdir))
}
$env:TEMP = Join-Path $ProjectSupport 'temp'
$env:TMP = $env:TEMP
$env:PIP_CACHE_DIR = Join-Path $ProjectSupport 'cache\pip'
$env:MPLCONFIGDIR = Join-Path $ProjectSupport 'config\matplotlib'
$env:XDG_CACHE_HOME = Join-Path $ProjectSupport 'cache'
$env:PYTHONPYCACHEPREFIX = Join-Path $ProjectSupport 'cache\pycache'
$env:OMP_NUM_THREADS = '2'
$env:OPENBLAS_NUM_THREADS = '2'
$env:MKL_NUM_THREADS = '2'
$env:QUIETMIRROR_ROOT = $ProjectRoot
$env:PYTHONUTF8 = '1'
$env:PATH = (Join-Path $ProjectSupport 'venv\Scripts') + ';' + $env:PATH
Set-Location -LiteralPath $ProjectRoot
