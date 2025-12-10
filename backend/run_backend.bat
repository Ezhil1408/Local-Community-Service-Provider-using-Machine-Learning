@echo off
echo ============================================
echo   Starting Backend Server
echo ============================================
echo.

if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run setup_backend.bat first
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting Flask server on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python app.py
