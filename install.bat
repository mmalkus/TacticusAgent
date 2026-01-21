@echo off
echo Creating virtual environment...
python -m venv .venv

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing requirements...
pip install -r requirements.txt

echo.
echo Installation complete!
echo Run 'run.bat' to start the application.
pause
