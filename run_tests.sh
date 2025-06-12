#!/bin/bash

# Navigate to the directory containing the shopkeeperPython package
# This assumes run_tests.sh is in the root and shopkeeperPython is a subdirectory
# Adjust the path if your structure is different.
cd "$(dirname "$0")/shopkeeperPython"

# Run unittest discovery from the 'shopkeeperPython' directory
# This will find tests in the 'tests' subdirectory
echo "Running tests..."
python3 -m unittest discover -s tests -p "test_*.py"

# Optional: Add a specific path to python if needed, or use `python` if `python3` is not standard
# Example: /usr/bin/python3 -m unittest discover tests
