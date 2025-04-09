#!/bin/bash

# Get the Python 3 version (e.g., 3.10)
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)

if [ -z "$PYTHON_VERSION" ]; then
    echo "Python 3 is not installed."
    exit 1
fi

# Construct venv package name
VENV_PACKAGE="python$PYTHON_VERSION-venv"

echo "Detected Python version: $PYTHON_VERSION"
echo "Trying to install package: $VENV_PACKAGE"

# Install the venv package (requires sudo)
sudo apt update
sudo apt install -y "$VENV_PACKAGE"

# Create virtual environment
echo "Creating virtual environment: myenv"
python3 -m venv myenv
source myenv/bin/activate
# pip install -r requirements.txt
pip install apscheduler
pip install flask
pip install pandas
pip install selenium
pip install webdriver-manager

if [ $? -eq 0 ]; then
    echo "Virtual environment created successfully in ./myenv"
    echo "To activate the virtual environment, run:"
    echo "source myenv/bin/activate"
    echo "Then run python3 selectServer.py"
else
    echo "Failed to create virtual environment."
    exit 1
fi

