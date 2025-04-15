#!/bin/bash

# Script to extract the private key and certificate from cloudlab.pem
# and save them as a decrypted PEM file.
# It also runs encrypt.py to create credentials if they don't exist.

PEM_FILE="cloudlab.pem"
OUTPUT_FILE="cloudlab-decrypted.pem"
BACKUP_FILE="${OUTPUT_FILE}.bak"
CREDS_FILE="credentials.encrypted"
KEY_FILE="encryption_key.key"

echo "📦 Checking for $PEM_FILE in the current directory..."

if [[ ! -f $PEM_FILE ]]; then
    echo "❌ Error: '$PEM_FILE' not found."
    echo "🔧 Please download it from the CloudLab server and place it in this directory."
    exit 1
fi

# Backup previous output if it exists
if [[ -f $OUTPUT_FILE ]]; then
    echo "🔁 Backing up existing $OUTPUT_FILE to $BACKUP_FILE"
    mv "$OUTPUT_FILE" "$BACKUP_FILE"
fi

# Prompt for username first
echo "👤 Please enter your CloudLab username:"
read CLOUDLAB_USERNAME

# Prompt for password once
echo "🔐 Enter your CloudLab certificate password:"
read -s PASSWORD
echo

# Check if credentials exist, if not, create them with encrypt.py
if [[ ! -f $CREDS_FILE || ! -f $KEY_FILE ]]; then
    echo "ℹ️ Encrypted credentials not found. Running encrypt.py to create them..."
    
    # Run encrypt.py with input provided via pipe
    echo "Using your certificate password for CloudLab authentication..."
    
    # Run encrypt.py and provide CloudLab username and password
    echo -e "$CLOUDLAB_USERNAME\n$PASSWORD" | python3 encrypt.py
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create encrypted credentials with encrypt,py"
        exit 1
    fi
    echo "✅ Encrypted credentials created successfully"
fi

echo "🔐 Decrypting private key and extracting certificate from $PEM_FILE..."

# Extract certificate (doesn't require password)
openssl x509 -in "$PEM_FILE" > "$OUTPUT_FILE"

# Decrypt RSA key using the stored password and append to output
echo "$PASSWORD" | openssl rsa -in "$PEM_FILE" -passin stdin >> "$OUTPUT_FILE" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Decrypted PEM saved as $OUTPUT_FILE"
    
    # Check for encrypted credentials
    echo "👤 Checking encrypted credentials..."

    if [[ -f $CREDS_FILE && -f $KEY_FILE ]]; then
        echo "🔑 Found encrypted credentials and key file"
        echo "🔓 Decrypting credentials..."
        
        # Use Python to decrypt credentials
        python3 - <<EOF
from cryptography.fernet import Fernet
import sys

try:
    # Load encryption key
    with open("$KEY_FILE", "rb") as f:
        key = f.read()
    
    # Create cipher for decryption
    cipher = Fernet(key)
    
    # Read encrypted credentials
    with open("$CREDS_FILE", "rb") as f:
        lines = f.readlines()
        if len(lines) < 2:
            print("❌ Invalid credentials file format")
            sys.exit(1)
            
        encrypted_username = lines[0].strip()
        encrypted_password = lines[1].strip()
    
    # Decrypt credentials
    username = cipher.decrypt(encrypted_username).decode()
    password = cipher.decrypt(encrypted_password).decode()
    
    # Output decrypted credentials
    print("\n📋 Decrypted Credentials:")
    print(f"Username: {username}")
    print("Password: [HIDDEN]")
    print("\nℹ️ These credentials will be used automatically when running chromeServer.py")
    
except Exception as e:
    print(f"❌ Error decrypting credentials: {e}")
    sys.exit(1)
EOF
    else
        echo "❓ Strange: credentials should exist but weren't found"
    fi
else
    echo "❌ Failed to decrypt private key. Invalid password."
    rm "$OUTPUT_FILE"  # Remove incomplete output file
    exit 1
fi
