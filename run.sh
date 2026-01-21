#!/bin/bash
echo "Starting Tacticus Agent..."

source .venv/bin/activate

# Open browser (works on Linux and Mac)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5000 &
elif command -v open &> /dev/null; then
    open http://localhost:5000 &
fi

python app.py
