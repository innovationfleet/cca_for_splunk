from ansible.errors import AnsibleFilterError
import re

def extract_deleted_apps(rsync_output):
    """
    Extract a list of app directories within the path etc/deployment-apps
    that are marked for deletion in the rsync dry run output.
    """
    if not isinstance(rsync_output, list):
        raise AnsibleFilterError("The input should be a list of strings representing rsync output lines.")

    deleted_apps = set()
    pattern = re.compile(r'\*deleting\s+([^/]+)/$')

    for line in rsync_output:
        match = pattern.search(line)
        if match:
            deleted_apps.add(match.group(1))

    return list(deleted_apps)

class FilterModule(object):
    ''' Ansible rsync filters '''

    def filters(self):
        return {
            'extract_deleted_apps': extract_deleted_apps
        }
