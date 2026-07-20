$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPython = Join-Path $ProjectRoot "backend\.venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $BackendPython)) {
    throw "Backend virtual environment not found at backend\.venv. See README.md for setup."
}

Write-Host "[1/7] Backend: Ruff"
Push-Location (Join-Path $ProjectRoot "backend")
try {
    & $BackendPython -m ruff check .
    if ($LASTEXITCODE -ne 0) { throw "Ruff failed." }

    Write-Host "[2/7] Backend: mypy"
    & $BackendPython -m mypy app tests
    if ($LASTEXITCODE -ne 0) { throw "mypy failed." }

    Write-Host "[3/7] Backend: pytest"
    & $BackendPython -m pytest
    if ($LASTEXITCODE -ne 0) { throw "pytest failed." }
}
finally {
    Pop-Location
}

Push-Location (Join-Path $ProjectRoot "frontend")
try {
    Write-Host "[4/7] Frontend: ESLint"
    & npm.cmd run lint
    if ($LASTEXITCODE -ne 0) { throw "ESLint failed." }

    Write-Host "[5/7] Frontend: TypeScript"
    & npm.cmd run typecheck
    if ($LASTEXITCODE -ne 0) { throw "TypeScript type check failed." }

    Write-Host "[6/7] Frontend: Vitest"
    & npm.cmd run test
    if ($LASTEXITCODE -ne 0) { throw "Vitest failed." }

    Write-Host "[7/7] Frontend: Vite production build"
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw "Vite production build failed." }
}
finally {
    Pop-Location
}

Write-Host "DriveGuard Lab verification passed."
