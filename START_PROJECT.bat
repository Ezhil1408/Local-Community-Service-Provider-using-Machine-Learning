@echo off
title Smart Community Service Provider - Full Stack Application
color 0A

echo.
echo ================================================================
echo    SMART COMMUNITY SERVICE PROVIDER
echo    Machine Learning Powered Platform
echo ================================================================
echo.
echo    This will start both Backend and Frontend servers
echo.
echo ================================================================
echo.

echo [Step 1] Starting Backend Server (Flask - Port 5000)...
start "Backend Server - Flask" cmd /k "cd backend && run_backend.bat"

echo.
echo Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak >nul

echo.
echo [Step 2] Starting Frontend Server (React - Port 3000)...
start "Frontend Server - React" cmd /k "cd frontend && run_frontend.bat"

echo.
echo ================================================================
echo    SERVERS STARTING...
echo ================================================================
echo.
echo    Backend (Flask API):  http://localhost:5000
echo    Frontend (React UI):  http://localhost:3000
echo.
echo    Both servers are running in separate windows.
echo    Close those windows to stop the servers.
echo.
echo ================================================================
echo.
echo Opening browser in 10 seconds...
timeout /t 10 /nobreak >nul

start http://localhost:3000

echo.
echo Project is now running! Enjoy! 
echo.
pause
