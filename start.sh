#!/bin/bash
# Quick start script for Movie Sentiment Analyzer

echo "🎬 Movie Sentiment Analyzer - Quick Start"
echo "=========================================="
echo ""

# Check Python
echo "✓ Checking Python..."
python --version || { echo "❌ Python not found"; exit 1; }

# Check Node.js
echo "✓ Checking Node.js..."
node --version || { echo "❌ Node.js not found"; exit 1; }

# Setup Backend
echo ""
echo "📦 Setting up Backend..."
cd movie-sentiment-backend

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt -q

# Start backend in background
echo "🚀 Starting Backend on port 8000..."
python main.py &
BACKEND_PID=$!

cd ..

# Setup Frontend
echo ""
echo "📦 Setting up Frontend..."
cd movie-sentiment-frontend

echo "Installing Node dependencies..."
npm install -q

echo "🚀 Starting Frontend on port 3000..."
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ Both servers are starting..."
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔌 Backend: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
