# abort if not sourced
(return 0 2>/dev/null) || {
  echo "ERROR: this script must be sourced, not executed."
  echo "       run:  source $0"
  exit 1
}

# now everything runs in your current shell…
# ./scripts/install_go.sh 
. ./scripts/install_go.sh
./scripts/setupEnvironment.sh
. ./scripts/getChrome.sh
source myenv/bin/activate
python3 getChromeCredentials.py

# re‑load your ~/.profile into this same shell
source ~/.profile

#…finish up
#./scripts/build_provider.sh 
echo "
# Now you can:
#   terraform init
#   terraform apply
"
