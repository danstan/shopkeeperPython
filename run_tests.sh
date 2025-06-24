#!/bin/bash

# Set PYTHONPATH to include the project root
export PYTHONPATH=$(pwd)

# Install dependencies
echo "Installing dependencies..."
pip install -r shopkeeperPython/requirements.txt

# Verify installed packages and their versions
echo "Verifying installed packages..."
pip freeze

# Set default environment variables for testing if not already set
export FLASK_SECRET_KEY=${FLASK_SECRET_KEY:-test_secret_key}
export GOOGLE_OAUTH_CLIENT_ID=${GOOGLE_OAUTH_CLIENT_ID:-test_google_client_id}
export GOOGLE_OAUTH_CLIENT_SECRET=${GOOGLE_OAUTH_CLIENT_SECRET:-test_google_client_secret}

# Start Flask server in the background
echo "Starting Flask server with dummy environment variables..."
echo "FLASK_SECRET_KEY: $FLASK_SECRET_KEY"
echo "GOOGLE_OAUTH_CLIENT_ID: $GOOGLE_OAUTH_CLIENT_ID"
echo "GOOGLE_OAUTH_CLIENT_SECRET: $GOOGLE_OAUTH_CLIENT_SECRET"
python3 shopkeeperPython/app.py > flask_server_main_tests.log 2>&1 &
FLASK_PID=$!

# Wait for the server to start
echo "Waiting for Flask server to initialize (sleep 5s)..."
sleep 5
echo "Finished waiting for Flask server."

# Run non-UI tests
echo "Running all non-UI tests..."
echo "Test output will be captured in test_run_output.log"
python3 -m unittest \
    shopkeeperPython.tests.test_app \
    shopkeeperPython.tests.test_app_utils \
    shopkeeperPython.tests.test_backgrounds \
    shopkeeperPython.tests.test_character \
    shopkeeperPython.tests.test_g_event \
    shopkeeperPython.tests.test_game_manager \
    shopkeeperPython.tests.test_item \
    shopkeeperPython.tests.test_shop \
    shopkeeperPython.tests.test_user_data > test_run_output.log 2>&1
TEST_EXIT_CODE=$?

# Display the test output log
echo "Displaying test_run_output.log:"
cat test_run_output.log
echo "--- End of test_run_output.log ---"

# Display Flask server log for this run
echo "Displaying flask_server_main_tests.log:"
cat flask_server_main_tests.log
echo "--- End of flask_server_main_tests.log ---"

# Stop Flask server
echo "Stopping Flask server (PID: $FLASK_PID)..."
if kill $FLASK_PID; then
    echo "Flask server (PID: $FLASK_PID) stopped successfully."
else
    echo "Failed to stop Flask server (PID: $FLASK_PID) or it was not running."
fi

# Exit with the test result
exit $TEST_EXIT_CODE
