$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'enter-project.ps1')
$CadPython = Join-Path $ProjectSupport 'venv\Scripts\python.exe'
foreach ($Step in @('mechanical.py','electronics.py','validate.py','insertion_check.py','invariants.py')) {
    & $CadPython -u (Join-Path $PSScriptRoot $Step)
    if ($LASTEXITCODE -ne 0) { throw "Failed: $Step" }
}
python (Join-Path $PSScriptRoot 'check.py') --geometry-only
if ($LASTEXITCODE -ne 0) { throw 'Geometry / mesh check failed' }
foreach ($Step in @('thickness_check.py','slice.py','render.py')) {
    python -u (Join-Path $PSScriptRoot $Step)
    if ($LASTEXITCODE -ne 0) { throw "Failed: $Step" }
}
& (Join-Path $ProjectSupport 'tools\FreeCAD\FreeCAD_1.1.4-Windows-x86_64-py311\FreeCADCmd.exe') --user-cfg (Join-Path $ProjectSupport 'config\FreeCAD-user.cfg') --system-cfg (Join-Path $ProjectSupport 'config\FreeCAD-system.cfg') (Join-Path $PSScriptRoot 'native.py')
if ($LASTEXITCODE -ne 0) { throw 'Native FreeCAD failed' }
python (Join-Path $PSScriptRoot 'make_report.py')
if ($LASTEXITCODE -ne 0) { throw 'Report failed' }
python (Join-Path $PSScriptRoot 'package.py')
if ($LASTEXITCODE -ne 0) { throw 'Package failed' }
