#!/usr/bin/env bash
# This script is a part of CCA and is used to make sure cgroupv1 is being used
# and re-configured after a manual kernel update. Cgroupv2 is not yet supported
# by Splunk, until then this script handles the cgroup changes.
# systemd-based Linux distributions.
# Managed by CCA via Ansible
GRUB_FILE="/etc/default/grub"

# Check if the host has rebooted more than 3 times during the last day with same kernel.
if [ $(last reboot | grep -E "$(date --date='today' '+%a %b %d')" | grep "$(uname -r | grep -oP '^[0-9.-]*[^a-zA-Z]')" | wc -l) -ge 3 ]; then
    message="CCA has detected more than 2 reboots with the same kernel, killing script to prevent boot-loop"
    echo $message && echo $message | systemd-cat -p info -t cca_cgroup_version_daemon
    exit 0
else
    if [ $(grep -c "cgroup /sys/fs/cgroup/systemd cgroup" /etc/mtab) -lt 1 ]; then
        message="Cgroup version 2 is in use"
        echo $message && echo $message | systemd-cat -p info -t cca_cgroup_version_daemon

        if [ -e /etc/os-release ]; then
        source /etc/os-release
            if [[ $ID == "debian" || $ID_LIKE == *"debian"* || $ID == "ubuntu" || $ID_LIKE == *"ubuntu"* ]]; then
                if [ ! -f "$GRUB_FILE" ]; then
                    message="Error: GRUB file ($GRUB_FILE) not found."
                    echo $message && echo $message | systemd-cat -p info -t cca_cgroup_version_daemon
                    exit 0
                fi
                # Backup the original GRUB file
                cp "$GRUB_FILE" "$GRUB_FILE.bak"

                # Use sed to replace or add the line in the GRUB file
                sed -i -E 's/^(GRUB_CMDLINE_LINUX=".*)"\$/ \1 systemd.unified_cgroup_hierarchy=0"/' "$GRUB_FILE"
                # Inform the user about the changes
                message="GRUB configuration updated to disable unified cgroup hierarchy."
                echo $message && echo $message | systemd-cat -p info -t cca_cgroup_version_daemon

                # Update GRUB
                update-grub
                shutdown --reboot 1 "System rebooting in 1 minute to configure cgroup hierarchy - cca_cgroup_version_daemon"
            else
                # Update grub & inform the user.
                grubby --update-kernel=ALL --args="systemd.unified_cgroup_hierarchy=0"
                message="GRUB configuration updated to disable unified cgroup hierarchy."
                echo $message && echo $message | systemd-cat -p info -t cca_cgroup_version_daemon
                shutdown --reboot 1 "System rebooting in 1 minute to configure cgroup hierarchy - cca_cgroup_version_daemon"
            fi
        else
            message="Unable to determine the distribution."
            echo $message && echo $message | systemd-cat -p info -t cca_cgroup_version_daemon
        fi
    else
        message="Cgroup version is correct. Closing down"
        echo $message && echo $message | systemd-cat -p info -t cca_cgroup_version_daemon
    fi
fi
