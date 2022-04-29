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

     while IFS= read -r line; do

       file=$(echo ${line} | cut -d"/" -f2-)
       rm -f ${splunk_path}/${file}

    done < "${1}"

  else

    echo "Splunk path doesn't exist, script will exit"
    exit 1

  fi

else

  echo "Untracked diff file don't exist. Skipping cleanup"

fi
