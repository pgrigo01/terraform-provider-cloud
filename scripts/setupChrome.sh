#!/bin/bash

set -e  # Exit if any command fails

echo "🌀 Updating system packages..."
sudo apt update

# Detect Python version (major.minor), e.g., 3.10 or 3.12
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)

if [ -z "$PYTHON_VERSION" ]; then
  echo "❌ Python 3 is not installed. Exiting."
  exit 1
fi

echo "✅ Detected Python version: $PYTHON_VERSION"

# Try to install the matching pythonX.Y-venv
VENV_PKG="python${PYTHON_VERSION}-venv"
echo "📦 Installing venv package: $VENV_PKG"
sudo apt install -y "$VENV_PKG"

# Install pip if needed
echo "📦 Ensuring pip is installed..."
sudo apt install -y python3-pip

# Upgrade pip
echo "🚀 Upgrading pip..."
python3 -m pip install --upgrade pip

# Create virtual environment (optional)
if [ ! -d "myenv" ]; then
  echo "🧪 Creating virtual environment..."
  python3 -m venv myenv
else
  echo "🔁 Virtual environment already exists: myenv"
fi

# Download and install Google Chrome
echo "🌐 Installing Google Chrome (this may take a while)..."
wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome.deb
rm google-chrome.deb

echo "✅ Setup complete!"
