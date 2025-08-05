#!/usr/bin/env pwsh
# Build script for Windows (PowerShell)

param(
    [string]$Command = "build"
)

function Build {
    Write-Host "Building project..." -ForegroundColor Green
    
    # Create dist directory if it doesn't exist
    if (!(Test-Path "dist")) {
        New-Item -ItemType Directory -Path "dist" | Out-Null
    }
    
    # Build bundle.js using browserify
    Write-Host "Building bundle.js..." -ForegroundColor Yellow
    if (Get-Command browserify -ErrorAction SilentlyContinue) {
        browserify src/index.js -o dist/bundle.js
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ bundle.js built successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to build bundle.js" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✗ browserify not found. Please install it with: npm install -g browserify" -ForegroundColor Red
        exit 1
    }
    
    # Build index.html using pug
    Write-Host "Building index.html..." -ForegroundColor Yellow
    if (Get-Command pug -ErrorAction SilentlyContinue) {
        pug src/index.pug -o dist/
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ index.html built successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to build index.html" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✗ pug not found. Please install it with: npm install -g pug-cli" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Build completed successfully!" -ForegroundColor Green
}

function Clean {
    Write-Host "Cleaning build artifacts..." -ForegroundColor Yellow
    
    if (Test-Path "dist") {
        Remove-Item -Recurse -Force "dist"
        Write-Host "✓ dist directory removed" -ForegroundColor Green
    } else {
        Write-Host "dist directory doesn't exist, nothing to clean" -ForegroundColor Yellow
    }
}

function Show-Help {
    Write-Host "Usage: .\build.ps1 [command]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Cyan
    Write-Host "  build    Build the project (default)" -ForegroundColor White
    Write-Host "  clean    Remove build artifacts" -ForegroundColor White
    Write-Host "  help     Show this help message" -ForegroundColor White
}

# Main script logic
switch ($Command.ToLower()) {
    "build" { Build }
    "clean" { Clean }
    "help" { Show-Help }
    default { 
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
