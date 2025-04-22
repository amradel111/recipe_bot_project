#!/bin/bash

echo "Starting Recipe Bot Web Server..."
echo ""
echo "Open your browser and go to: http://127.0.0.1:5000/"
echo "Press Ctrl+C to stop the server."
echo ""

# Check if virtual environment exists and activate it
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Using system Python."
fi

# Install dependencies if needed
echo "Checking dependencies..."
pip install -r requirements.txt

# Run the Flask app
echo ""
echo "Starting Flask server..."
python app.py 