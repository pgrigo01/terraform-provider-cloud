#!/bin/bash
# install_go_1.23.sh
#
# This script installs Go version 1.23 on Linux (amd64).
# It downloads the binary tarball from the official Go site,
# removes any previous Go installation, extracts the new files into /usr/local,
# updates the PATH environment variable, and then prompts you to verify the installation.
#
# References:
# :contentReference[oaicite:0]{index=0} – Official Go installation instructions (go.dev/doc/install)
# :contentReference[oaicite:1]{index=1} – Example usage of wget and tar for Go installation

# Set desired Go version and target platform
GO_VERSION="1.23"
OS="linux"
ARCH="amd64"

# Define the tarball and download URL
GO_TARBALL="go${GO_VERSION}.${OS}-${ARCH}.tar.gz"
DOWNLOAD_URL="https://go.dev/dl/${GO_TARBALL}"

echo "Installing Go version ${GO_VERSION} for ${OS}/${ARCH}..."

# Remove any existing Go installation
echo "Removing any previous Go installation from /usr/local/go..."
sudo rm -rf /usr/local/go

# Download the tarball
echo "Downloading ${GO_TARBALL} from ${DOWNLOAD_URL}..."
wget "${DOWNLOAD_URL}" -O "${GO_TARBALL}"
if [ $? -ne 0 ]; then
    echo "Error: Failed to download ${GO_TARBALL}."
    exit 1
fi

# Extract the tarball into /usr/local
echo "Extracting ${GO_TARBALL} to /usr/local..."
sudo tar -C /usr/local -xzf "${GO_TARBALL}"

# Remove the downloaded tarball
echo "Cleaning up downloaded file..."
rm "${GO_TARBALL}"

# Update PATH in the user's profile if not already set
PROFILE_FILE="$HOME/.profile"
if ! grep -q "/usr/local/go/bin" "$PROFILE_FILE"; then
    echo "Updating PATH environment variable in ${PROFILE_FILE}..."
    echo "export PATH=\$PATH:/usr/local/go/bin" >> "$PROFILE_FILE"
fi

# Reload the profile file to update PATH in the current session.
# (This may not affect the current shell; you might need to log out and log back in.)
source "$PROFILE_FILE"

echo "Go version ${GO_VERSION} has been installed successfully."
echo "Verify the installation by running: go version"

#Terraform 
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common

wget -O- https://apt.releases.hashicorp.com/gpg | \
gpg --dearmor | \
sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null


gpg --no-default-keyring \
--keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg \
--fingerprint

echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
sudo tee /etc/apt/sources.list.d/hashicorp.list

sudo apt update

sudo apt-get install terraform

terraform -help
