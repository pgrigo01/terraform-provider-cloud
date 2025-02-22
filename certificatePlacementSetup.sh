#!/bin/bash
# Change to the user's home directory
cd ~

# Create the .ssl directory if it doesn't exist and set permissions to 700
mkdir -p .ssl
chmod 700 .ssl

# Copy the certificate to the .ssl directory
cd SQL-API
cp cloudlab-decrypted.pem ~/.ssl

# Change into the .ssl directory
cd ~/.ssl

# Rename the certificate file
mv cloudlab-decrypted.pem emulab.pem

# Set the certificate file permissions to 600
chmod 600 emulab.pem
