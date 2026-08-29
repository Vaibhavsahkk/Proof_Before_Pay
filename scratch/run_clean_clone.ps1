param (
    [Parameter(Mandatory = $true)]
    [string]$CandidateSha,

    [Parameter(Mandatory = $false)]
    [ValidateSet("phase_0", "phase_1")]
    [string]$Phase = "phase_1"
)

$runner = Join-Path $PSScriptRoot "..\scripts\run_clean_clone_tests.ps1"
& powershell.exe -NonInteractive -NoProfile -ExecutionPolicy Bypass -File $runner -CandidateSha $CandidateSha -Phase $Phase
exit $LASTEXITCODE
