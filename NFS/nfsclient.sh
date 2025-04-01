#!/bin/bash
# nfs-client.sh: Mounts an NFS share from a CloudLab NFS server

set -e

# Default server IP if not provided
DEFAULT_SERVER_IP="172.20.3.2"
SERVER_IP=${1:-$DEFAULT_SERVER_IP}
MOUNT_POINT=${2:-"/mnt/nfsshare"}
NFS_PATH="/users/pgrigo01/nfsshare"

echo "Setting up NFS client to connect to server $SERVER_IP..."

# Install NFS client
if ! dpkg -l | grep -q nfs-common; then
    echo "Installing NFS client software..."
    sudo apt-get update && sudo apt-get install -y nfs-common
fi

# Create mount point if it doesn't exist
if [ ! -d "$MOUNT_POINT" ]; then
    echo "Creating mount point: $MOUNT_POINT"
    sudo mkdir -p "$MOUNT_POINT"
fi

# Check if already mounted
if mount | grep -q "$MOUNT_POINT"; then
    echo "NFS share already mounted at $MOUNT_POINT"
else
    # Mount the NFS share
    echo "Mounting NFS share from $SERVER_IP:$NFS_PATH to $MOUNT_POINT..."
    sudo mount -t nfs "$SERVER_IP:$NFS_PATH" "$MOUNT_POINT"
    
    # Check if mount was successful
    if mount | grep -q "$MOUNT_POINT"; then
        echo "NFS share mounted successfully!"
    else
        echo "Failed to mount NFS share. Please check connectivity and NFS server status."
        exit 1
    fi
fi

# Add to fstab for persistence across reboots (optional)
if ! grep -q "$SERVER_IP:$NFS_PATH" /etc/fstab; then
    echo "Adding mount to /etc/fstab for persistence..."
    echo "$SERVER_IP:$NFS_PATH $MOUNT_POINT nfs defaults,_netdev 0 0" | sudo tee -a /etc/fstab
fi

echo "NFS client setup complete. Share from $SERVER_IP mounted at $MOUNT_POINT"
echo "Testing access by listing the shared directory:"
ls -la "$MOUNT_POINT"
