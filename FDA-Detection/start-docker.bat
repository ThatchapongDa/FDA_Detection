@echo off
REM FDA Detection Phase 1 - Docker Startup Script
REM This script starts all containers and monitors the startup

echo.
echo ========================================
echo FDA Detection System - Docker Startup
echo ========================================
echo.
echo Phase 1 Optimizations: OCR Parallel + Image Parallel + Conditional SAM
echo.

REM Change to project directory
cd /d "d:\Project\FDA detectionV2\FDA-Detection"

echo [1/4] Building and starting containers...
docker-compose up -d --build

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to start containers
    pause
    exit /b 1
)

echo.
echo [2/4] Waiting for services to start...
timeout /t 10 /nobreak

echo.
echo [3/4] Checking container status...
docker-compose ps

echo.
echo [4/4] Checking logs for startup...
echo.
echo Backend logs (Phase 1 model warm-up):
echo =======================================
docker-compose logs backend --tail=30

echo.
echo ========================================
echo Startup Complete!
echo ========================================
echo.
echo Services:
echo   ✓ Backend API:  http://localhost:8000/api
echo   ✓ Frontend:     http://localhost:3000
echo   ✓ Database:     postgresql://localhost:5432
echo.
echo Monitor logs with:
echo   docker-compose logs -f backend
echo.
echo Test the API with:
echo   curl -X POST http://localhost:8000/api/scan ^
echo     -H "Content-Type: application/json" ^
echo     -d "{\"url\":\"https://shopee.co.th/...\", \"force\":true}"
echo.
echo Stop containers:
echo   docker-compose down
echo.
pause
