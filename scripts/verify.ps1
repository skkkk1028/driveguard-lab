$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPython = Join-Path $ProjectRoot "backend\.venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $BackendPython)) {
    throw "Backend virtual environment not found at backend\.venv. See README.md for setup."
}

Write-Host "[1/8] API v1 contract fixture drift"
& $BackendPython (Join-Path $PSScriptRoot "api_contract_fixtures.py") --check
if ($LASTEXITCODE -ne 0) { throw "API contract fixture check failed." }

Write-Host "[2/8] Backend: Ruff"
Push-Location (Join-Path $ProjectRoot "backend")
try {
    & $BackendPython -m ruff check .
    if ($LASTEXITCODE -ne 0) { throw "Ruff failed." }

    Write-Host "[3/8] Backend: mypy"
    & $BackendPython -m mypy app tests
    if ($LASTEXITCODE -ne 0) { throw "mypy failed." }

    Write-Host "[4/8] Backend: pytest (deterministic base profile, SUMO excluded)"
    & $BackendPython -m pytest -m "not sumo"
    if ($LASTEXITCODE -ne 0) { throw "pytest failed." }
}
finally {
    Pop-Location
}

Push-Location (Join-Path $ProjectRoot "frontend")
try {
    Write-Host "[5/8] Frontend: ESLint"
    & npm.cmd run lint
    if ($LASTEXITCODE -ne 0) { throw "ESLint failed." }

    Write-Host "[6/8] Frontend: TypeScript"
    & npm.cmd run typecheck
    if ($LASTEXITCODE -ne 0) { throw "TypeScript type check failed." }

    Write-Host "[7/8] Frontend: Vitest"
    & npm.cmd run test
    if ($LASTEXITCODE -ne 0) { throw "Vitest failed." }

    Write-Host "[8/8] Frontend: Vite production build"
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw "Vite production build failed." }
}
finally {
    Pop-Location
}

Write-Host "DriveGuard Lab base verification passed (SUMO was not exercised)."
