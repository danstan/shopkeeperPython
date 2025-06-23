#!/bin/bash

# Run unittest discovery from the project root directory
# This will find tests in the 'shopkeeperPython/tests' subdirectory
# and its sub-packages (like shopkeeperPython/tests/ui).
echo "Running all tests (including UI tests)..."
python3 -m unittest discover -s shopkeeperPython/tests -p "test_*.py"

# Optional: Add a specific path to python if needed, or use `python` if `python3` is not standard
# Example: /usr/bin/python3 -m unittest discover tests
