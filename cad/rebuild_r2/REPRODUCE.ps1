$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ProjectSupport = Join-Path (Split-Path $ProjectRoot -Parent) '_support'
. (Join-Path $PSScriptRoot 'enter-project.ps1')
$CadPython = Join-Path $ProjectSupport 'venv\Scripts\python.exe'
foreach ($Step in @('build.py','mesh_motion.py','insertion_check.py')) {
    & $CadPython -u (Join-Path $PSScriptRoot $Step)
    if ($LASTEXITCODE -ne 0) { throw "Failed: $Step" }
}
& $CadPython -u (Join-Path $PSScriptRoot 'check.py') --geometry-only
if ($LASTEXITCODE -ne 0) { throw 'Geometry/mesh checks failed' }
& $CadPython -u (Join-Path $PSScriptRoot 'interface_check.py') --sample-count 3
if ($LASTEXITCODE -ne 0) { throw 'Interface checks failed' }
& $CadPython -u (Join-Path $PSScriptRoot 'thickness_check.py')
if ($LASTEXITCODE -ne 0) { throw 'Thickness audit failed' }
# FEM is separate and can take longer. See the report for its assumptions.
& $CadPython -u (Join-Path $PSScriptRoot 'fem_check.py') --benchmark --body
if ($LASTEXITCODE -ne 0) { throw 'FEM failed' }
& (Join-Path $ProjectSupport 'tools\FreeCAD\FreeCAD_1.1.4-Windows-x86_64-py311\FreeCADCmd.exe') --user-cfg (Join-Path $ProjectSupport 'config\FreeCAD-user.cfg') --system-cfg (Join-Path $ProjectSupport 'config\FreeCAD-system.cfg') (Join-Path $PSScriptRoot 'native.py')
if ($LASTEXITCODE -ne 0) { throw 'FreeCAD export failed' }
& $CadPython -u (Join-Path $PSScriptRoot 'slice.py')
if ($LASTEXITCODE -ne 0) { throw 'Slicing failed' }
& $CadPython -u (Join-Path $PSScriptRoot 'render.py')
if ($LASTEXITCODE -ne 0) { throw 'Rendering failed' }
& $CadPython -u (Join-Path $PSScriptRoot 'render_fem.py')
if ($LASTEXITCODE -ne 0) { throw 'FEM rendering failed' }
& $CadPython -u (Join-Path $PSScriptRoot 'make_report.py')
if ($LASTEXITCODE -ne 0) { throw 'Report generation failed' }
& $CadPython -u (Join-Path $PSScriptRoot 'package.py')
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed' }
