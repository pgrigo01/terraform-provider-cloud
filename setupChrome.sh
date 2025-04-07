#!/bin/bash

# Activate the virtual environment
sudo apt update
#sudo apt install python3-venv
#sudo apt install python3-pip
pip install flask

source myenv/bin/activate
#sudo apt install python3-pip



sudo apt install python3-pip
# Ensure pip is installed and upgrade it
# python -m ensurepip --upgrade
# pip install --upgrade pip

# Install required packages

pip install flask

# Download and install Google Chrome
wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome.deb
rm google-chrome.deb

# Install necessary Python packages
pip3 install selenium pandas webdriver-manager

pip install webdriver_manager
pip install apscheduler
pip install pandas

# Run the server
#python3 server.py
