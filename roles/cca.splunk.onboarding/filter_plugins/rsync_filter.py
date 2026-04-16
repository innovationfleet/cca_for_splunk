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


def check_deletion_threshold(deleted_apps, total_app_count,
                            percent_threshold, max_count, min_apps_for_percent):
    """
    Check if the number of deleted apps is within acceptable thresholds.

    Args:
        deleted_apps: List of app names marked for deletion
        total_app_count: Total number of apps on remote destination
        percent_threshold: Max percentage allowed when total > min_apps_for_percent
        max_count: Max count allowed when total <= min_apps_for_percent
        min_apps_for_percent: Threshold to switch between count and percent mode

    Returns:
        dict with is_within_threshold, deleted_count, total_count, threshold_type,
        threshold_value, max_allowed
    """
    deleted_count = len(deleted_apps) if isinstance(deleted_apps, list) else 0
    total_app_count = int(total_app_count)

    if total_app_count > min_apps_for_percent:
        threshold_value = percent_threshold
        max_allowed = int((total_app_count * percent_threshold) / 100)
        is_within = deleted_count < max_allowed or max_allowed == 0
        threshold_type = 'percent'
    else:
        threshold_value = max_count
        max_allowed = max_count
        is_within = deleted_count <= max_count
        threshold_type = 'count'

    return {
        'is_within_threshold': is_within,
        'deleted_count': deleted_count,
        'total_count': total_app_count,
        'threshold_type': threshold_type,
        'threshold_value': threshold_value,
        'max_allowed': max_allowed
    }


class FilterModule(object):
    ''' Ansible rsync filters '''

    def filters(self):
        return {
            'extract_deleted_apps': extract_deleted_apps,
            'check_deletion_threshold': check_deletion_threshold
        }
