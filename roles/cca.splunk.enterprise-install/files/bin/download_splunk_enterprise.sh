#!/usr/bin/env bash

# Download Splunk Enterprise versions

# Get the directory of the script
script_dir=$(dirname "$0")

# Load versions from JSON file
versions_json_file="${script_dir}/../dat/versions.json"

# Function to load versions from JSON
load_versions_from_json() {
    if [[ ! -f "$versions_json_file" ]]; then
        echo "❌ Error: versions.json file not found at $versions_json_file"
        echo "Please run version_chronicle.sh first to generate the versions file."
        exit 1
    fi

    # Check if jq is available
    if ! command -v jq > /dev/null; then
        echo "❌ Error: jq is required but not installed"
        echo "Please install jq to parse the versions.json file"
        exit 1
    fi

    # Validate JSON file
    if ! jq empty "$versions_json_file" 2>/dev/null; then
        echo "❌ Error: Invalid JSON in $versions_json_file"
        exit 1
    fi

    # Extract versions and convert to the expected format
    local versions_array=()
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            # Parse the JSON object and format as 'product|version|build|platform|arch|url'
            local product=$(echo "$line" | jq -r '.product')
            local version=$(echo "$line" | jq -r '.version')
            local build=$(echo "$line" | jq -r '.build')
            local platform=$(echo "$line" | jq -r '.platform')
            local arch=$(echo "$line" | jq -r '.arch')
            local url=$(echo "$line" | jq -r '.url')

            versions_array+=("${product}|${version}|${build}|${platform}|${arch}|${url}")
        fi
    done < <(jq -c '.versions[]' "$versions_json_file")

    # Return the array
    printf '%s\n' "${versions_array[@]}"
}

# Load versions from JSON file
echo "📋 Loading versions from $versions_json_file..."
versions=($(load_versions_from_json))

if [[ ${#versions[@]} -eq 0 ]]; then
    echo "❌ Error: No versions found in $versions_json_file"
    exit 1
fi

echo "✅ Loaded ${#versions[@]} versions from JSON file"

# Display metadata if available
if command -v jq > /dev/null && [[ -f "$versions_json_file" ]]; then
    last_updated=$(jq -r '.metadata.last_updated // "unknown"' "$versions_json_file")
    total_versions=$(jq -r '.metadata.total_versions // "unknown"' "$versions_json_file")
    echo "📊 Metadata: $total_versions versions, last updated: $last_updated"
fi

default_download_dir="${CCA_INFRASTRUCTURE_REPO_DIR}/splunk/var/images"

# Display the EULA content and ask for acceptance
eula_file="${script_dir}/../dat/splunk-license-eula.txt"
echo -e "\nSplunk End User License Agreement (EULA) will be displayed below."
echo -e "Please read the entire agreement. Press 'q' to exit 'less' and continue the script."
echo -e "By continuing, you indicate your acceptance of the EULA.\n"
read -n 1 -s -r -p "Press any key to continue..."

less "$eula_file"

echo
echo "Splunk (EULA) accepted"

while true; do
  read -p "Press enter for the selected directory or enter a new path (${default_download_dir}):" download_dir
  download_dir="${download_dir:-$default_download_dir}"

  # Reverse the order of versions for display
  reversed_versions=("${versions[@]}")
  IFS=$'\n' reversed_versions=($(echo "${reversed_versions[*]}" | tac))

  echo "Select Splunk version to download to ${download_dir}:"
  select option in "${reversed_versions[@]}" "Quit"; do
    if [[ -n $option ]]; then
      if [ "$option" == "Quit" ]; then
        echo "Exiting the script."
        exit 0
      fi

      IFS='|' read -r -a version_info <<< "$option"
      product="${version_info[0]}"
      version="${version_info[1]}"
      build="${version_info[2]}"
      platform="${version_info[3]}"
      arch="${version_info[4]}"
      url="${version_info[5]}"

      # Download the main file using the URL from JSON
      wget -P "$download_dir" "$url"

      # Download the SHA512 file
      sha512_url="${url}.sha512"
      wget -P "$download_dir" "$sha512_url"

      # Extract filename from URL for checksum verification
      filename=$(basename "$url")
      # Extract SHA512 hash from the downloaded SHA512 file
      sha512_hash=$(grep -oE '[a-f0-9]{128}' "${download_dir}/${filename}.sha512")

      # Check if sha512sum command is available
      if command -v sha512sum > /dev/null; then
        Sha512Sum=$(sha512sum "${download_dir}/${filename}" | awk '{print $1}')
      elif command -v sha512 > /dev/null; then  # For macOS
        Sha512Sum=$(sha512 -q "${download_dir}/${filename}")
      else
        read -p "No SHA512 tool found. Do you want to skip SHA512 check? (y/n): " skip_sha512_check
        if [ "$skip_sha512_check" == "y" ]; then
          echo "Skipping SHA512 check."
          break
        else
          echo "Exiting the script."
          exit 1
        fi
      fi

      if [[ "a${Sha512Sum}" == "a${sha512_hash}" ]]; then
        echo "File integrity check is OK"
      else
        echo "Failed to validate downloaded file. Please try again."
        exit 1
      fi

      read -p "Do you want to download another version? (y/n): " answer
      if [[ "$answer" != "y" ]]; then
        echo "Exiting the loop."
        exit 0
      else
        break
      fi
    else
      echo "Invalid option. Please select a valid version or 'Quit'."
    fi
  done
done