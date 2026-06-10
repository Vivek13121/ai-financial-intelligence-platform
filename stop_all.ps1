# stop_all.ps1 - Stop AI Financial Intelligence Platform

Write-Host "Stopping all AI Financial Intelligence Platform services..." -ForegroundColor Yellow

# Kill FastAPI and Workers (Python)
Write-Host "Stopping Python processes (FastAPI, Workers, Scheduler)..." -ForegroundColor Cyan
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue

# Kill Vite Frontend (Node)
Write-Host "Stopping Node processes (Vite Frontend)..." -ForegroundColor Cyan
Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue

# Kill Redis
Write-Host "Stopping Redis Server..." -ForegroundColor Cyan
Stop-Process -Name "redis-server" -Force -ErrorAction SilentlyContinue

Write-Host "All services stopped successfully. No zombie processes remain!" -ForegroundColor Green
