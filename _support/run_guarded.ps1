param(
    [Parameter(Mandatory=$true)][string]$Executable,
    [Parameter(Mandatory=$true)][string[]]$Arguments,
    [Parameter(Mandatory=$true)][string]$Log,
    [double]$MemoryGiB = 4,
    [int]$TimeoutSeconds = 2400
)
. (Join-Path $PSScriptRoot 'enter-env.ps1')
& $CadPython (Join-Path $PSScriptRoot 'guard.py') --memory-gib $MemoryGiB --timeout $TimeoutSeconds --log $Log -- $Executable @Arguments
exit $LASTEXITCODE
