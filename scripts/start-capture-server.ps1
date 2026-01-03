<# 
.SYNOPSIS
    Start the memos.MCP Capture Server

.DESCRIPTION
    Starts the ephemeral capture server for AI conversation persistence.
    The server runs on localhost:8765 by default and provides:
    - /capture endpoint for browser extension
    - /health endpoint for status checks
    - /stats endpoint for capture statistics

.PARAMETER Port
    The port to run the server on (default: 8765)

.PARAMETER Background
    Run the server in the background as a job

.EXAMPLE
    .\start-capture-server.ps1
    
.EXAMPLE
    .\start-capture-server.ps1 -Port 8080 -Background
#>

param(
    [int]$Port = 8765,
    [switch]$Background
)

$ErrorActionPreference = "Stop"

# Navigate to project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Push-Location $ProjectRoot

try {
    Write-Host "🚀 Starting memos.MCP Capture Server on port $Port..." -ForegroundColor Cyan
    
    # Check if poetry is available
    if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
        Write-Error "Poetry is not installed or not in PATH"
        exit 1
    }
    
    # Set environment variables
    $env:OBSIDIAN_VAULT_PATH = $env:OBSIDIAN_VAULT_PATH ?? "$ProjectRoot\vault"
    
    Write-Host "📁 Obsidian vault path: $env:OBSIDIAN_VAULT_PATH" -ForegroundColor Gray
    
    if ($Background) {
        # Run in background as a job
        $job = Start-Job -ScriptBlock {
            param($root, $port)
            Set-Location $root
            poetry run python -c "from memos_mcp.capture_server import run_server; run_server(port=$port)"
        } -ArgumentList $ProjectRoot, $Port
        
        Write-Host "✅ Capture server started as background job (ID: $($job.Id))" -ForegroundColor Green
        Write-Host "   Use 'Get-Job -Id $($job.Id)' to check status" -ForegroundColor Gray
        Write-Host "   Use 'Stop-Job -Id $($job.Id)' to stop the server" -ForegroundColor Gray
    }
    else {
        # Run in foreground
        Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
        Write-Host ""
        
        poetry run python -c "from memos_mcp.capture_server import run_server; run_server(port=$Port)"
    }
}
finally {
    Pop-Location
}
