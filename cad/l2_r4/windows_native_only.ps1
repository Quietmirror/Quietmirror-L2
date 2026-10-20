$ErrorActionPreference = 'Stop'
$rootPath = (Resolve-Path '.').Path
$toolsPath = Join-Path $rootPath '_support/tools/windows-ci'
New-Item -ItemType Directory -Path $toolsPath -Force | Out-Null
$freecadArchive = Join-Path $toolsPath 'FreeCAD-1.1.4.7z'
Invoke-WebRequest -Uri 'https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/FreeCAD_1.1.4-Windows-x86_64-py311.7z' -OutFile $freecadArchive
$hash = (Get-FileHash -LiteralPath $freecadArchive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne '4828741fc91ee37fafcdb97a1abacb18b04ba451ac4372d9ff7a7349b36f4d6d') { throw 'FreeCAD release asset integrity mismatch' }
$unpackPath = Join-Path $toolsPath 'FreeCAD'
& 7z x $freecadArchive "-o$unpackPath" -y | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'FreeCAD archive extraction failed' }
$fcPython = Get-ChildItem -LiteralPath $unpackPath -Recurse -Filter 'python.exe' | Where-Object { $_.Directory.Name -eq 'bin' } | Select-Object -First 1
if (!$fcPython) { throw 'FreeCAD bundled Python missing' }
$env:QUIETMIRROR_ROOT = $rootPath
$env:PYTHONUTF8 = '1'
$env:QT_QPA_PLATFORM = 'offscreen'
python cad/l2_r4/evidence_identity.py --python $fcPython.FullName --script cad/l2_r4/native.py
if ($LASTEXITCODE -ne 0) { throw 'Native FreeCAD assembly validation failed' }
python cad/l2_r4/ci_checkpoint.py
if ($LASTEXITCODE -ne 0) { throw 'Native checkpoint failed' }
