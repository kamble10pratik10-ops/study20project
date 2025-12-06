#!/bin/bash

# LearnConnect FastAPI Backend Startup Script

echo "🚀 Starting LearnConnect FastAPI Backend..."
echo ""
echo "📋 Checking Python environment..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt -q

# Run the server
echo ""
echo "✅ Starting server..."
echo "🌐 Backend will be available at http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""
python main.py
