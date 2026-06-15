$ErrorActionPreference = "Stop"

$root = git rev-parse --show-toplevel
Set-Location $root

git config core.hooksPath project-hooks
Write-Host "Configured local git hooksPath=project-hooks"
