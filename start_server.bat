@echo off
echo Starting Recipe Bot Web Server...
echo.
echo Open your browser and go to: http://127.0.0.1:5000/
echo Press Ctrl+C to stop the server.
echo.

:: Check if virtual environment exists and activate it
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Using system Python.
)

:: Install dependencies if needed
echo Checking dependencies...
pip install -r requirements.txt

:: Run the Flask app
echo.
echo Starting Flask server...
python app.py

pause 