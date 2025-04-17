#!/bin/bash
# build_and_update.sh
# This script automatically increments the version based on the version in main.tf,
# builds the Terraform provider, updates main.tf with the new version,
# removes any existing Terraform state files, installs the new provider binary,
# and runs "terraform init -upgrade".

echo "REMINDER!!!: Ensure that you have updated the client.go HostURL to the correct endpoint before continuing."

# 1. Get version: from argument or auto-increment from main.tf
if [ -n "$1" ]; then
  version="$1"
else
  if [ -f main.tf ]; then
    # Extract the first occurrence of a version in the pattern "X.Y.Z"
    current_version=$(grep -E 'version *= *"[0-9]+\.[0-9]+\.[0-9]+"' main.tf | head -1 | sed -E 's/.*"([0-9]+\.[0-9]+\.[0-9]+)".*/\1/')
    if [ -z "$current_version" ]; then
      echo "❌ Error: Could not extract a valid version from main.tf."
      exit 1
    fi

    # Split the version into major, minor, and patch components
    IFS='.' read -r major minor patch <<< "$current_version"

    # Auto-increment logic:
    # If the patch is 9, bump the minor version and set patch to 0 (e.g., v5.0.9 -> v5.1.0)
    if [ "$patch" -eq 9 ]; then
      minor=$((minor + 1))
      patch=0
    else
      patch=$((patch + 1))
    fi
    version="v${major}.${minor}.${patch}"
    echo "Auto-incremented version: ${version}"
  else
    echo "❌ Error: main.tf not found. Please provide a version as an argument."
    exit 1
  fi
fi

# 2. Validate version format (must start with 'v')
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

# …existing code…

# 8. Move the built binary to linux_amd64 plugin path
echo "📦 Moving provider binary to ${install_path}/..."
mv terraform-provider-cloudlab_${version} "${install_path}/"

# 8.1 Cross‑build for other platforms to populate the fs‑mirror
platforms=(darwin_amd64 darwin_arm64 windows_amd64 windows_arm64 linux_arm64)
for p in "${platforms[@]}"; do
  os=${p%_*}; arch=${p#*_}
  mirror_dir="$HOME/.terraform.d/plugins/registry.terraform.io/pgrigo01/cloudlab/${version_folder}/${os}_${arch}"
  echo "🔧 Building provider for ${os}/${arch}..."
  mkdir -p "${mirror_dir}"
  GOOS=$os GOARCH=$arch go build -o "${mirror_dir}/terraform-provider-cloudlab_${version}"
done

# 9. Run Terraform init with upgrade
echo "🚀 Running 'terraform init -upgrade'..."
terraform init -upgrade

# 10. Update lockfile with additional platform checksums…
echo "🔐 Running 'terraform providers lock' for multiple platforms…'"
terraform providers lock \
  -platform=linux_amd64 \
  -platform=darwin_amd64 \
  -platform=darwin_arm64 \
  -platform=windows_amd64 \
  -platform=windows_arm64 \
  -platform=linux_arm64 \
  -fs-mirror="$HOME/.terraform.d/plugins"

echo "🎉 Done. Provider version ${version} is now built, installed locally, and main.tf updated."
