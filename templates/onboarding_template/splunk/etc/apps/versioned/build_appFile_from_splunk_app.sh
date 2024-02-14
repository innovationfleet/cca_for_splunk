#/usr/bin/env bash

# Generic Splunk apps are stored in the onboarding role following
# a naming convetion with the original name of the extracted tar file
# prefixed with appFile and suffixed with the version of the app.
# E.g. appFile-splunk_app_name-v123
#
# This helper script assists unpacking and renaming the directory
# to make the process a bit easier.

# Validate if the file exists
if [[ -n ${1} ]] ; then

  test -f ${1} && echo "File ${1} is OK" || echo "File ${1} not found"

else

  echo "File not specified"
  exit 1

fi

# Set variables from tgz file
DirName=$(tar tf ${1} | awk -F"/" '{ print $1 }' | sort -u )

if [[ $(echo ${DirName} | egrep -o " " | wc -l) -eq 0 ]] ; then

  if [[ ! -d ${AppFile} ]] ; then

    tar -xzf ${1} > /dev/null

    unset version
    source <(grep version ${DirName}/default/app.conf | grep = | sed -e 's/[[:space:]]//g' | sed 's/\.//g')
    if [[ -n ${version} ]] ; then

      # Use the version from apps app.conf file
      AppVersion=$version
      AppFile=$(echo "appFile-${DirName}_v${AppVersion}")

    else

      # Fallback to use the version from the file name if app.conf didn't have a version
      AppVersion=$(echo ${1} | cut -d"_" -f2 | cut -d"." -f1 )
      AppFile=$(echo "appFile-${DirName}_v${AppVersion}")

    fi

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
