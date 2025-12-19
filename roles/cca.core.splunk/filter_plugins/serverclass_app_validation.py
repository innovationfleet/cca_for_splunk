# CCA Splunk serverclass app validation
# filter_plugins/serverclass_app_validation.py

from ansible.errors import AnsibleFilterError
import json
import os
import glob

def cca_validate_serverclass_apps(serverclass_data, deployment_apps_staging_dir):
    """
    Validate that all apps referenced in serverclass.conf files exist in the deployment-apps staging directory.

    Args:
        serverclass_data: JSON string containing parsed serverclass data
        deployment_apps_staging_dir: Path to the staging directory containing deployment apps

    Returns:
        dict: Validation results with missing apps and validation status
    """
    try:
        if isinstance(serverclass_data, str):
            serverclass_dict = json.loads(serverclass_data)
        else:
            serverclass_dict = serverclass_data
    except Exception as e:
        raise AnsibleFilterError(f"Error parsing serverclass data: {e}")

    # Get list of available apps in deployment-apps staging directory
    available_apps = set()
    if os.path.exists(deployment_apps_staging_dir):
        for app_dir in os.listdir(deployment_apps_staging_dir):
            app_path = os.path.join(deployment_apps_staging_dir, app_dir)
            if os.path.isdir(app_path):
                available_apps.add(app_dir)

    # Extract app references from serverclass data
    referenced_apps = set()
    missing_apps = set()

    for key, value in serverclass_dict.items():
        # Look for app references in serverclass entries
        if ":app:" in key:
            app_name = key.split(":app:")[1]
            referenced_apps.add(app_name)

            # Check if the app exists in deployment-apps staging directory
            if app_name not in available_apps:
                missing_apps.add(app_name)

    # Also check for app references in the values (some serverclass configs might reference apps in values)
    for key, value in serverclass_dict.items():
        if isinstance(value, str) and value.strip():
            # Look for common app reference patterns in values
            # This is a basic pattern - you might need to adjust based on your serverclass format
            if value.startswith('app:') or value.endswith('.app'):
                app_name = value.replace('app:', '').replace('.app', '').strip()
                if app_name:
                    referenced_apps.add(app_name)
                    if app_name not in available_apps:
                        missing_apps.add(app_name)

    validation_result = {
        'valid': len(missing_apps) == 0,
        'referenced_apps': list(referenced_apps),
        'available_apps': list(available_apps),
        'missing_apps': list(missing_apps),
        'total_referenced': len(referenced_apps),
        'total_available': len(available_apps),
        'total_missing': len(missing_apps)
    }

    return validation_result

def get_serverclass_app_references(serverclass_data):
    """
    Extract all app references from serverclass data for debugging purposes.

    Args:
        serverclass_data: JSON string containing parsed serverclass data

    Returns:
        list: List of all app references found in serverclass data
    """
    try:
        if isinstance(serverclass_data, str):
            serverclass_dict = json.loads(serverclass_data)
        else:
            serverclass_dict = serverclass_data
    except Exception as e:
        raise AnsibleFilterError(f"Error parsing serverclass data: {e}")

    app_references = []

    for key, value in serverclass_dict.items():
        if ":app:" in key:
            app_name = key.split(":app:")[1]
            app_references.append({
                'key': key,
                'app_name': app_name,
                'value': value
            })
        elif isinstance(value, str) and value.strip():
            if value.startswith('app:') or value.endswith('.app'):
                app_name = value.replace('app:', '').replace('.app', '').strip()
                if app_name:
                    app_references.append({
                        'key': key,
                        'app_name': app_name,
                        'value': value
                    })

    return app_references

class FilterModule(object):
    ''' Ansible custom filter plugin for serverclass app validation '''

    def filters(self):
        return {
            'cca_validate_serverclass_apps': cca_validate_serverclass_apps,
            'get_serverclass_app_references': get_serverclass_app_references
        }
