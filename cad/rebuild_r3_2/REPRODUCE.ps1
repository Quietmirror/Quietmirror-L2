$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\rebuild_r3\enter-project.ps1')
$CadPython = Join-Path $ProjectSupport 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot 'exports\rebuild_r3\assembly\BODY.step'))) {
    foreach ($Step in @('mechanical.py','electronics.py')) {
        & $CadPython -u (Join-Path $ProjectRoot "cad\rebuild_r3\$Step")
        if ($LASTEXITCODE -ne 0) { throw "Failed R3 base: $Step" }
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot 'exports\rebuild_r3_1\assembly\BODY.step'))) {
    & $CadPython -u (Join-Path $ProjectRoot 'cad\rebuild_r3_1\build.py')
    if ($LASTEXITCODE -ne 0) { throw 'Failed R3.1 base' }
}
foreach ($Step in @('build.py','check_geometry.py','electronics.py','validate.py','insertion_check.py','thickness_check.py','slice.py','check_slice_support.py','render.py')) {
    & $CadPython -u (Join-Path $PSScriptRoot $Step)
    if ($LASTEXITCODE -ne 0) { throw "Failed R3.2: $Step" }
}
& (Join-Path $ProjectSupport 'tools\FreeCAD\FreeCAD_1.1.4-Windows-x86_64-py311\FreeCADCmd.exe') --user-cfg (Join-Path $ProjectSupport 'config\FreeCAD-user.cfg') --system-cfg (Join-Path $ProjectSupport 'config\FreeCAD-system.cfg') (Join-Path $PSScriptRoot 'native.py')
if ($LASTEXITCODE -ne 0) { throw 'Native FreeCAD failed' }
foreach ($Step in @('make_report.py','package.py')) {
    & $CadPython -u (Join-Path $PSScriptRoot $Step)
    if ($LASTEXITCODE -ne 0) { throw "Failed R3.2: $Step" }
}
