#!/bin/bash

# Set PYTHONPATH to include the project root
export PYTHONPATH=$(pwd)

# Install dependencies
echo "Installing dependencies..."
pip install -r shopkeeperPython/requirements.txt

# Start Flask server in the background
echo "Starting Flask server..."
python3 shopkeeperPython/app.py &
FLASK_PID=$!

# Wait for the server to start
sleep 3

# Run unittest discovery from the project root directory
# This will find tests in the 'shopkeeperPython/tests' subdirectory
# and its sub-packages (like shopkeeperPython/tests/ui).
echo "Running all tests (including UI tests)..."
python3 -m unittest discover -s shopkeeperPython/tests -p "test_*.py"
TEST_EXIT_CODE=$?

# Stop Flask server
echo "Stopping Flask server..."
kill $FLASK_PID

# Exit with the test result
exit $TEST_EXIT_CODE
