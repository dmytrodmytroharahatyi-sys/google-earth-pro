@echo off
REM Test script for Windows
REM Double-click this file to run tests

echo ========================================
echo Google Earth KML Service - Test Suite
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate
    echo.
)

REM Check if dependencies are installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo.
)

REM Run tests
python test_local.py

echo.
echo ========================================
echo Test complete!
echo ========================================
pause
