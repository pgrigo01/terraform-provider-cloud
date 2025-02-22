#!/bin/bash
# build_and_update.sh
# This script builds the Terraform provider, updates main.tf with the new version,
# removes any existing Terraform state files, installs the new provider binary,
# and runs "terraform init -upgrade".

echo "REMINDER!!! : Ensure that you have updated the client.go HostURL to the correct endpoint before continuing."

# 1. Prompt for the version (must start with "v", e.g. v2.5.2)
read -p "Enter version (starting with v, e.g., v2.5.2): " version
if [[ $version != v* ]]; then
  echo "Error: Version must start with 'v'."
  exit 1
fi

# 2. Remove the leading 'v' for folder naming (e.g. v2.5.2 -> 2.5.2)
version_folder="${version:1}"

# 3. Build the provider binary with the version in its name
echo "Building provider binary for version ${version}..."
go build -o terraform-provider-cloudlab_${version}
if [ $? -ne 0 ]; then
  echo "Error: Go build failed."
  exit 1
fi

# 4. Delete any existing Terraform state files
echo "Deleting terraform.tfstate and terraform.tfstate.backup if they exist..."
rm -f terraform.tfstate terraform.tfstate.backup

# 5. Update main.tf to use the new version (e.g. change version = "..." line)
#    This uses sed to update a line that starts with optional spaces then "version ="
if [ -f main.tf ]; then
  echo "Updating main.tf version to ${version_folder}..."
  # The sed command looks for lines starting with optional whitespace and 'version = "old_value"'
  sed -i.bak -E 's/^( *version *= *")[^"]+(")/\1'"${version_folder}"'\2/' main.tf
  echo "main.tf updated. A backup is saved as main.tf.bak."
else
  echo "Warning: main.tf not found. Skipping version update in main.tf."
fi

# 6. Create the directory structure for the provider plugin (for Linux/amd64)
install_path="$HOME/.terraform.d/plugins/registry.terraform.io/pgrigo01/cloudlab/${version_folder}/linux_amd64"
echo "Creating directory: ${install_path}..."
mkdir -p "${install_path}"

# 7. Move the built provider binary into that directory
echo "Moving provider binary to ${install_path}..."
mv terraform-provider-cloudlab_${version} "${install_path}/"

# 8. Run terraform init -upgrade
echo "Running 'terraform init -upgrade'..."
terraform init -upgrade

echo "Done. Provider version ${version} is now built, installed locally, and main.tf updated."
