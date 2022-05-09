# Installed bash profile for CCA for Splunk Automation Frawework
#
# Version: 2022.1.1

# Check if bash scrip is run interactivly or not
# https://unix.stackexchange.com/questions/26676/how-to-check-if-a-shell-is-login-interactive-batch/26827#26827
case $- in

  *i*) ;;
    *) return;;

esac

# Source general aliases and functions specific for this user
if [[ -f ~/.bashrc ]] ; then

  source ~/.bashrc

fi

# Source splunk speific profile, that set's path and functions
if [[ -f ~/.profile ]] ; then

  source ~/.profile

fi

