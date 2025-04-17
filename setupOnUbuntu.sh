./install_go.sh 
./setupChrome.sh 
./setupEnvironment.sh 
./decryptCredentials.sh 
source myenv/bin/activate
python3 getChromeCredentials.py

#./build_provider.sh 
echo "#Run on your terminal
# 
# Run the following command to set up the environment
source myenv/bin/activate  

# Run the following command to start the server
python3 selectServer.py

"
