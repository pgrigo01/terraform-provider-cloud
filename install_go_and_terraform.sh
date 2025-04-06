#!/bin/bash

set -e

# === SYSTEM UPDATE ===
echo "🔄 Updating package list..."
sudo apt update

# === CONFIG ===
GO_VERSION="1.23.0"
TERRAFORM_VERSION="$(curl -s https://api.github.com/repos/hashicorp/terraform/releases/latest | grep -Po '"tag_name": "\K[^"]*')"
ARCH="amd64"
OS="linux"

# === INSTALL GO ===
echo "⬇️ Downloading Go $GO_VERSION..."
wget -q "https://go.dev/dl/go${GO_VERSION}.${OS}-${ARCH}.tar.gz" -O go.tar.gz

echo "📦 Installing Go to /usr/local/go..."
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go.tar.gz
rm go.tar.gz

# Add Go to PATH if not already
if ! grep -q '/usr/local/go/bin' ~/.bashrc; then
  echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
  echo "✅ Added Go to PATH in ~/.bashrc"
fi

# === INSTALL TERRAFORM ===
echo "⬇️ Downloading Terraform $TERRAFORM_VERSION..."
wget -q "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_${OS}_${ARCH}.zip" -O terraform.zip

echo "📦 Installing Terraform to /usr/local/bin..."
unzip -o terraform.zip
sudo mv terraform /usr/local/bin/
rm terraform.zip

# === VERIFY ===
echo ""
echo "✅ Versions installed:"
source ~/.bashrc
go version
terraform version
