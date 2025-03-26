#!/bin/bash
# nfs-server.sh: Sets up and configures the NFS server for CloudLab experiments

set -e

# Define the export directory (adjust as needed)
EXPORT_DIR="$HOME/nfsshare"

echo "Starting NFS server setup..."

# Install nfs-kernel-server and firewall if not installed
if ! command -v nfsd > /dev/null 2>&1; then
    echo "Installing nfs-kernel-server..."
    sudo apt-get update && sudo apt-get install -y nfs-kernel-server ufw
fi

# Create the export directory if it does not exist
if [ ! -d "$EXPORT_DIR" ]; then
    echo "Creating export directory: $EXPORT_DIR"
    mkdir -p "$EXPORT_DIR"
    chmod 777 "$EXPORT_DIR"
fi

# Get the server's IP address (assumes eth0 is the main interface in CloudLab)
SERVER_IP=$(ip addr show eth0 | grep -oP 'inet \K[\d.]+')
echo "Server IP is: $SERVER_IP"

# Update /etc/exports to export the directory to any host
EXPORTS_LINE="$EXPORT_DIR *(rw,sync,no_subtree_check,no_root_squash)"
if ! grep -qF "$EXPORTS_LINE" /etc/exports; then
    echo "Updating /etc/exports..."
    echo "$EXPORTS_LINE" | sudo tee -a /etc/exports
fi

# Configure firewall to allow NFS
echo "Configuring firewall for NFS..."
sudo ufw allow nfs
sudo ufw allow 111/tcp  # portmapper
sudo ufw allow 111/udp
sudo ufw allow 2049/tcp # nfs
sudo ufw allow 2049/udp
sudo ufw allow from any to any port 1110:1200 proto tcp  # auxiliary NFS ports
sudo ufw allow from any to any port 1110:1200 proto udp

# Re-export the shares
echo "Re-exporting shares..."
sudo exportfs -ra

# Restart the NFS service
echo "Restarting NFS server..."
sudo systemctl restart nfs-kernel-server
sudo systemctl enable nfs-kernel-server

echo "NFS server setup complete. Exporting $EXPORT_DIR from $SERVER_IP."
echo "To mount this NFS share on another experiment, run:"
echo "  sudo mount -t nfs $SERVER_IP:$EXPORT_DIR /mnt/nfsshare"
