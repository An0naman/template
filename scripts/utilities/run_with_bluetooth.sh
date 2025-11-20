#!/bin/bash
# Run the Flask application directly on the host for Bluetooth/Niimbot support
# This bypasses Docker's Bluetooth limitations

set -e

echo "================================================"
echo "  Running Flask App with Bluetooth Support"
echo "================================================"
echo ""
echo "This script runs the application directly on your"
echo "host machine to enable Bluetooth/Niimbot printing."
echo ""

# Check if we're in the right directory
if [ ! -f "run.py" ]; then
    echo "Error: run.py not found. Please run this script from the project root."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade requirements
echo "Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if bleak is installed
if ! python -c "import bleak" 2>/dev/null; then
    echo ""
    echo "Warning: Bleak library not found. Installing..."
    pip install bleak
fi

echo ""
echo "================================================"
echo "  Starting Flask Application"
echo "================================================"
echo ""
echo "Application will be available at:"
echo "  http://localhost:5001"
echo ""
echo "Bluetooth/Niimbot printing is now enabled!"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Set environment variables
export FLASK_APP=run.py
export NETWORK_RANGE=${NETWORK_RANGE:-192.168.68.0/24}
export PYTHONUNBUFFERED=1

# Run the application
python run.py
