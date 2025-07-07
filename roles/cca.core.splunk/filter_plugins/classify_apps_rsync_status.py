from ansible.errors import AnsibleFilterError
import re
import json

def classify_apps(rsync_output):
    """
    Classify apps based on rsync dry-run output into Removed, Added, and Modified.
    """
    if not isinstance(rsync_output, list):
        raise AnsibleFilterError("The input should be a list of strings representing rsync output lines.")

    apps = {
        'Removed': set(),
        'Added': set(),
        'Modified': set()
    }

    add_pattern = re.compile(r'^cd\+\+\+\+\+\+\+\+\+ ([^/]+)/$')
    delete_pattern = re.compile(r'^\*deleting\s+([^/]+)/$')
    modify_pattern = re.compile(r'^[<>].*\s+([^/]+)/')

    existing_apps = set()

    for line in rsync_output:
        add_match = add_pattern.search(line)
        delete_match = delete_pattern.search(line)
        modify_match = modify_pattern.search(line)

        if add_match:
            app_name = add_match.group(1)
            apps['Added'].add(app_name)
        elif delete_match:
            app_name = delete_match.group(1)
            if app_name in existing_apps:
                apps['Modified'].add(app_name)
            else:
                apps['Removed'].add(app_name)
        elif modify_match:
            app_path = modify_match.group(1)
            top_level_dir = app_path.split('/')[0]
            if top_level_dir not in apps['Added'] and top_level_dir not in apps['Removed']:
                apps['Modified'].add(top_level_dir)
            existing_apps.add(top_level_dir)

    # Convert sets to lists for JSON serialization
    for key in apps:
        apps[key] = list(apps[key])

    return json.dumps(apps, indent=2)

class FilterModule(object):
    ''' Ansible rsync filters '''

    def filters(self):
        return {
            'classify_apps': classify_apps
        }
