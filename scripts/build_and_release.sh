#!/bin/bash
# filepath: /home/pg/terraform-provider-cloudlab/scripts/build_and_release.sh

set -e

# Configuration variables
PROVIDER_NAME="cloudlab"
PUBLISHER="pgrigo01"
VERSION="1.0.3"  # Update this to match your current version

# Ensure we're in the project root directory
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Clean previous builds
rm -rf ./dist
mkdir -p ./dist

echo "Building Terraform Provider ${PROVIDER_NAME} v${VERSION}..."

# Build for all required platforms
# Terraform Registry requires at minimum: linux_amd64, darwin_amd64, windows_amd64
# Adding arm64 architectures for broader compatibility
PLATFORMS=(
  "darwin_amd64"
  "darwin_arm64"
  "linux_amd64"
  "linux_arm64"
  "windows_amd64"
  "windows_arm64"
)

# Build binary for each platform
for platform in "${PLATFORMS[@]}"; do
  os=${platform%_*}
  arch=${platform#*_}
  
  echo "Building for ${os}/${arch}..."
  
  output_name="terraform-provider-${PROVIDER_NAME}_v${VERSION}"
  if [ "$os" = "windows" ]; then
    output_name="${output_name}.exe"
  fi
  
  output_path="dist/${os}_${arch}/${output_name}"
  mkdir -p "dist/${os}_${arch}"
  
  GOOS=$os GOARCH=$arch go build -o "$output_path" -trimpath -ldflags="-s -w"
  
  # Create zip archive as required by Terraform Registry
  (
    cd "dist/${os}_${arch}"
    zip "terraform-provider-${PROVIDER_NAME}_${VERSION}_${os}_${arch}.zip" "$(basename "$output_name")"
    rm "$output_name"
  )
done

# Generate SHA256SUMS file
echo "Generating SHA256SUMS file..."
(
  cd dist
  find . -type f -name "*.zip" | sort | xargs sha256sum > SHA256SUMS
)

# Optional: Sign the checksums file if GPG key is available
if command -v gpg &> /dev/null; then
  echo "Do you want to sign the SHA256SUMS file? (y/N)"
  read -r sign_response
  if [[ "$sign_response" =~ ^[Yy]$ ]]; then
    (
      cd dist
      gpg --detach-sign SHA256SUMS
    )
    echo "SHA256SUMS.sig created."
  fi
fi

echo "Build completed successfully!"
echo
echo "Files ready for release:"
find dist -type f | sort

echo
echo "To publish to Terraform Registry:"
echo "1. Create a GitHub release for v${VERSION}"
echo "2. Upload all files from the dist directory to the release"
echo "3. Make sure to include both the zip files and SHA256SUMS file"
echo "4. If you signed the checksums, include the SHA256SUMS.sig file as well"