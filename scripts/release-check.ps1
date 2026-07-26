$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendRoot = Join-Path $ProjectRoot "backend"
$BackendPython = Join-Path $BackendRoot ".venv\Scripts\python.exe"
$ReleaseTemp = Join-Path ([System.IO.Path]::GetTempPath()) (
    "driveguard-release-check-" + [System.Guid]::NewGuid().ToString("N")
)
$OriginalTemp = $env:TEMP
$OriginalTmp = $env:TMP
$OriginalStaticDirectory = $env:DRIVEGUARD_STATIC_DIR

if (-not (Test-Path -LiteralPath $BackendPython)) {
    throw "Backend virtual environment not found at backend\.venv. See README.md for setup."
}

try {
    New-Item -ItemType Directory -Path $ReleaseTemp | Out-Null
    $RuntimeTemp = Join-Path $ReleaseTemp "runtime-temp"
    $ArtifactRoot = Join-Path $ReleaseTemp "artifacts"
    $SmokeVenv = Join-Path $ReleaseTemp "smoke-venv"
    New-Item -ItemType Directory -Path $RuntimeTemp | Out-Null
    New-Item -ItemType Directory -Path $ArtifactRoot | Out-Null
    $env:TEMP = $RuntimeTemp
    $env:TMP = $RuntimeTemp

    Write-Host "[1/6] Complete deterministic base verification"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (
        Join-Path $PSScriptRoot "verify.ps1"
    )
    if ($LASTEXITCODE -ne 0) { throw "Base verification failed." }

    Write-Host "[2/6] Release metadata and documentation"
    & $BackendPython (Join-Path $PSScriptRoot "check_release.py")
    if ($LASTEXITCODE -ne 0) { throw "Release metadata check failed." }

    Write-Host "[3/6] Same-origin production Dashboard delivery"
    $env:DRIVEGUARD_STATIC_DIR = Join-Path $ProjectRoot "frontend\dist"
    & $BackendPython -c (
        "from fastapi.testclient import TestClient; " +
        "from app.main import app; " +
        "client = TestClient(app); " +
        "root = client.get('/'); " +
        "assert root.status_code == 200 and '<div' in root.text and 'id=' in root.text; " +
        "assert client.get('/health').status_code == 200; " +
        "assert client.get('/api/v1/regression-scenarios').status_code == 200; " +
        "assert client.get('/docs').status_code == 200"
    )
    if ($LASTEXITCODE -ne 0) { throw "Same-origin delivery smoke test failed." }

    Write-Host "[4/6] Backend wheel and source distribution"
    Push-Location $BackendRoot
    try {
        & $BackendPython -m build --outdir $ArtifactRoot
        if ($LASTEXITCODE -ne 0) { throw "Backend package build failed." }
    }
    finally {
        Pop-Location
    }

    Write-Host "[5/6] Built artifact metadata"
    & $BackendPython (Join-Path $PSScriptRoot "check_release.py") `
        --artifacts $ArtifactRoot
    if ($LASTEXITCODE -ne 0) { throw "Built artifact validation failed." }

    Write-Host "[6/6] Clean wheel installation and package import"
    & $BackendPython -m venv $SmokeVenv
    if ($LASTEXITCODE -ne 0) { throw "Smoke-test virtual environment failed." }
    $SmokePython = Join-Path $SmokeVenv "Scripts\python.exe"
    $Wheels = @(Get-ChildItem -LiteralPath $ArtifactRoot -Filter *.whl -File)
    if ($Wheels.Count -ne 1) { throw "Expected exactly one wheel artifact." }
    $Wheel = $Wheels[0].FullName
    & $SmokePython -m pip install --disable-pip-version-check --no-deps $Wheel
    if ($LASTEXITCODE -ne 0) { throw "Wheel installation failed." }
    & $SmokePython -c "from app import APP_VERSION; assert APP_VERSION == '1.0.0'"
    if ($LASTEXITCODE -ne 0) { throw "Installed package import failed." }
}
finally {
    $env:TEMP = $OriginalTemp
    $env:TMP = $OriginalTmp
    $env:DRIVEGUARD_STATIC_DIR = $OriginalStaticDirectory
    $ResolvedTemp = [System.IO.Path]::GetFullPath($ReleaseTemp)
    $SystemTemp = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
    if (
        $ResolvedTemp.StartsWith($SystemTemp) -and
        (Split-Path -Leaf $ResolvedTemp).StartsWith("driveguard-release-check-") -and
        (Test-Path -LiteralPath $ResolvedTemp)
    ) {
        Remove-Item -LiteralPath $ResolvedTemp -Recurse -Force
    }
}

Write-Host "DriveGuard Lab v1.0 release candidate verification passed."
