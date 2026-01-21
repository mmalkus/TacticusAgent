#!/bin/bash
echo "Creating virtual environment..."
python3 -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo ""
echo "Installation complete!"
echo "Run './run.sh' to start the application."
