@echo off
REM Quick start script for Movie Sentiment Analyzer (Windows)

echo.
echo 🎬 Movie Sentiment Analyzer - Quick Start
echo ==========================================
echo.

REM Check Python
echo ✓ Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found
    exit /b 1
)

REM Check Node.js
echo ✓ Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found
    exit /b 1
)

REM Setup Backend
echo.
echo 📦 Setting up Backend...
cd movie-sentiment-backend

REM Create virtual environment if not exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt -q

REM Start backend
echo 🚀 Starting Backend on port 8000...
start python main.py

cd ..

REM Setup Frontend
echo.
echo 📦 Setting up Frontend...
cd movie-sentiment-frontend

echo Installing Node dependencies...
call npm install -q

echo 🚀 Starting Frontend on port 3000...
start npm run dev

cd ..

echo.
echo ✅ Both servers are starting...
echo.
echo 📱 Frontend: http://localhost:3000
echo 🔌 Backend: http://localhost:8000
echo.
echo Close the terminals to stop the servers
echo.
pause
