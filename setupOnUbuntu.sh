./scripts/install_go.sh 
. ./scripts/install_go.sh
./scripts/setupEnvironment.sh 
source myenv/bin/activate
python3 getChromeCredentials.py

#./scripts/build_provider.sh 
echo "#Run on your terminal
# 
# Run the following command to set up the environment
source myenv/bin/activate  
terraform init

Modify main.tf and then run the following command to apply the changes
terraform apply

"