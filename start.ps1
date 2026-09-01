# start.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Setting up Full Stack Chat Application  " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check for Node.js
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Node.js is not installed. Attempting to install via winget..." -ForegroundColor Yellow
    winget install OpenJS.NodeJS -e --silent
    Write-Host "[*] Node.js installed. Please restart your terminal and run this script again." -ForegroundColor Red
    exit
} else {
    Write-Host "[OK] Node.js is installed." -ForegroundColor Green
}

# 2. Check for Ollama
if (!(Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Ollama is not installed. Downloading and installing..." -ForegroundColor Yellow
    $OllamaInstaller = "$env:TEMP\OllamaSetup.exe"
    Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $OllamaInstaller
    Write-Host "Running Ollama installer. Please follow the prompts..." -ForegroundColor Yellow
    Start-Process -FilePath $OllamaInstaller -Wait
    Write-Host "[*] Ollama installation complete." -ForegroundColor Green
    
    # Refresh PATH for current session
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "[OK] Ollama is installed." -ForegroundColor Green
}

# Start ollama serve in the background just in case it's not running
Write-Host "[*] Starting Ollama server in background..." -ForegroundColor Cyan
Start-Process -WindowStyle Hidden -FilePath "ollama" -ArgumentList "serve" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# 3. Pull the Ollama model
Write-Host "[*] Ensuring model qwen3:1.7b is available (this may take a moment to download if missing)..." -ForegroundColor Cyan
ollama pull qwen3:1.7b

# 4. Check for uv
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "[!] 'uv' (Python package manager) is not installed. Installing..." -ForegroundColor Yellow
    Invoke-RestMethod -Uri "https://astral.sh/uv/install.ps1" | Invoke-Expression
    # Refresh PATH in current session for uv
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "[OK] 'uv' is installed." -ForegroundColor Green
}

# 5. Start Backend
Write-Host "[*] Starting FastAPI Backend..." -ForegroundColor Cyan
$BackendDir = Join-Path -Path $PWD -ChildPath "be"
# uv run automatically handles virtual environments and installs dependencies
Start-Process -FilePath "uv" -ArgumentList "run uvicorn main:app --port 8080" -WorkingDirectory $BackendDir

# 6. Start Frontend
Write-Host "[*] Installing Frontend dependencies and starting Vite..." -ForegroundColor Cyan
$FrontendDir = Join-Path -Path $PWD -ChildPath "fe\chat-bot"
Start-Process -Wait -NoNewWindow -FilePath "npm.cmd" -ArgumentList "install" -WorkingDirectory $FrontendDir
Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory $FrontendDir

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host " Application is starting up! " -ForegroundColor Green
Write-Host " Backend running in a new window on http://localhost:8080" -ForegroundColor Green
Write-Host " Frontend running in a new window on http://localhost:5173" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host " Opening browser..." -ForegroundColor Cyan

Start-Sleep -Seconds 4
Start-Process "http://localhost:5173"

Write-Host "Done! You can close this script window." -ForegroundColor Green
