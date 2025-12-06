@echo off
REM LearnConnect FastAPI Backend Startup Script for Windows

echo.
echo 🚀 Starting LearnConnect FastAPI Backend...
echo.
echo 📋 Checking Python environment...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt -q

REM Run the server
echo.
echo ✅ Starting server...
echo 🌐 Backend will be available at http://localhost:8000
echo 📚 API docs available at http://localhost:8000/docs
echo.
python main.py

pause
