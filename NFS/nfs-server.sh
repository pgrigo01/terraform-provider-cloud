#!/bin/bash
# nfs-server.sh: Sets up and configures the local NFS server

set -e

# Define the export directory (adjust as needed)
EXPORT_DIR="$HOME/nfsshare"

echo "Starting NFS server setup..."

# Install nfs-kernel-server if exportfs is not available
if ! command -v exportfs > /dev/null 2>&1; then
    echo "Installing nfs-kernel-server..."
    sudo apt-get update && sudo apt-get install -y nfs-kernel-server
fi

# Create the export directory if it does not exist
if [ ! -d "$EXPORT_DIR" ]; then
    echo "Creating export directory: $EXPORT_DIR"
    mkdir -p "$EXPORT_DIR"
    chmod 777 "$EXPORT_DIR"
fi

# Update /etc/exports to export the directory
EXPORTS_LINE="$EXPORT_DIR *(rw,sync,no_subtree_check)"
if ! grep -qF "$EXPORTS_LINE" /etc/exports; then
    echo "Updating /etc/exports..."
    echo "$EXPORTS_LINE" | sudo tee -a /etc/exports
fi

# Re-export the shares
echo "Re-exporting shares..."
sudo exportfs -ra

# Restart the NFS service
echo "Restarting NFS server..."
sudo systemctl restart nfs-kernel-server

echo "NFS server setup complete. Exporting $EXPORT_DIR."
