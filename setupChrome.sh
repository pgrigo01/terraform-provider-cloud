#!/bin/bash

# Activate the virtual environment
sudo apt update
#python3 -m venv myenv

#source myenv/bin/activate
#sudo apt install python3-pip
sudo apt install python3.12-venv


sudo apt install python3-pip
# Ensure pip is installed and upgrade it
python -m ensurepip --upgrade
pip install --upgrade pip

# Install required packages


# Download and install Google Chrome 
echo "Installing Google Chrome this may take a while..."
wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome.deb
rm google-chrome.deb

#pip install -r requirements.txt
