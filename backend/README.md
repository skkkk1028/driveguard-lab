# DriveGuard Lab Backend

This directory contains the minimal FastAPI application and the pure Python domain
contracts for DriveGuard Lab. The API exposes only `GET /health`; the domain layer
defines data representation and validation but no simulation or risk-assessment
behavior.

## Local setup

From this directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Verification

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy app tests
.\.venv\Scripts\python.exe -m pytest
```
