#!/usr/bin/env bash

# ==============================================================================
# Interactive 3D Earth Hotspot Monitor (TERRA-PULSE 3D) Launch Script
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "======================================================================"
echo "🌍 Starting Camera-Driven Interactive 3D Earth (TERRA-PULSE 3D)"
echo "======================================================================"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but was not found."
    exit 1
fi

VENV_DIR="$PROJECT_DIR/.venv"

# Create virtualenv if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating Python virtual environment in .venv..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtualenv
echo "🔄 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "📥 Checking and installing required packages (FastAPI, Uvicorn)..."
pip install -q --upgrade pip
pip install -q -r "$PROJECT_DIR/backend/requirements.txt"

PORT="${PORT:-8050}"

echo ""
echo "🚀 Application is ready!"
echo "📡 Open your browser at: http://localhost:$PORT"
echo "🇧🇩 Click the 'Bangladesh' or 'Dhaka' preset button to see dynamic regional LOD."
echo "🛑 Press Ctrl+C to stop the server."
echo "======================================================================"
echo ""

# Run the FastAPI server
exec uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" --reload
