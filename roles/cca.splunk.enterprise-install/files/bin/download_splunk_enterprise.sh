#!/usr/bin/env bash

# Download Splunk Enterprise versions

# Get the directory of the script
script_dir=$(dirname "$0")

readonly versions=(
  'splunk|8.1.2|545206cc9f70|Linux|x86_64'
  'splunk|8.1.3|63079c59e632|Linux|x86_64'
  'splunk|8.1.4|17f862b42a7c|Linux|x86_64'
  'splunk|8.1.5|9c0c082e4596|Linux|x86_64'
  'splunk|8.1.6|c1a0dd183ee5|Linux|x86_64'
  'splunk|8.2.0|e053ef3c985f|Linux|x86_64'
  'splunk|8.2.1|ddff1c41e5cf|Linux|x86_64'
  'splunk|8.2.2|87344edfcdb4|Linux|x86_64'
  'splunk|8.2.2.1|ae6821b7c64b|Linux|x86_64'
  'splunk|8.2.2.2|e89a7a0a7f22|Linux|x86_64'
  'splunk|8.2.3|cd0848707637|Linux|x86_64'
  'splunk|8.2.3.2|5281ae34c90c|Linux|x86_64'
  'splunk|8.2.3.3|e40ea5a516d2|Linux|x86_64'
  'splunk|8.2.4|87e2dda940d1|Linux|x86_64'
  'splunk|8.2.5|77015bc7a462|Linux|x86_64'
  'splunk|8.2.6|a6fe1ee8894b|Linux|x86_64'
  'splunk|8.2.7|2e1fca123028|Linux|x86_64'
  'splunk|8.2.8|da25d08d5d3e|Linux|x86_64'
  'splunk|8.2.9|4a20fb65aa78|Linux|x86_64'
  'splunk|8.2.10|417e74d5c950|Linux|x86_64'
  'splunk|8.2.11.2|84863c49dc5d|Linux|x86_64'
  'splunk|8.2.12|e973afd6886e|Linux|x86_64'
  'splunk|9.0.0|6818ac46f2ec|Linux|x86_64'
  'splunk|9.0.1|82c987350fde|Linux|x86_64'
  'splunk|9.0.2|17e00c557dc1|Linux|x86_64'
  'splunk|9.0.3|dd0128b1f8cd|Linux|x86_64'
  'splunk|9.0.4|de405f4a7979|Linux|x86_64'
  'splunk|9.0.5|e9494146ae5c|Linux|x86_64'
  'splunk|9.0.6|050c9bca8588|Linux|x86_64'
  'splunk|9.0.7|b985591d12fd|Linux|x86_64'
  'splunk|9.0.8|4fb5067d40d2|Linux|x86_64'
  'splunk|9.1.1|64e843ea36b1|Linux|x86_64'
  'splunk|9.1.2|b6b9c8185839|Linux|x86_64'
  'splunk|9.1.3|d95b3299fa65|Linux|x86_64'
  'splunk|9.1.4|a414fc70250e|Linux|x86_64'
  'splunk|9.2.0.1|d8ae995bf219|Linux|x86_64'
  'splunk|9.2.1|78803f08aabb|Linux|x86_64'
)

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

      # Download the main file
      url="https://d7wz6hmoaavd0.cloudfront.net/products/splunk/releases/${version}/linux/${product}-${version}-${build}-${platform}-${arch}.tgz"
      wget -P "$download_dir" "$url"

      # Download the MD5 file
      md5_url="${url}.md5"
      wget -P "$download_dir" "$md5_url"

      # Extract MD5 hash from the downloaded MD5 file
      md5_hash=$(grep -oE '[a-f0-9]{32}' "${download_dir}/${product}-${version}-${build}-${platform}-${arch}.tgz.md5")

      # Check if md5sum command is available
      if command -v md5sum > /dev/null; then
        Md5Sum=$(md5sum "${download_dir}/${product}-${version}-${build}-${platform}-${arch}.tgz" | awk '{print $1}')
      elif command -v md5 > /dev/null; then  # For macOS
        Md5Sum=$(md5 -q "${download_dir}/${product}-${version}-${build}-${platform}-${arch}.tgz")
      else
        read -p "No MD5 tool found. Do you want to skip MD5 check? (y/n): " skip_md5_check
        if [ "$skip_md5_check" == "y" ]; then
          echo "Skipping MD5 check."
          break
        else
          echo "Exiting the script."
          exit 1
        fi
      fi

      if [[ "a${Md5Sum}" == "a${md5_hash}" ]]; then
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
