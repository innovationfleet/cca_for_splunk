#/usr/bin/env bash

# Generic Splunk apps are stored in the onboarding role following
# a naming convetion with the original name of the extracted tar file
# prefixed with appFile and suffixed with the version of the app.
# E.g. appFile-splunk_app_name-v123
#
# This helper script assists unpacking and renaming the directory
# to make the process a bit easier.

# Validate if the file exists
test -f ${1} && echo "File ${1} is OK" || echo "File ${1} not found"

# Set variables from tgz file
DirName=$(tar tvf ${1} | awk '{ print $6 }' | cut -d "/" -f1 | sort -u )
AppVersion=$(echo ${1} | cut -d"_" -f2 | cut -d"." -f1 )

if [[ $(echo ${DirName} | egrep -o " " | wc -l) -eq 0 ]] ; then

  AppFile=$(echo "appFile-${DirName}_v${AppVersion}")

  if [[ ! -d ${AppFile} ]] ; then

    tar -xvzf ${1} > /dev/null

    mv ${DirName} ${AppFile}

    rm ${1}

  else

    echo "ERROR: It looks like the ${AppFile} directory already exists"
    exit 1

  fi

else

  echo "ERROR: Found multiple base directories, could not determine AppName"
  exit 1

fi
