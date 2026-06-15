param(
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"

Write-Host "[pre-commit] Backend compile"
python -m compileall src main.py

if (-not $SkipFrontend) {
    Write-Host "[pre-commit] Frontend lint/build"
    Push-Location frontend
    try {
        npm run lint
        npm run build
    }
    finally {
        Pop-Location
    }
}

Write-Host "[pre-commit] OK"
