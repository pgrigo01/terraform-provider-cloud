#!/bin/bash
# nfs-client.sh: Mounts an NFS share from another CloudLab experiment

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <nfs-server-ip> [mount-point]"
    exit 1
fi

SERVER_IP=$1
MOUNT_POINT=${2:-/mnt/nfsshare}

# Install NFS client
echo "Installing NFS client..."
sudo apt-get update && sudo apt-get install -y nfs-common

# Create mount point if it doesn't exist
if [ ! -d "$MOUNT_POINT" ]; then
    echo "Creating mount point: $MOUNT_POINT"
    sudo mkdir -p "$MOUNT_POINT"
fi

# Mount the NFS share
echo "Mounting NFS share from $SERVER_IP to $MOUNT_POINT..."
sudo mount -t nfs "$SERVER_IP:/home/$(whoami)/nfsshare" "$MOUNT_POINT"

# Add to fstab for persistence across reboots
if ! grep -q "$SERVER_IP:/home" /etc/fstab; then
    echo "Adding mount to /etc/fstab for persistence..."
    echo "$SERVER_IP:/home/$(whoami)/nfsshare $MOUNT_POINT nfs defaults 0 0" | sudo tee -a /etc/fstab
fi

echo "NFS client setup complete. Share mounted at $MOUNT_POINT"
