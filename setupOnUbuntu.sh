# abort if not sourced
(return 0 2>/dev/null) || {
  echo "ERROR: this script must be sourced, not executed."
  echo "       run:  source $0"
  exit 1
}

# figure out where this script lives
SCRIPTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# install Go
source "$SCRIPTDIR/scripts/install_go.sh"

# set up env vars
bash "$SCRIPTDIR/scripts/setupEnvironment.sh"

# ensure Chrome is installed
if ! command -v google-chrome >/dev/null; then
  echo "Installing Google Chrome..."
  wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
  sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list'
  sudo apt-get update
  sudo apt-get install -y google-chrome-stable
fi

# optional: custom getChrome logic
if [[ -f "$SCRIPTDIR/scripts/getChrome.sh" ]]; then
  source "$SCRIPTDIR/scripts/getChrome.sh"
fi

# activate venv & fetch credentials
source myenv/bin/activate
python3 getChromeCredentials.py

# reload profile
source ~/.profile

echo "
# Now you can:
#   terraform init
#   terraform apply
"