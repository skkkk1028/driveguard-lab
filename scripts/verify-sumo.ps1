$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendRoot = Join-Path $ProjectRoot "backend"
$BackendPython = Join-Path $BackendRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $BackendPython)) {
    throw "Backend virtual environment not found at backend\.venv. See README.md for setup."
}

Push-Location $BackendRoot
try {
    Write-Host "[1/2] SUMO: supported headless runtime"
    & $BackendPython -m app.adapters.sumo doctor
    if ($LASTEXITCODE -ne 0) {
        throw "Supported headless SUMO 1.27.1 is unavailable; strict SUMO verification cannot pass."
    }

    Write-Host "[2/2] SUMO: live replay and native probe tests"
    & $BackendPython -m pytest -p no:cacheprovider -m sumo --strict-markers
    if ($LASTEXITCODE -ne 0) { throw "Strict SUMO tests failed." }
}
finally {
    Pop-Location
}

Write-Host "DriveGuard Lab strict SUMO verification passed."
