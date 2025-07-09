from ansible.errors import AnsibleFilterError
import json

def classify_and_lookup(classified_apps, serverclass_data):
    """
    Perform a lookup for the classified apps in the provided JSON data.
    Returns a list of server classes associated with the apps.
    """
    try:
        if isinstance(serverclass_data, dict):
            serverclass_data_dict = serverclass_data
        else:
            serverclass_data_dict = json.loads(serverclass_data)
    except Exception as e:
        raise AnsibleFilterError(f"Error parsing JSON data: {e}")

    # Create a lookup dictionary for serverclass_data
    app_to_serverclass = {}
    for key, value in serverclass_data_dict.items():
        if ":app:" in key:
            app_name = key.split(":app:")[1]
            serverclass_id = key.split(":")[1]
            if app_name not in app_to_serverclass:
                app_to_serverclass[app_name] = set()
            app_to_serverclass[app_name].add(serverclass_id)

    serverclasses = set()
    restart_needed = False

    for state, apps in classified_apps.items():
        for app in apps:
            if app in app_to_serverclass:
                serverclasses.update(app_to_serverclass[app])
            else:
                restart_needed = True

    if restart_needed:
        serverclasses.add('RESTART_DEPLOYMENT_SERVER')

    return list(serverclasses)

class FilterModule(object):
    ''' Ansible classify and lookup filters '''

    def filters(self):
        return {
            'classify_and_lookup': classify_and_lookup
        }
