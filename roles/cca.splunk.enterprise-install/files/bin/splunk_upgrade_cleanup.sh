#!/bin/env bash

# Arguments:
#
# Diff file:   Full path to diff file on target server, e.g. /tmp/untracked_files_splunk_8.1.2_Linux.diff
# Splunk path: Splunk install path, e.g. /opt/splunk

# Usage:
# splunk_upgrade_cleanup.sh <path_to_diff_file>/untracked_files_splunk_<version>_Linux.diff <splunk_path>

splunk_path=$2

if [[ -f ${1} ]] ; then

  if [[ -d ${splunk_path} ]] ; then

     # Check if xargs is available for efficient processing
     if command -v xargs >/dev/null 2>&1; then
       # Use xargs for efficient parallel processing
       # -P 20: Process up to 20 files in parallel
       # -I {}: Replace {} with each line from the file
       cat "${1}" | cut -d"/" -f2- | xargs -P 20 -I {} rm -f "${splunk_path}/{}"
     else
       # Fallback to original line-by-line processing
       while IFS= read -r line; do
         file=$(echo ${line} | cut -d"/" -f2-)
         rm -f ${splunk_path}/${file}
       done < "${1}"
     fi

  else

    echo "Argument 2 is missing or is not a valid Splunk path, script will exit"
    exit 1

  fi

else

  echo "Untracked diff file doesn't exist. Skipping cleanup"

fi
