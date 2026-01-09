Write-Host "Starting Flask backend server..." -ForegroundColor Green
Write-Host ""
Write-Host "Make sure you're in the virtual environment!" -ForegroundColor Yellow
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & .\venv\Scripts\Activate.ps1
}

# Start Flask server
python index.py
