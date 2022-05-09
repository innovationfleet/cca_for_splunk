#!/usr/bin/env bash
# Installed PS1 path file for CCA for Splunk Automation Frawework
#
# Version: 2022.1.1


CurrentPwd=$(pwd)
CurrentPwd=$(echo $CurrentPwd | sed "s|${HOME}|~|")

OrigIfs="$IFS"
IFS='/'
read -a path_items <<< "${CurrentPwd}"
IFS="$OrigIfs"

PathLen=${#path_items[@]}
LastItem=$(($PathLen-1))
SecondLastItem=$(($PathLen-2))

if [[ ( $CurrentPwd  =~ master* ) && ( ${PathLen} -gt 6 ) ]] ; then

   printf "${path_items[0]}/...master.../${path_items[$SecondLastItem]}/${path_items[$LastItem]}"

elif [[ ( $CurrentPwd =~ dev* ) && ( ${PathLen} -gt 6 ) ]] ; then

   printf "${path_items[0]}/...dev.../${path_items[$SecondLastItem]}/${path_items[$LastItem]}"

elif [[ ${PathLen} -gt 4 ]] ; then

   printf "${path_items[0]}/.../${path_items[$SecondLastItem]}/${path_items[$LastItem]}"

else

  printf $CurrentPwd

fi

