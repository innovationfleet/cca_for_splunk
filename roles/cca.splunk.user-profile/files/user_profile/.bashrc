# Installed bashrc file for CCA for Splunk Automation Frawework
#
# Version: 2022.1.1

# Source bashrc global definitions
if [[ -f /etc/bashrc ]] ; then

  source /etc/bashrc

fi


# Check if bash scrip is run interactivly or not
# https://unix.stackexchange.com/questions/26676/how-to-check-if-a-shell-is-login-interactive-batch/26827#26827
case $- in

  *i*) ;;
    *) return;;

esac

#Check existing screen sessions
ScreenSessions=$(echo $STY | wc -m)

##########################################################################
# Function that sets the window name for a screen session
# Arguments: None
##########################################################################
function screen_name() {

  echo "Give your screen session a descriptive title."
  read title
  echo -ne "\ek${STY} - ${title}\e\\"

}

if command -v screen &> /dev/null ; then

  if [[ ${ScreenSessions} -gt 5 ]] ; then

    screen_name "Add a shortname for your screen window" || exit 0

  fi

  alias title='source ~/.bashrc'

  if [[ ${ScreenSessions} -lt 2 ]] ; then

    screen -ls | grep -v "No Sockets found in"

  fi

fi

