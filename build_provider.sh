#!/bin/bash
# build_and_update.sh
# This script builds the Terraform provider, updates main.tf with the new version,
# removes any existing Terraform state files, installs the new provider binary,
# and runs "terraform init -upgrade".

echo "REMINDER!!! : Ensure that you have updated the client.go HostURL to the correct endpoint before continuing."

# 1. Get version: from argument or prompt user
if [ -n "$1" ]; then
  version="$1"
else
  read -p "Enter version (starting with v, e.g., v2.5.2): " version
fi

# 2. Validate the version format
if [[ $version != v* ]]; then
  echo "❌ Error: Version must start with 'v' (e.g., v2.5.2)."
  exit 1
fi

# 3. Strip leading 'v' for folder naming
version_folder="${version:1}"

# 4. Build the provider binary
echo "🔧 Building provider binary for version ${version}..."
go build -o terraform-provider-cloudlab_${version}
if [ $? -ne 0 ]; then
  echo "❌ Error: Go build failed."
  exit 1
fi

# 5. Remove existing Terraform state files
echo "🧹 Deleting terraform.tfstate and terraform.tfstate.backup if they exist..."
rm -f terraform.tfstate terraform.tfstate.backup

# 6. Update main.tf version line
if [ -f main.tf ]; then
  echo "✏️  Updating main.tf version to ${version_folder}..."
  sed -i.bak -E 's/^( *version *= *")[^"]+(")/\1'"${version_folder}"'\2/' main.tf
  echo "✅ main.tf updated. A backup is saved as main.tf.bak."
else
  echo "⚠️  Warning: main.tf not found. Skipping version update."
fi

# 7. Create the provider plugin directory
install_path="$HOME/.terraform.d/plugins/registry.terraform.io/pgrigo01/cloudlab/${version_folder}/linux_amd64"
echo "📁 Creating directory: ${install_path}..."
mkdir -p "${install_path}"

# 8. Move the built binary to the plugin path
echo "📦 Moving provider binary to ${install_path}/..."
mv terraform-provider-cloudlab_${version} "${install_path}/"

# 9. Run Terraform init with upgrade
echo "🚀 Running 'terraform init -upgrade'..."
terraform init -upgrade

echo "🎉 Done. Provider version ${version} is now built, installed locally, and main.tf updated."
