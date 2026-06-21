# start_all.ps1 - Launch AI Financial Intelligence Platform

Write-Host "Starting AI Financial Intelligence Platform..." -ForegroundColor Green

$env:PYTHONPATH = "d:\ai sentiment analysis"

# Start Redis
Write-Host "Starting Redis..." -ForegroundColor Cyan
Start-Process redis-server -NoNewWindow

# Start FastAPI Backend
Write-Host "Starting FastAPI Backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"`$env:PYTHONPATH='d:\ai sentiment analysis'; cd apps\api; uvicorn app.main:app --reload`""

# Start Main Worker
Write-Host "Starting Main Worker..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"`$env:PYTHONPATH='d:\ai sentiment analysis'; cd apps\worker; python run.py`""

# Start Sentiment Worker
Write-Host "Starting Sentiment Worker..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"`$env:PYTHONPATH='d:\ai sentiment analysis'; cd apps\worker; python run_sentiment.py`""

# Start Forecast Worker
Write-Host "Starting Forecast Worker..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"`$env:PYTHONPATH='d:\ai sentiment analysis'; cd apps\worker; python run_forecast.py`""

# Start Entity Worker
Write-Host "Starting Entity Worker..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"`$env:PYTHONPATH='d:\ai sentiment analysis'; cd apps\worker; python run_entity.py`""

# Start Scheduler
Write-Host "Starting Scheduler..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"`$env:PYTHONPATH='d:\ai sentiment analysis'; cd apps\scheduler; python run.py`""

# Start Vite Frontend
Write-Host "Starting Vite Frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"cd apps\web; npm run dev`""

Write-Host "All services started successfully in separate windows!" -ForegroundColor Green
Write-Host "Frontend is running at http://localhost:5173" -ForegroundColor Yellow

