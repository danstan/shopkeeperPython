#!/bin/bash

# Set PYTHONPATH to include the project root
export PYTHONPATH=$(pwd)

# Install dependencies
echo "Installing dependencies for UI tests..."
pip install -r shopkeeperPython/requirements.txt

# Verify installed packages and their versions
echo "Verifying installed packages for UI tests..."
pip freeze

# Set default environment variables for testing if not already set
export FLASK_SECRET_KEY=${FLASK_SECRET_KEY:-test_secret_key_ui}
export GOOGLE_OAUTH_CLIENT_ID=${GOOGLE_OAUTH_CLIENT_ID:-test_google_client_id_ui}
export GOOGLE_OAUTH_CLIENT_SECRET=${GOOGLE_OAUTH_CLIENT_SECRET:-test_google_client_secret_ui}

# Start Flask server in the background
echo "Starting Flask server for UI tests with dummy environment variables..."
echo "FLASK_SECRET_KEY: $FLASK_SECRET_KEY"
echo "GOOGLE_OAUTH_CLIENT_ID: $GOOGLE_OAUTH_CLIENT_ID"
echo "GOOGLE_OAUTH_CLIENT_SECRET: $GOOGLE_OAUTH_CLIENT_SECRET"
python3 shopkeeperPython/app.py > flask_server_ui_tests.log 2>&1 &
FLASK_PID=$!

# Wait for the server to start
echo "Waiting for Flask server to initialize (sleep 5s) for UI tests..."
sleep 5
echo "Finished waiting for Flask server for UI tests."

# Run UI tests
echo "Running UI tests..."
echo "UI Test output will be captured in ui_test_run_output.log"
python3 -m unittest discover -s shopkeeperPython/tests/ui -p "test_*.py" > ui_test_run_output.log 2>&1
UI_TEST_EXIT_CODE=$?

# Display the UI test output log
echo "Displaying ui_test_run_output.log:"
cat ui_test_run_output.log
echo "--- End of ui_test_run_output.log ---"

# Display Flask server log for this run
echo "Displaying flask_server_ui_tests.log:"
cat flask_server_ui_tests.log
echo "--- End of flask_server_ui_tests.log ---"

# Stop Flask server
echo "Stopping Flask server (PID: $FLASK_PID) for UI tests..."
if kill $FLASK_PID; then
    echo "Flask server (PID: $FLASK_PID) stopped successfully for UI tests."
else
    echo "Failed to stop Flask server (PID: $FLASK_PID) for UI tests or it was not running."
fi

# Exit with the UI test result
exit $UI_TEST_EXIT_CODE
