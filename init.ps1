param(
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$checkScript = Join-Path $scriptRoot ".agents\skills\validation-demo\scripts\check_project.ps1"

if (-not (Test-Path $checkScript)) {
    throw "Verification script not found: $checkScript"
}

$skipArg = ""
if ($SkipFrontend) {
    $skipArg = " -SkipFrontend"
}

Write-Host "=== Harness Initialization ==="
Write-Host "=== Verification Commands ==="
Write-Host "check_project.ps1$skipArg"

if ($SkipFrontend) {
    & $checkScript -SkipFrontend
} else {
    & $checkScript
}

Write-Host "=== Verification Complete ==="
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Record command and output summary as Verification Evidence in progress.md"
Write-Host "2. Update feature_list.json status, evidence, and next_step"
Write-Host "3. Refresh session-handoff.md before ending the session"
