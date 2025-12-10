@echo off
echo ============================================
echo   BACKEND SETUP - Smart Community Service
echo ============================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3/4] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [4/4] Initializing database and training ML models...
python initialize.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to initialize
    pause
    exit /b 1
)

echo.
echo ============================================
echo   SETUP COMPLETE!
echo ============================================
echo.
echo You can now run the backend server with:
echo   run_backend.bat
echo.
pause
