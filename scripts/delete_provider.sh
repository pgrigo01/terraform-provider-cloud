#!/bin/bash
# delete_provider.sh
# This script deletes a given version of the Terraform provider from your local plugin directory.
# It expects a version input (e.g., v2.5.2) and deletes:
# ~/.terraform.d/plugins/registry.terraform.io/pgrigo01/cloudlab/<version_without_v>/linux_amd64
#
# Usage: 
#   ./delete_provider.sh           # will prompt for a version
#   ./delete_provider.sh v2.5.2      # will use the provided version

# Get the version from the first argument or prompt the user.
if [ -n "$1" ]; then
  version="$1"
else
  read -p "Enter the provider version to delete (e.g., v2.5.2): " version
fi

# Ensure the version starts with "v"
if [[ $version != v* ]]; then
  echo "Error: Version must start with 'v'."
  exit 1
fi

# Remove the leading "v" for folder naming (e.g., v2.5.2 -> 2.5.2)
version_folder="${version:1}"

# Construct the directory path for the provider (Linux/amd64 in this example)
provider_path="$HOME/.terraform.d/plugins/registry.terraform.io/pgrigo01/cloudlab/${version_folder}/linux_amd64"

echo "Provider version to delete: ${version} (folder: ${version_folder})"
echo "Target folder: ${provider_path}"

# Check if the folder exists, then prompt for confirmation and delete.
if [ -d "$provider_path" ]; then
  read -p "Are you sure you want to delete the folder ${provider_path}? (y/n): " confirm
  if [[ "$confirm" =~ ^[Yy]$ ]]; then
    rm -rf "$provider_path"
    echo "Folder ${provider_path} deleted."
  else
    echo "Deletion canceled."
  fi
else
  echo "Folder ${provider_path} does not exist."
fi
