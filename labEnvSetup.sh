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
