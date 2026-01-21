@echo off
echo Starting Tacticus Agent...

call .venv\Scripts\activate.bat

start http://localhost:5000

python app.py
