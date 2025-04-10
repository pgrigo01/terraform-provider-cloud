#!/bin/bash

# Script to extract the private key and certificate from cloudlab.pem
# and save them as a decrypted PEM file.

set -e

PEM_FILE="cloudlab.pem"
OUTPUT_FILE="cloudlab-decrypted.pem"
BACKUP_FILE="${OUTPUT_FILE}.bak"

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

echo "🔐 Decrypting private key and extracting certificate from $PEM_FILE..."

{
    openssl rsa -in "$PEM_FILE"
    openssl x509 -in "$PEM_FILE"
} > "$OUTPUT_FILE"

echo "✅ Decrypted PEM saved as $OUTPUT_FILE"
